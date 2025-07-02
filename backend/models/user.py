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
    # CAMPOS BÁSICOS EXISTENTES
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
    
    # NUEVOS CAMPOS PARA WORKFLOW ABOGADO (TODOS OPCIONALES)
    tomo: Optional[str] = None
    folio: Optional[str] = None
    condicion_fiscal: Optional[str] = None  # "Responsable Inscripto", "Monotributista", etc.
    cuit: Optional[str] = None
    legajo: Optional[str] = None
    domicilio_legal: Optional[str] = None  # Diferente de domicilio_profesional
    nombre_estudio: Optional[str] = None
    telefono_contacto: Optional[str] = None  # Para demandas (auto-rellena desde telefono)
    email_contacto: Optional[str] = None  # Para demandas (auto-rellena desde email)
    telefono_secundario: Optional[str] = None
    email_secundario: Optional[str] = None 