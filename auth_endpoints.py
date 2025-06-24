# =====================================
# ENDPOINTS DE AUTENTICACIÓN Y USUARIOS
# Sistema Legal AI - Generador de Demandas
# =====================================

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
import uuid
from datetime import datetime

from supabase_integration import (
    get_current_user, get_current_abogado,
    abogado_service, carpeta_service, chat_service, 
    demanda_service, documento_service, storage_service,
    AbogadoCreate, AbogadoUpdate, CarpetaCreate, 
    ChatSesionCreate, DocumentoCreate, supabase
)

router = APIRouter(prefix="/api/v1", tags=["auth"])

# =====================================
# ENDPOINTS DE AUTENTICACIÓN
# =====================================

@router.post("/auth/register")
async def register_user(email: str, password: str, datos_abogado: AbogadoCreate):
    """Registra un nuevo usuario y crea su perfil de abogado."""
    try:
        print(f"🔐 [DEBUG] Registrando usuario: {email}")
        
        # Registrar usuario en Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error creando usuario"
            )
        
        user_id = auth_response.user.id
        print(f"✅ [DEBUG] Usuario creado con ID: {user_id}")
        
        # Crear perfil de abogado
        perfil = await abogado_service.crear_perfil(user_id, datos_abogado)
        print(f"✅ [DEBUG] Perfil de abogado creado: {perfil['id']}")
        
        # Crear carpeta "General" por defecto
        carpeta_default = await carpeta_service.crear_carpeta(
            perfil['id'], 
            CarpetaCreate(nombre="General", descripcion="Carpeta por defecto")
        )
        print(f"✅ [DEBUG] Carpeta por defecto creada")
        
        return {
            "success": True,
            "mensaje": "Usuario registrado exitosamente",
            "user": auth_response.user,
            "perfil": perfil,
            "carpeta_default": carpeta_default
        }
        
    except Exception as e:
        print(f"❌ [DEBUG] Error en registro: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en registro: {str(e)}"
        )

