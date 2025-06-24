import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    
    # Qdrant Configuration
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION_PREFIX: str = "user_"
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # File Upload Configuration
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: set = {"pdf", "doc", "docx", "txt"}
    
    # Processing Configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # Vector Configuration
    VECTOR_DIMENSION: int = int(os.getenv("VECTOR_DIMENSION", "1536"))  # text-embedding-3-small
    
    # Google Drive Configuration
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")
    GOOGLE_SCOPES: list = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.file"
    ]
    
    # Encryption for storing Google tokens
    TOKEN_ENCRYPTION_KEY: str = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    
    # Validation
    def validate(self) -> bool:
        """Validate that all required settings are present"""
        required_settings = [
            self.SUPABASE_URL,
            self.SUPABASE_SERVICE_KEY,
            self.OPENAI_API_KEY,
        ]
        
        return all(setting for setting in required_settings)
    
    def validate_google_drive(self) -> bool:
        """Validate Google Drive specific settings"""
        return all([
            self.GOOGLE_CLIENT_ID,
            self.GOOGLE_CLIENT_SECRET,
            self.TOKEN_ENCRYPTION_KEY
        ])
    
    def get_qdrant_collection_name(self, user_id: str) -> str:
        """Generate Qdrant collection name for user"""
        return f"{self.QDRANT_COLLECTION_PREFIX}{user_id}_documents"

# Global settings instance
settings = Settings()

# Validate settings on import
if not settings.validate():
    raise ValueError(
        "Missing required environment variables. "
        "Please check SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and OPENAI_API_KEY"
    ) 