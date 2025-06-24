"""
Token Manager for Google Drive OAuth2 tokens
Handles encryption, decryption, and token refresh
"""

import os
import json
import base64
from typing import Dict, Optional, Tuple, TYPE_CHECKING
from datetime import datetime, timedelta, timezone

# Importaciones para type hints (solo durante type checking)
if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow

# Importaciones condicionales para compatibilidad con Railway
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None

try:
    import google.auth.transport.requests
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False
    # Definir clases dummy para evitar errores de nombre
    Credentials = None
    Flow = None

try:
    from ..config import settings
except ImportError:
    from ..config import settings


class TokenManager:
    """Manages encryption/decryption and refresh of Google OAuth2 tokens"""
    
    def __init__(self):
        self.available = CRYPTOGRAPHY_AVAILABLE and GOOGLE_AUTH_AVAILABLE
        
        if not self.available:
            print("⚠️ TokenManager no disponible - faltan dependencias crypto/google-auth")
            self.encryption_key = None
            self.fernet = None
            return
            
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get encryption key from environment or derive from a password"""
        if not CRYPTOGRAPHY_AVAILABLE:
            raise Exception("Cryptography no disponible para generar claves de encriptación")
            
        if settings.TOKEN_ENCRYPTION_KEY:
            # If we have a key, use it directly
            try:
                return base64.urlsafe_b64decode(settings.TOKEN_ENCRYPTION_KEY)
            except:
                # If it's not base64, derive a key from it
                password = settings.TOKEN_ENCRYPTION_KEY.encode()
                salt = b'google_drive_salt_2024'  # In production, use a random salt per user
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                return base64.urlsafe_b64encode(kdf.derive(password))
        else:
            # Generate a new key (for development only)
            key = Fernet.generate_key()
            print(f"⚠️ Generated new encryption key: {key.decode()}")
            print("⚠️ Add this to your .env as TOKEN_ENCRYPTION_KEY")
            return key
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt a token string"""
        if not self.available:
            raise Exception("TokenManager no disponible - faltan dependencias crypto/google-auth")
            
        try:
            if not token:
                return ""
            encrypted_bytes = self.fernet.encrypt(token.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            raise Exception(f"Error encrypting token: {e}")
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token string"""
        if not self.available:
            raise Exception("TokenManager no disponible - faltan dependencias crypto/google-auth")
            
        try:
            if not encrypted_token:
                return ""
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_token.encode())
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            raise Exception(f"Error decrypting token: {e}")
    
    def encrypt_token_data(self, token_data: Dict) -> Dict[str, str]:
        """Encrypt token data dictionary"""
        if not self.available:
            raise Exception("TokenManager no disponible - faltan dependencias crypto/google-auth")
            
        return {
            'access_token_encrypted': self.encrypt_token(token_data.get('access_token', '')),
            'refresh_token_encrypted': self.encrypt_token(token_data.get('refresh_token', ''))
        }
    
    def decrypt_token_data(self, encrypted_data: Dict) -> Dict[str, str]:
        """Decrypt token data dictionary"""
        if not self.available:
            raise Exception("TokenManager no disponible - faltan dependencias crypto/google-auth")
            
        return {
            'access_token': self.decrypt_token(encrypted_data.get('access_token_encrypted', '')),
            'refresh_token': self.decrypt_token(encrypted_data.get('refresh_token_encrypted', ''))
        }
    
    def create_credentials_from_token_data(self, token_data: Dict, expires_at: datetime = None) -> "Credentials":
        """Create Google Credentials object from decrypted token data"""
        if not self.available:
            raise Exception("TokenManager no disponible - Google Drive requiere dependencias adicionales")
            
        return Credentials(
            token=token_data['access_token'],
            refresh_token=token_data['refresh_token'],
            token_uri='https://oauth2.googleapis.com/token',
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=settings.GOOGLE_SCOPES,
            expiry=expires_at
        )
    
    def refresh_credentials(self, credentials: "Credentials") -> Tuple["Credentials", bool]:
        """
        Refresh Google credentials if needed
        Returns: (credentials, was_refreshed)
        """
        if not self.available:
            raise Exception("TokenManager no disponible - Google Drive requiere dependencias adicionales")
            
        try:
            # Check if token needs refresh (expires in next 5 minutes)
            # Nota: Google Auth espera naive datetimes, así que usamos datetime.utcnow()
            now_utc = datetime.utcnow()
            
            needs_refresh = (
                credentials.expiry is None or 
                credentials.expiry <= now_utc + timedelta(minutes=5)
            )
            
            if needs_refresh and credentials.refresh_token:
                print("🔄 Refreshing Google Drive access token...")
                request = google.auth.transport.requests.Request()
                credentials.refresh(request)
                print("✅ Token refreshed successfully")
                return credentials, True
            
            return credentials, False
            
        except Exception as e:
            print(f"❌ Error refreshing token: {e}")
            raise Exception(f"Failed to refresh Google Drive token: {e}")
    
    def validate_credentials(self, credentials: "Credentials") -> bool:
        """Validate that credentials are working"""
        if not self.available:
            return False
            
        try:
            # Try to make a simple API call
            service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
            # Get user info to validate
            about = service.about().get(fields='user').execute()
            return True
        except Exception as e:
            print(f"❌ Credentials validation failed: {e}")
            return False
    
    def get_oauth_flow(self, state: str = None) -> "Flow":
        """Create OAuth2 flow for Google Drive"""
        if not self.available:
            raise Exception("TokenManager no disponible - Google Drive requiere dependencias adicionales")
            
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=settings.GOOGLE_SCOPES
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
        return flow
    
    def get_authorization_url(self, user_id: str) -> str:
        """Generate authorization URL for OAuth2 flow"""
        if not self.available:
            raise Exception("TokenManager no disponible - Google Drive requiere dependencias adicionales")
            
        flow = self.get_oauth_flow()
        
        # Include user_id in state for security
        state = f"user:{user_id}"
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'  # Force consent to get refresh token
        )
        
        return auth_url
    
    def exchange_code_for_tokens(self, authorization_code: str, user_id: str) -> Dict:
        """Exchange authorization code for tokens"""
        if not self.available:
            raise Exception("TokenManager no disponible - Google Drive requiere dependencias adicionales")
            
        try:
            flow = self.get_oauth_flow()
            
            # Exchange code for tokens
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            
            # Get user info
            service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
            about = service.about().get(fields='user').execute()
            user_info = about.get('user', {})
            
            return {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'expires_at': credentials.expiry,
                'google_email': user_info.get('emailAddress', ''),
                'google_user_id': user_info.get('permissionId', ''),
                'scope': ' '.join(credentials.scopes or [])
            }
            
        except Exception as e:
            raise Exception(f"Failed to exchange authorization code: {e}")


# Global instance (condicional para compatibilidad con Railway)
if CRYPTOGRAPHY_AVAILABLE and GOOGLE_AUTH_AVAILABLE:
    token_manager = TokenManager()
else:
    # Crear un manager mock que arroja errores informativos
    class MockTokenManager:
        def __init__(self):
            self.available = False
            
        def __getattr__(self, name):
            def method_not_available(*args, **kwargs):
                raise Exception("Google Drive no disponible - instale cryptography y google-auth-oauthlib")
            return method_not_available
    
    token_manager = MockTokenManager() 