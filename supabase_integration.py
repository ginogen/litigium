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
import time
from functools import wraps

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

# Configuración de cliente HTTP más robusta para evitar problemas SSL
def create_robust_supabase_client(url: str, key: str) -> Client:
    """Crea un cliente de Supabase con configuración robusta para SSL."""
    try:
        # Configurar httpx con timeouts más largos y manejo de SSL mejorado
        httpx_client = httpx.Client(
            timeout=httpx.Timeout(
                connect=10.0,  # 10 segundos para conectar
                read=30.0,     # 30 segundos para leer
                write=30.0,    # 30 segundos para escribir
                pool=30.0      # 30 segundos para pool
            ),
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5
            ),
            verify=True,  # Mantener verificación SSL
            follow_redirects=True
        )
        
        # Crear cliente Supabase con cliente HTTP personalizado
        client = create_client(
            url, 
            key,
            options={
                'schema': 'public',
                'auto_refresh_token': True,
                'persist_session': True,
                'detect_session_in_url': False,
                'headers': {
                    'User-Agent': 'aibot-legal/1.0'
                }
            }
        )
        
        # Configurar el cliente HTTP en el cliente Supabase si es posible
        if hasattr(client, '_client'):
            client._client = httpx_client
        elif hasattr(client, 'postgrest') and hasattr(client.postgrest, 'session'):
            client.postgrest.session = httpx_client
            
        return client
        
    except Exception as e:
        print(f"❌ Error creando cliente Supabase robusto: {e}")
        # Fallback al método original
        return create_client(url, key)

# Clientes Supabase con configuración robusta
try:
    supabase: Client = create_robust_supabase_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print(f"✅ Cliente Supabase normal inicializado con configuración robusta")
    
    if SUPABASE_SERVICE_KEY:
        print(f"🔑 SERVICE_ROLE_KEY encontrada: {SUPABASE_SERVICE_KEY[:20]}...{SUPABASE_SERVICE_KEY[-10:]}")
        supabase_admin: Client = create_robust_supabase_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print(f"✅ Cliente Supabase admin inicializado con configuración robusta")
    else:
        print("⚠️ SUPABASE_SERVICE_ROLE_KEY no configurado - algunas funciones admin no funcionarán")
        supabase_admin = supabase  # Usar cliente normal como fallback
except Exception as e:
    print(f"❌ Error inicializando Supabase: {e}")
    print("🔧 Intentando con configuración básica...")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_SERVICE_KEY else supabase
        print(f"✅ Clientes Supabase inicializados con configuración básica")
    except Exception as e2:
        print(f"❌ Error crítico inicializando Supabase: {e2}")
        raise

# Security
security = HTTPBearer()

# =====================================
# UTILIDADES PARA MANEJO DE ERRORES SSL
# =====================================

