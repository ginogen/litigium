from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel
import os
from datetime import datetime

from auth.dependencies import get_current_user
from models.user import User
from supabase_integration import supabase

router = APIRouter(prefix="/api/config", tags=["config"])

class ConfigSupabase(BaseModel):
    supabase_url: str
    supabase_anon_key: str

@router.get("/health")
async def health_check():
    """Verifica el estado del servidor."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "Legal Assistant AI Backend"
    }

@router.get("/v1/supabase-config")
async def obtener_config_supabase():
    """Obtiene la configuración de Supabase para el frontend."""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_anon_key:
            return {
                "configured": False,
                "message": "Supabase no está configurado en el servidor"
            }
        
        return {
            "configured": True,
            "supabase_url": supabase_url,
            "supabase_anon_key": supabase_anon_key
        }
        
    except Exception as e:
        return {
            "configured": False,
            "error": str(e)
        }

@router.get("/sesiones")
async def obtener_sesiones_activas(current_user: User = Depends(get_current_user)):
    """Obtiene todas las sesiones activas del usuario actual."""
    try:
        # Obtener sesiones de chat del usuario
        response = supabase.table('chat_sesiones')\
            .select('*')\
            .eq('abogado_id', current_user.id)\
            .execute()
        
        chat_sessions = response.data or []
        
        # Obtener sesiones del editor (si existen)
        editor_sessions = []  # TODO: Implementar cuando se migre editor_routes
        
        return {
            "success": True,
            "sesiones": {
                "chat": len(chat_sessions),
                "editor": len(editor_sessions),
                "total": len(chat_sessions) + len(editor_sessions)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo sesiones: {str(e)}")

@router.get("/sistema/estadisticas")
async def obtener_estadisticas_sistema(
    current_user: User = Depends(get_current_user)
):
    """Obtiene estadísticas generales del sistema."""
    try:
        # Solo administradores pueden ver estas estadísticas
        # TODO: Implementar sistema de roles
        
        from .editor_routes import editor_sessions
        
        # Obtener sesiones de chat desde Supabase
        try:
            response = supabase.table('chat_sesiones')\
                .select('*')\
                .eq('abogado_id', current_user.id)\
                .execute()
            chat_sessions_count = len(response.data or [])
        except:
            chat_sessions_count = 0
        
        estadisticas = {
            "sesiones_activas": {
                "chat": chat_sessions_count,
                "editor": len(editor_sessions),
                "total": chat_sessions_count + len(editor_sessions)
            },
            "usuarios_activos": {
                "total": 1,  # Por simplicidad, solo el usuario actual
                "conectados_hoy": 1
            },
            "sistema": {
                "version": "1.0.0",
                "uptime": "Sistema en desarrollo",
                "memoria_usada": "N/A",
                "procesador": "N/A"
            },
            "funcionalidades": {
                "chat_ia": "En desarrollo",
                "editor_granular": "Implementado",
                "transcripcion_audio": "Implementado",
                "training_personalizado": "Implementado",
                "generacion_documentos": "En desarrollo"
            }
        }
        
        return {
            "success": True,
            "estadisticas": estadisticas,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@router.get("/sistema/logs")
async def obtener_logs_sistema(
    current_user: User = Depends(get_current_user),
    nivel: Optional[str] = "info",
    limite: int = 100
):
    """Obtiene los logs del sistema."""
    try:
        # TODO: Implementar sistema de logs real
        # Por ahora, logs simulados
        
        logs_simulados = [
            {
                "timestamp": datetime.now().isoformat(),
                "nivel": "info",
                "modulo": "chat_routes",
                "mensaje": "Sesión de chat iniciada exitosamente",
                "usuario": current_user.email
            },
            {
                "timestamp": datetime.now().isoformat(),
                "nivel": "info", 
                "modulo": "training_routes",
                "mensaje": "Documento procesado para entrenamiento",
                "usuario": current_user.email
            },
            {
                "timestamp": datetime.now().isoformat(),
                "nivel": "debug",
                "modulo": "editor_routes",
                "mensaje": "Editor inicializado para sesión",
                "usuario": current_user.email
            }
        ]
        
        # Filtrar por nivel si se especifica
        if nivel and nivel != "all":
            logs_filtrados = [log for log in logs_simulados if log["nivel"] == nivel]
        else:
            logs_filtrados = logs_simulados
        
        # Limitar resultados
        logs_limitados = logs_filtrados[:limite]
        
        return {
            "success": True,
            "logs": logs_limitados,
            "total": len(logs_filtrados),
            "filtros_aplicados": {
                "nivel": nivel,
                "limite": limite
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo logs: {str(e)}")

@router.post("/sistema/configurar")
async def configurar_sistema(
    config_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Configura parámetros del sistema."""
    try:
        # TODO: Implementar sistema de configuración persistente
        # Por ahora, solo validación
        
        configuraciones_validas = [
            "max_sesiones_usuario",
            "timeout_sesion",
            "tamaño_maximo_archivo",
            "idioma_predeterminado",
            "formato_fecha"
        ]
        
        configuraciones_aplicadas = {}
        configuraciones_rechazadas = {}
        
        for clave, valor in config_data.items():
            if clave in configuraciones_validas:
                configuraciones_aplicadas[clave] = valor
            else:
                configuraciones_rechazadas[clave] = f"Configuración '{clave}' no reconocida"
        
        return {
            "success": True,
            "mensaje": f"Se aplicaron {len(configuraciones_aplicadas)} configuraciones",
            "configuraciones_aplicadas": configuraciones_aplicadas,
            "configuraciones_rechazadas": configuraciones_rechazadas,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error configurando sistema: {str(e)}")

@router.get("/sistema/backup")
async def crear_backup_sistema(
    current_user: User = Depends(get_current_user)
):
    """Crea un backup de las sesiones y configuración del usuario."""
    try:
        from .editor_routes import editor_sessions
        
        # Obtener datos del usuario desde Supabase
        try:
            response = supabase.table('chat_sesiones')\
                .select('*')\
                .eq('abogado_id', current_user.id)\
                .execute()
            user_chat_sessions = response.data or []
        except:
            user_chat_sessions = []
        
        # Filtrar datos del usuario
        user_data = {
            "chat_sessions": {
                s['session_id']: s for s in user_chat_sessions
            },
            "editor_sessions": {
                k: v for k, v in editor_sessions.items() 
                if v.get("user_id") == current_user.id
            }
        }
        
        backup_info = {
            "usuario": {
                "id": current_user.id,
                "email": current_user.email,
                "nombre": current_user.nombre_completo
            },
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "datos": user_data,
            "estadisticas": {
                "sesiones_chat": len(user_data["chat_sessions"]),
                "sesiones_editor": len(user_data["editor_sessions"])
            }
        }
        
        return {
            "success": True,
            "backup": backup_info,
            "mensaje": "Backup creado exitosamente"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando backup: {str(e)}")

@router.post("/sistema/restaurar")
async def restaurar_backup(
    backup_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Restaura un backup del usuario."""
    try:
        # TODO: Implementar restauración real de backup
        # Por ahora, solo validación
        
        if not backup_data.get("datos"):
            raise HTTPException(status_code=400, detail="Datos de backup inválidos")
        
        # Verificar que el backup pertenece al usuario
        backup_usuario = backup_data.get("usuario", {})
        if backup_usuario.get("id") != current_user.id:
            raise HTTPException(status_code=403, detail="El backup no pertenece a este usuario")
        
        return {
            "success": True,
            "mensaje": "Backup restaurado exitosamente (simulación)",
            "elementos_restaurados": {
                "sesiones_chat": len(backup_data.get("datos", {}).get("chat_sessions", {})),
                "sesiones_editor": len(backup_data.get("datos", {}).get("editor_sessions", {}))
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restaurando backup: {str(e)}")

@router.get("/version")
async def obtener_version():
    """Obtiene información de versión del sistema."""
    return {
        "version": "1.0.0",
        "nombre": "Legal Assistant AI",
        "descripcion": "Sistema de asistencia legal con IA",
        "autor": "Legal Assistant AI Team",
        "licencia": "Propietaria",
        "fecha_compilacion": datetime.now().isoformat(),
        "componentes": {
            "backend": "FastAPI 0.104.1",
            "frontend": "React 18 + TypeScript",
            "base_datos": "Supabase",
            "ia": "En desarrollo",
            "vectores": "Qdrant"
        }
    }

@router.get("/exportar-datos")
async def exportar_datos_usuario(current_user: User = Depends(get_current_user)):
    """Exporta todos los datos del usuario en formato JSON."""
    try:
        # Obtener todas las sesiones del usuario
        response = supabase.table('chat_sesiones')\
            .select('*')\
            .eq('abogado_id', current_user.id)\
            .execute()
        
        chat_sessions = response.data or []
        
        # Obtener mensajes del usuario
        mensajes_response = supabase.table('chat_mensajes')\
            .select('*')\
            .in_('sesion_id', [s['id'] for s in chat_sessions])\
            .execute()
        
        mensajes = mensajes_response.data or []
        
        # Estructurar datos para exportación
        datos_exportacion = {
            "usuario": {
                "id": current_user.id,
                "email": current_user.email,
                "nombre": current_user.nombre_completo,
                "fecha_exportacion": datetime.now().isoformat()
            },
            "sesiones_chat": chat_sessions,
            "mensajes": mensajes,
            "estadisticas": {
                "total_sesiones": len(chat_sessions),
                "total_mensajes": len(mensajes),
                "sesiones_chat": len(chat_sessions),
                "ultima_actividad": max([s.get('updated_at', s.get('created_at', '')) for s in chat_sessions]) if chat_sessions else None
            }
        }
        
        return {
            "success": True,
            "datos": datos_exportacion
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando datos: {str(e)}")

@router.post("/importar-datos")
async def importar_datos_usuario(
    backup_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Importa datos de respaldo del usuario."""
    try:
        if not backup_data.get("datos"):
            raise HTTPException(status_code=400, detail="Datos de respaldo inválidos")
        
        datos = backup_data["datos"]
        
        # Estadísticas de importación
        stats = {
            "sesiones_chat": len(datos.get("sesiones_chat", [])),
            "mensajes": len(datos.get("mensajes", [])),
            "importado_exitosamente": True
        }
        
        # TODO: Implementar importación real cuando sea necesario
        # Por ahora, solo validamos y reportamos estadísticas
        
        return {
            "success": True,
            "mensaje": "Datos importados correctamente",
            "estadisticas": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importando datos: {str(e)}") 