@router.post("/auth/login")
async def login_user(email: str, password: str):
    """Inicia sesión de usuario."""
    try:
        print(f"🔐 [DEBUG] Login usuario: {email}")
        
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        # Obtener perfil del abogado
        perfil_response = supabase.table('abogados')\
            .select('*')\
            .eq('user_id', auth_response.user.id)\
            .single()\
            .execute()
        
        print(f"✅ [DEBUG] Login exitoso")
        
        return {
            "success": True,
            "mensaje": "Login exitoso",
            "user": auth_response.user,
            "session": auth_response.session,
            "perfil": perfil_response.data if perfil_response.data else None
        }
        
    except Exception as e:
        print(f"❌ [DEBUG] Error en login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

@router.post("/auth/logout")
async def logout_user(user = Depends(get_current_user)):
    """Cierra sesión del usuario."""
    try:
        supabase.auth.sign_out()
        return {"success": True, "mensaje": "Logout exitoso"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en logout: {str(e)}"
        )

@router.get("/auth/me")
async def get_current_user_info(abogado = Depends(get_current_abogado)):
    """Obtiene información del usuario actual."""
    return {
        "success": True,
        "abogado": abogado
    }

# =====================================
# ENDPOINTS DE PERFIL
# =====================================

@router.get("/perfil")
async def obtener_perfil(abogado = Depends(get_current_abogado)):
    """Obtiene el perfil completo del abogado."""
    try:
        # Obtener estadísticas adicionales
        stats_response = supabase.rpc('get_abogado_stats', {'abogado_id': abogado['id']}).execute()
        
        return {
            "success": True,
            "perfil": abogado,
            "estadisticas": stats_response.data if stats_response.data else {}
        }
    except Exception as e:
        print(f"❌ [DEBUG] Error obteniendo perfil: {str(e)}")
        return {
            "success": True,
            "perfil": abogado,
            "estadisticas": {}
        }

@router.put("/perfil")
async def actualizar_perfil(
    datos: AbogadoUpdate, 
    abogado = Depends(get_current_abogado)
):
    """Actualiza el perfil del abogado."""
    try:
        print(f"📝 [DEBUG] Actualizando perfil: {abogado['id']}")
        
        perfil_actualizado = await abogado_service.actualizar_perfil(
            abogado['id'], datos
        )
        
        return {
            "success": True,
            "mensaje": "Perfil actualizado exitosamente",
            "perfil": perfil_actualizado
        }
    except Exception as e:
        print(f"❌ [DEBUG] Error actualizando perfil: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando perfil: {str(e)}"
        )

# =====================================
# ENDPOINTS DE CARPETAS
# =====================================

@router.get("/carpetas")
async def obtener_carpetas(abogado = Depends(get_current_abogado)):
    """Obtiene todas las carpetas del abogado."""
    try:
        carpetas = await carpeta_service.obtener_carpetas(abogado['id'])
        
        # Obtener conteo de sesiones por carpeta
        for carpeta in carpetas:
            count_response = supabase.table('chat_sesiones')\
                .select('id', count='exact')\
                .eq('carpeta_id', carpeta['id'])\
                .execute()
            carpeta['total_sesiones'] = count_response.count or 0
        
        return {
            "success": True,
            "carpetas": carpetas
        }
    except Exception as e:
        print(f"❌ [DEBUG] Error obteniendo carpetas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo carpetas: {str(e)}"
        )

@router.post("/carpetas")
async def crear_carpeta(
    datos: CarpetaCreate,
    abogado = Depends(get_current_abogado)
):
    """Crea una nueva carpeta."""
    try:
        print(f"📁 [DEBUG] Creando carpeta: {datos.nombre}")
        
        carpeta = await carpeta_service.crear_carpeta(abogado['id'], datos)
        
        return {
            "success": True,
            "mensaje": "Carpeta creada exitosamente",
            "carpeta": carpeta
        }
    except Exception as e:
        print(f"❌ [DEBUG] Error creando carpeta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando carpeta: {str(e)}"
        )

@router.delete("/carpetas/{carpeta_id}")
async def eliminar_carpeta(
    carpeta_id: str,
    abogado = Depends(get_current_abogado)
):
    """Elimina una carpeta."""
    try:
        # Verificar que la carpeta pertenece al abogado
        response = supabase.table('carpetas')\
            .delete()\
            .eq('id', carpeta_id)\
            .eq('abogado_id', abogado['id'])\
            .execute()
        
        return {
            "success": True,
            "mensaje": "Carpeta eliminada exitosamente"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando carpeta: {str(e)}"
        )

# =====================================
# ENDPOINTS DE SESIONES/CHATS
# =====================================

@router.get("/sesiones")
async def obtener_sesiones(
    carpeta_id: Optional[str] = None,
    abogado = Depends(get_current_abogado)
):
    """Obtiene las sesiones del abogado, opcionalmente filtradas por carpeta."""
    try:
        sesiones = await chat_service.obtener_sesiones(abogado['id'], carpeta_id)
        
        return {
            "success": True,
            "sesiones": sesiones
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo sesiones: {str(e)}"
        )

@router.post("/sesiones")
async def crear_sesion(
    datos: ChatSesionCreate,
    abogado = Depends(get_current_abogado)
):
    """Crea una nueva sesión de chat."""
    try:
        session_id = str(uuid.uuid4())
        
        sesion = await chat_service.crear_sesion(
            abogado['id'], session_id, datos
        )
        
        return {
            "success": True,
            "mensaje": "Sesión creada exitosamente",
            "sesion": sesion,
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando sesión: {str(e)}"
        )

@router.put("/sesiones/{sesion_id}/carpeta")
async def mover_sesion_carpeta(
    sesion_id: str,
    carpeta_id: Optional[str],
    abogado = Depends(get_current_abogado)
):
    """Mueve una sesión a otra carpeta."""
    try:
        response = supabase.table('chat_sesiones')\
            .update({'carpeta_id': carpeta_id})\
            .eq('id', sesion_id)\
            .eq('abogado_id', abogado['id'])\
            .execute()
        
        return {
            "success": True,
            "mensaje": "Sesión movida exitosamente"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error moviendo sesión: {str(e)}"
        )

# =====================================
# ENDPOINTS DE DOCUMENTOS
# =====================================

@router.post("/documentos/upload")
async def subir_documento(
    archivo: UploadFile = File(...),
    tipo_demanda: str = Form(...),
    categoria: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    abogado = Depends(get_current_abogado)
):
    """Sube un documento para entrenamiento."""
    try:
        print(f"📄 [DEBUG] Subiendo documento: {archivo.filename}")
        
        # Validar tipo de archivo
        if not archivo.filename.endswith(('.pdf', '.docx', '.doc')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten archivos PDF, DOC y DOCX"
            )
        
        # Leer archivo
        archivo_bytes = await archivo.read()
        
        # Generar path único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = archivo.filename.split('.')[-1]
        file_path = f"{abogado['id']}/{tipo_demanda}/{timestamp}_{archivo.filename}"
        
        # Subir a Supabase Storage
        archivo_url = await storage_service.subir_archivo(
            "documentos-entrenamiento",
            file_path,
            archivo_bytes,
            archivo.content_type
        )
        
        # Procesar tags
        tags_list = []
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',')]
        
        # Registrar en base de datos
        documento = await documento_service.subir_documento(
            abogado['id'],
            archivo_url,
            DocumentoCreate(
                nombre_archivo=archivo.filename,
                tipo_demanda=tipo_demanda,
                categoria=categoria,
                tags=tags_list
            )
        )
        
        print(f"✅ [DEBUG] Documento registrado: {documento['id']}")
        
        # TODO: Aquí puedes agregar una tarea asíncrona para procesar el documento
        # y vectorizarlo en Qdrant
        
        return {
            "success": True,
            "mensaje": "Documento subido exitosamente",
            "documento": documento
        }
        
    except Exception as e:
        print(f"❌ [DEBUG] Error subiendo documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subiendo documento: {str(e)}"
        )

@router.get("/documentos")
async def obtener_documentos(
    tipo_demanda: Optional[str] = None,
    abogado = Depends(get_current_abogado)
):
    """Obtiene los documentos del abogado."""
    try:
        documentos = await documento_service.obtener_documentos(
            abogado['id'], tipo_demanda
        )
        
        return {
            "success": True,
            "documentos": documentos
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo documentos: {str(e)}"
        )

@router.delete("/documentos/{documento_id}")
async def eliminar_documento(
    documento_id: str,
    abogado = Depends(get_current_abogado)
):
    """Elimina un documento."""
    try:
        # Obtener datos del documento
        doc_response = supabase.table('documentos_entrenamiento')\
            .select('archivo_url')\
            .eq('id', documento_id)\
            .eq('abogado_id', abogado['id'])\
            .single()\
            .execute()
        
        if not doc_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento no encontrado"
            )
        
        # Eliminar archivo de storage
        # TODO: Extraer path del URL y eliminar archivo
        
        # Eliminar de base de datos
        supabase.table('documentos_entrenamiento')\
            .delete()\
            .eq('id', documento_id)\
            .eq('abogado_id', abogado['id'])\
            .execute()
        
        return {
            "success": True,
            "mensaje": "Documento eliminado exitosamente"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando documento: {str(e)}"
        ) 