def retry_on_ssl_error(max_retries: int = 3, delay: float = 1.0):
    """Decorador para reintentar operaciones que fallan por SSL."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_str = str(e).lower()
                    
                    # Verificar si es un error SSL/conexión
                    if any(ssl_error in error_str for ssl_error in [
                        'ssl', 'connection', 'timeout', 'httpcore.connecterror',
                        'record layer failure', 'httpx.connecterror'
                    ]):
                        print(f"⚠️ Error SSL detectado (intento {attempt + 1}/{max_retries}): {str(e)[:100]}")
                        if attempt < max_retries - 1:
                            time.sleep(delay * (attempt + 1))  # Backoff exponencial
                            continue
                    
                    # Si no es un error SSL o es el último intento, propagar el error
                    raise e
            
            # Si llegamos aquí, todos los intentos fallaron
            print(f"❌ Todos los reintentos fallaron. Último error: {last_exception}")
            raise last_exception
            
        return wrapper
    return decorator

async def safe_supabase_query(query_func, *args, **kwargs):
    """Ejecuta una consulta de Supabase con manejo de errores SSL."""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            return query_func(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            
            if any(ssl_error in error_str for ssl_error in [
                'ssl', 'connection', 'timeout', 'httpcore.connecterror',
                'record layer failure', 'httpx.connecterror'
            ]):
                print(f"⚠️ Error SSL en consulta (intento {attempt + 1}/{max_retries}): {str(e)[:100]}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))  # Esperar antes del siguiente intento
                    continue
            
            # Si no es error SSL o es el último intento, propagar
            raise e
    
    raise Exception("Todos los reintentos de consulta fallaron")

# =====================================
# MODELOS PYDANTIC
# =====================================

class AbogadoCreate(BaseModel):
    # CAMPOS BÁSICOS (EXISTENTES - OBLIGATORIOS)
    nombre_completo: str
    matricula_profesional: str
    email: str
    
    # CAMPOS EXISTENTES (OPCIONALES - COMPATIBILIDAD)
    telefono: Optional[str] = None
    domicilio_profesional: Optional[str] = None
    especialidad: Optional[List[str]] = []
    colegio_abogados: Optional[str] = None
    
    # NUEVOS CAMPOS PARA WORKFLOW DEL ABOGADO (TODOS OPCIONALES)
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

class AbogadoUpdate(BaseModel):
    # CAMPOS EXISTENTES (MANTENER COMPATIBILIDAD)
    nombre_completo: Optional[str] = None
    telefono: Optional[str] = None
    domicilio_profesional: Optional[str] = None
    especialidad: Optional[List[str]] = None
    tribunal_predeterminado: Optional[str] = None
    
    # NUEVOS CAMPOS EXTENSIÓN
    tomo: Optional[str] = None
    folio: Optional[str] = None
    condicion_fiscal: Optional[str] = None
    cuit: Optional[str] = None
    legajo: Optional[str] = None
    domicilio_legal: Optional[str] = None
    nombre_estudio: Optional[str] = None
    telefono_contacto: Optional[str] = None
    email_contacto: Optional[str] = None
    telefono_secundario: Optional[str] = None
    email_secundario: Optional[str] = None

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
    estado: Optional[str] = "inicio"  # Estado inicial por defecto

class DocumentoCreate(BaseModel):
    nombre_archivo: str
    tipo_demanda: str
    categoria: Optional[str] = None
    tags: Optional[List[str]] = []

class DocumentoChatCreate(BaseModel):
    """Modelo para crear documentos adjuntos en chat."""
    session_id: str
    nombre_archivo: str
    tipo_documento: str  # 'telegrama', 'liquidacion', 'recibo_sueldo', 'carta_documento', 'imagen_general'
    mime_type: str
    tamaño_bytes: int

class DocumentoChatResponse(BaseModel):
    """Modelo para respuesta de documentos del chat."""
    id: str
    session_id: str
    abogado_id: str
    archivo_url: str
    nombre_archivo: str
    tipo_documento: str
    mime_type: str
    tamaño_bytes: int
    texto_extraido: Optional[str] = None
    datos_estructurados: Optional[Dict] = None
    metadatos_ocr: Optional[Dict] = None
    procesado: bool
    fecha_procesamiento: Optional[str] = None
    error_procesamiento: Optional[str] = None
    created_at: str
    updated_at: str

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

class DocumentoChatService:
    """Servicio para gestionar documentos adjuntos en chat."""
    
    @staticmethod
    async def crear_documento(abogado_id: str, archivo_url: str, datos: DocumentoChatCreate) -> Dict:
        """Registra un documento adjunto en chat."""
        try:
            doc_data = {
                "abogado_id": abogado_id,
                "archivo_url": archivo_url,
                **datos.dict()
            }
            
            response = supabase_admin.table('documentos_chat')\
                .insert(doc_data)\
                .execute()
            
            return response.data[0]
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error registrando documento chat: {str(e)}"
            )
    
    @staticmethod
    async def actualizar_procesamiento(
        documento_id: str, 
        texto_extraido: str, 
        datos_estructurados: Dict,
        metadatos_ocr: Dict,
        error: str = None
    ) -> Dict:
        """Actualiza los datos de procesamiento de un documento."""
        try:
            update_data = {
                "procesado": error is None,
                "fecha_procesamiento": datetime.now().isoformat(),
                "texto_extraido": texto_extraido,
                "datos_estructurados": datos_estructurados,
                "metadatos_ocr": metadatos_ocr,
                "error_procesamiento": error
            }
            
            response = supabase_admin.table('documentos_chat')\
                .update(update_data)\
                .eq('id', documento_id)\
                .execute()
            
            return response.data[0]
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error actualizando procesamiento: {str(e)}"
            )
    
    @staticmethod
    async def obtener_documentos_sesion(session_id: str, abogado_id: str) -> List[Dict]:
        """Obtiene todos los documentos de una sesión."""
        try:
            response = supabase_admin.table('documentos_chat')\
                .select('*')\
                .eq('session_id', session_id)\
                .eq('abogado_id', abogado_id)\
                .order('created_at', desc=False)\
                .execute()
            
            return response.data
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error obteniendo documentos de sesión: {str(e)}"
            )
    
    @staticmethod
    async def obtener_resumen_sesion(session_id: str) -> Dict:
        """Obtiene resumen consolidado de documentos de una sesión usando función SQL."""
        try:
            response = supabase_admin.rpc('get_documentos_chat_resumen', {
                'p_session_id': session_id
            }).execute()
            
            return response.data[0] if response.data else {}
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error obteniendo resumen: {str(e)}"
            )
    
    @staticmethod
    async def obtener_consolidado_sesion(session_id: str) -> Dict:
        """Obtiene información consolidada de todos los documentos usando función SQL."""
        try:
            response = supabase_admin.rpc('get_documentos_chat_consolidado', {
                'p_session_id': session_id
            }).execute()
            
            return response.data[0] if response.data else {}
        except APIError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error obteniendo consolidado: {str(e)}"
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
            print(f"☁️ [STORAGE] Subiendo archivo a bucket '{bucket}', path: {path}")
            
            # Usar supabase_admin para tener permisos completos
            response = supabase_admin.storage.from_(bucket).upload(
                path, archivo_bytes, 
                file_options={"content-type": content_type} if content_type else None
            )
            
            print(f"✅ [STORAGE] Upload response: {response}")
            
            # Manejar diferentes tipos de respuesta
            if hasattr(response, 'error') and response.error:
                print(f"❌ [STORAGE] Error en upload: {response.error}")
                raise Exception(response.error)
            elif hasattr(response, 'get') and response.get('error'):
                print(f"❌ [STORAGE] Error en upload: {response['error']}")
                raise Exception(response['error'])
            elif isinstance(response, dict) and response.get('error'):
                print(f"❌ [STORAGE] Error en upload: {response['error']}")
                raise Exception(response['error'])
            
            # Obtener URL pública - manejar correctamente el retorno
            try:
                url_response = supabase_admin.storage.from_(bucket).get_public_url(path)
                print(f"🔗 [STORAGE] URL response: {url_response}")
                
                # Verificar si es una cadena (URL) o un diccionario con data
                if isinstance(url_response, str):
                    public_url = url_response
                elif isinstance(url_response, dict) and url_response.get('publicUrl'):
                    public_url = url_response['publicUrl']
                elif hasattr(url_response, 'publicUrl'):
                    public_url = url_response.publicUrl
                else:
                    # Fallback: construir URL manualmente
                    public_url = f"{supabase_admin.supabase_url}/storage/v1/object/public/{bucket}/{path}"
                
                print(f"✅ [STORAGE] URL pública generada: {public_url}")
                return public_url
                
            except Exception as url_error:
                print(f"⚠️ [STORAGE] Error obteniendo URL pública, usando fallback: {url_error}")
                # Fallback: construir URL manualmente
                public_url = f"{supabase_admin.supabase_url}/storage/v1/object/public/{bucket}/{path}"
                print(f"🔗 [STORAGE] URL fallback: {public_url}")
                return public_url
            
        except Exception as e:
            print(f"❌ [STORAGE] Error subiendo archivo: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error subiendo archivo: {str(e)}"
            )
    
    @staticmethod
    async def eliminar_archivo(bucket: str, path: str) -> bool:
        """Elimina un archivo de Supabase Storage."""
        try:
            response = supabase_admin.storage.from_(bucket).remove([path])
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
documento_chat_service = DocumentoChatService()
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
    "documentos-chat",  # NUEVO: Para imágenes subidas en chat
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