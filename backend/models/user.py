from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: str
    email: str
    nombre_completo: Optional[str] = None
    matricula_profesional: Optional[str] = None
    colegio_abogados: Optional[str] = None
    created_at: datetime
    
class UserProfile(BaseModel):
    id: str
    user_id: str
    nombre_completo: str
    matricula_profesional: str
    colegio_abogados: Optional[str] = None
    telefono: Optional[str] = None
    domicilio_profesional: Optional[str] = None
    ciudad: Optional[str] = None
    provincia: Optional[str] = None
    codigo_postal: Optional[str] = None
    especialidad: list[str] = []
    anos_experiencia: int = 0
    universidad: Optional[str] = None
    ano_graduacion: Optional[int] = None
    tribunal_predeterminado: Optional[str] = None
    formato_demanda_preferido: str = 'formal'
    created_at: datetime
    updated_at: datetime
    activo: bool = True 