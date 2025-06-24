from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from models.user import User

load_dotenv()

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Para validación del lado del servidor

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise Exception("Faltan las variables de entorno SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Security scheme
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    Obtiene el usuario actual a partir del token JWT de Supabase.
    """
    try:
        # Verificar el token con Supabase
        token = credentials.credentials
        response = supabase.auth.get_user(token)
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_data = response.user
        
        # Crear objeto User
        user = User(
            id=user_data.id,
            email=user_data.email,
            nombre_completo=user_data.user_metadata.get('nombre_completo'),
            matricula_profesional=user_data.user_metadata.get('matricula_profesional'),
            colegio_abogados=user_data.user_metadata.get('colegio_abogados'),
            created_at=user_data.created_at
        )
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error validando token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_id(current_user: User = Depends(get_current_user)) -> str:
    """
    Función de conveniencia para obtener solo el ID del usuario actual.
    """
    return current_user.id 