# =====================================
# INTEGRACIÓN SUPABASE CON FASTAPI
# Sistema Legal AI - Generador de Demandas
# =====================================

import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
from supabase import create_client, Client
from postgrest.exceptions import APIError
from gotrue.errors import AuthError
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import json

# =====================================
# CONFIGURACIÓN
# =====================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") 
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Corregido nombre

# Verificar variables requeridas
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("⚠️ Variables de Supabase no configuradas correctamente")
    print("Verifica SUPABASE_URL y SUPABASE_ANON_KEY en tu .env")

# Clientes Supabase
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print(f"✅ Cliente Supabase normal inicializado")
    
    if SUPABASE_SERVICE_KEY:
        print(f"🔑 SERVICE_ROLE_KEY encontrada: {SUPABASE_SERVICE_KEY[:20]}...{SUPABASE_SERVICE_KEY[-10:]}")
        supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print(f"✅ Cliente Supabase admin inicializado")
    else:
        print("⚠️ SUPABASE_SERVICE_ROLE_KEY no configurado - algunas funciones admin no funcionarán")
        supabase_admin = supabase  # Usar cliente normal como fallback
except Exception as e:
    print(f"❌ Error inicializando Supabase: {e}")
    raise

# Security
security = HTTPBearer()

# =====================================
# MODELOS PYDANTIC
# =====================================

class AbogadoCreate(BaseModel):
    nombre_completo: str
    matricula_profesional: str
    email: str
    telefono: Optional[str] = None
    domicilio_profesional: Optional[str] = None
    especialidad: Optional[List[str]] = []
    colegio_abogados: Optional[str] = None

class AbogadoUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    telefono: Optional[str] = None
    domicilio_profesional: Optional[str] = None
    especialidad: Optional[List[str]] = None
    tribunal_predeterminado: Optional[str] = None

class CarpetaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    color: Optional[str] = "#3B82F6"
    parent_id: Optional[str] = None

class ChatSesionCreate(BaseModel):
    titulo: str
    tipo_demanda: Optional[str] = None
    carpeta_id: Optional[str] = None
    cliente_nombre: Optional[str] = None
    cliente_dni: Optional[str] = None

class DocumentoCreate(BaseModel):
    nombre_archivo: str
    tipo_demanda: str
    categoria: Optional[str] = None
    tags: Optional[List[str]] = []

# =====================================
# AUTENTICACIÓN Y AUTORIZACIÓN
# =====================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene el usuario actual desde el token JWT de Supabase."""
    try:
        token = credentials.credentials
        user = supabase.auth.get_user(token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado"
            )
        
        return user.user
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error de autenticación: {str(e)}"
        )

async def get_current_abogado(user = Depends(get_current_user)):
    """Obtiene el perfil del abogado actual."""
    try:
        response = supabase.table('abogados')\
            .select('*')\
            .eq('user_id', user.id)\
            .single()\
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de abogado no encontrado"
            )
        
        return response.data
    except APIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo perfil: {str(e)}"
        )

# =====================================
# SERVICIOS DE DATOS
# =====================================

class AbogadoService:
    """Servicio para gestionar perfiles de abogados."""
    
    @staticmethod
    async def crear_perfil(user_id: str, datos: AbogadoCreate) -> Dict:
        """Crea un nuevo perfil de abogado."""
        try:
            perfil_data = {
                "user_id": user_id,
                **datos.dict()
            }
            
            response = supabase.table('abogados')\
                .insert(perfil_data)\
                .execute()
            
            return response.data[0]
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creando perfil: {str(e)}"
            )
    
    @staticmethod
    async def actualizar_perfil(abogado_id: str, datos: AbogadoUpdate) -> Dict:
        """Actualiza el perfil de un abogado."""
        try:
            update_data = {k: v for k, v in datos.dict().items() if v is not None}
            
            response = supabase.table('abogados')\
                .update(update_data)\
                .eq('id', abogado_id)\
                .execute()
            
            return response.data[0]
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error actualizando perfil: {str(e)}"
            )

class CarpetaService:
    """Servicio para gestionar carpetas de organización."""
    
    @staticmethod
    async def obtener_carpetas(abogado_id: str) -> List[Dict]:
        """Obtiene todas las carpetas de un abogado."""
        try:
            response = supabase.table('carpetas')\
                .select('*')\
                .eq('abogado_id', abogado_id)\
                .order('orden')\
                .execute()
            
            return response.data
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error obteniendo carpetas: {str(e)}"
            )
    
    @staticmethod
    async def crear_carpeta(abogado_id: str, datos: CarpetaCreate) -> Dict:
        """Crea una nueva carpeta."""
        try:
            carpeta_data = {
                "abogado_id": abogado_id,
                **datos.dict()
            }
            
            response = supabase.table('carpetas')\
                .insert(carpeta_data)\
                .execute()
            
            return response.data[0]
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creando carpeta: {str(e)}"
            )

class ChatService:
    """Servicio para gestionar sesiones de chat."""
    
    @staticmethod
    async def crear_sesion(abogado_id: str, session_id: str, datos: ChatSesionCreate) -> Dict:
        """Crea una nueva sesión de chat."""
        try:
            sesion_data = {
                "session_id": session_id,
                "abogado_id": abogado_id,
                **datos.dict()
            }
            
            # Verificar qué cliente estamos usando
            print(f"🔍 Usando cliente: {'admin' if 'service_role' in str(supabase_admin.supabase_key) else 'normal'}")
            print(f"🔍 Datos de sesión: {sesion_data}")
            
            # Usar cliente admin para evitar RLS
            response = supabase_admin.table('chat_sesiones')\
                .insert(sesion_data)\
                .execute()
            
            print(f"✅ Sesión creada exitosamente")
            return response.data[0]
        except APIError as e:
            print(f"❌ Error API en crear_sesion: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creando sesión: {str(e)}"
            )
    
    @staticmethod
    async def obtener_sesiones(abogado_id: str, carpeta_id: Optional[str] = None) -> List[Dict]:
        """Obtiene las sesiones de un abogado, opcionalmente filtradas por carpeta."""
        try:
            query = supabase.table('chat_sesiones')\
                .select('*, carpetas(*)')\
                .eq('abogado_id', abogado_id)\
                .order('updated_at', desc=True)
            
            if carpeta_id:
                query = query.eq('carpeta_id', carpeta_id)
            
            response = query.execute()
            return response.data
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error obteniendo sesiones: {str(e)}"
            )
    
    @staticmethod
    async def guardar_mensaje(sesion_id: str, tipo: str, mensaje: str, metadata: Dict = None) -> Dict:
        """Guarda un mensaje en una sesión."""
        try:
            mensaje_data = {
                "sesion_id": sesion_id,
                "tipo": tipo,
                "mensaje": mensaje,
                "metadata": metadata or {}
            }
            
            # Usar cliente admin para evitar RLS
            response = supabase_admin.table('chat_mensajes')\
                .insert(mensaje_data)\
                .execute()
            
            return response.data[0]
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error guardando mensaje: {str(e)}"
            )
    
    @staticmethod
    async def obtener_mensajes(sesion_id: str) -> List[Dict]:
        """Obtiene todos los mensajes de una sesión."""
        try:
            print(f"🔍 ChatService.obtener_mensajes - sesion_id: {sesion_id}")
            
            # Usar cliente admin para evitar problemas de RLS
            response = supabase_admin.table('chat_mensajes')\
                .select('*')\
                .eq('sesion_id', sesion_id)\
                .order('created_at', desc=False)\
                .execute()
            
            mensajes = response.data or []
            print(f"✅ ChatService.obtener_mensajes - encontrados: {len(mensajes)} mensajes")
            
            return mensajes
        except APIError as e:
            print(f"❌ ChatService.obtener_mensajes - Error API: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error obteniendo mensajes: {str(e)}"
            )

class DemandaService:
    """Servicio para gestionar demandas generadas."""
    
    @staticmethod
    async def guardar_demanda(sesion_id: str, abogado_id: str, texto_demanda: str, 
                            archivo_url: str = None, metadata: Dict = None) -> Dict:
        """Guarda una demanda generada."""
        try:
            demanda_data = {
                "sesion_id": sesion_id,
                "abogado_id": abogado_id,
                "texto_demanda": texto_demanda,
                "archivo_docx_url": archivo_url,
                **(metadata or {})
            }
            
            response = supabase.table('demandas_generadas')\
                .insert(demanda_data)\
                .execute()
            
            return response.data[0]
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error guardando demanda: {str(e)}"
            )

class DocumentoService:
    """Servicio para gestionar documentos de entrenamiento."""
    
    @staticmethod
    async def subir_documento(abogado_id: str, archivo_url: str, datos: DocumentoCreate) -> Dict:
        """Registra un documento subido para entrenamiento."""
        try:
            doc_data = {
                "abogado_id": abogado_id,
                "archivo_url": archivo_url,
                **datos.dict()
            }
            
            response = supabase.table('documentos_entrenamiento')\
                .insert(doc_data)\
                .execute()
            
            return response.data[0]
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error registrando documento: {str(e)}"
            )
    
    @staticmethod
    async def obtener_documentos(abogado_id: str, tipo_demanda: str = None) -> List[Dict]:
        """Obtiene los documentos de un abogado."""
        try:
            query = supabase.table('documentos_entrenamiento')\
                .select('*')\
                .eq('abogado_id', abogado_id)\
                .order('created_at', desc=True)
            
            if tipo_demanda:
                query = query.eq('tipo_demanda', tipo_demanda)
            
            response = query.execute()
            return response.data
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error obteniendo documentos: {str(e)}"
            )
    
    @staticmethod
    async def actualizar_estado_procesamiento(doc_id: str, estado: str, 
                                            error: str = None, qdrant_collection: str = None) -> Dict:
        """Actualiza el estado de procesamiento de un documento."""
        try:
            update_data = {
                "estado_procesamiento": estado,
                "processed_at": datetime.now().isoformat()
            }
            
            if error:
                update_data["error_procesamiento"] = error
            
            if qdrant_collection:
                update_data["qdrant_collection"] = qdrant_collection
                update_data["vectorizado"] = True
            
            response = supabase.table('documentos_entrenamiento')\
                .update(update_data)\
                .eq('id', doc_id)\
                .execute()
            
            return response.data[0]
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error actualizando documento: {str(e)}"
            )

# =====================================
# UTILIDADES
# =====================================

class StorageService:
    """Servicio para gestionar archivos en Supabase Storage."""
    
    @staticmethod
    async def subir_archivo(bucket: str, path: str, archivo_bytes: bytes, 
                          content_type: str = None) -> str:
        """Sube un archivo a Supabase Storage."""
        try:
            response = supabase.storage.from_(bucket).upload(
                path, archivo_bytes, 
                file_options={"content-type": content_type} if content_type else None
            )
            
            if response.get('error'):
                raise Exception(response['error'])
            
            # Obtener URL pública - manejar correctamente el retorno
            try:
                url_response = supabase.storage.from_(bucket).get_public_url(path)
                
                # Verificar si es una cadena (URL) o un diccionario con data
                if isinstance(url_response, str):
                    return url_response
                elif isinstance(url_response, dict) and url_response.get('publicUrl'):
                    return url_response['publicUrl']
                elif hasattr(url_response, 'publicUrl'):
                    return url_response.publicUrl
                else:
                    # Fallback: construir URL manualmente
                    return f"{supabase.supabase_url}/storage/v1/object/public/{bucket}/{path}"
            except Exception as url_error:
                print(f"⚠️ Error obteniendo URL pública, usando fallback: {url_error}")
                # Fallback: construir URL manualmente
                return f"{supabase.supabase_url}/storage/v1/object/public/{bucket}/{path}"
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error subiendo archivo: {str(e)}"
            )
    
    @staticmethod
    async def eliminar_archivo(bucket: str, path: str) -> bool:
        """Elimina un archivo de Supabase Storage."""
        try:
            response = supabase.storage.from_(bucket).remove([path])
            return not response.get('error')
        except Exception as e:
            print(f"Error eliminando archivo: {e}")
            return False

# =====================================
# INSTANCIAS DE SERVICIOS
# =====================================

abogado_service = AbogadoService()
carpeta_service = CarpetaService()
chat_service = ChatService()
demanda_service = DemandaService()
documento_service = DocumentoService()
storage_service = StorageService()

# =====================================
# CONFIGURACIÓN DE BUCKETS
# =====================================

# Buckets necesarios en Supabase Storage:
# - documentos-entrenamiento: Para PDFs/DOCs subidos
# - demandas-generadas: Para archivos .docx generados
# - avatares: Para fotos de perfil (opcional)

BUCKETS_REQUIRED = [
    "documentos-entrenamiento",
    "demandas-generadas", 
    "avatares"
]

async def initialize_storage():
    """Inicializa los buckets necesarios en Supabase Storage."""
    for bucket in BUCKETS_REQUIRED:
        try:
            # Intentar crear bucket (falla silenciosamente si ya existe)
            supabase_admin.storage.create_bucket(bucket, {"public": False})
            print(f"✅ Bucket '{bucket}' inicializado")
        except Exception as e:
            print(f"⚠️ Bucket '{bucket}' ya existe o error: {e}") 