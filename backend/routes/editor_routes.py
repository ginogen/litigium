from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ..auth.dependencies import get_current_user
from ..models.user import User
from supabase_integration import supabase_admin as supabase

router = APIRouter(prefix="/api/editor", tags=["editor"])

# Modelos para el editor
class ComandoEdicion(BaseModel):
    comando: str = Field(..., description="Comando de edición en lenguaje natural")
    session_id: str = Field(..., description="ID de la sesión")
    texto_seleccionado: Optional[str] = Field(None, description="Texto seleccionado para editar")
    contexto_seleccion: Optional[str] = Field(None, description="Contexto circundante del texto seleccionado")

class ParrafoData(BaseModel):
    numero: int
    contenido: str
    tipo: str
    modificado: bool = False
    fecha_modificacion: Optional[str] = None

class EditHistoryItem(BaseModel):
    id: str
    comando: str
    operacion: str
    parrafo_numero: Optional[int] = None
    timestamp: str
    exito: bool
    mensaje: Optional[str] = None
    resultado: Optional[Any] = None

# Almacenamiento temporal del editor
editor_sessions = {}

async def obtener_sesion_chat_supabase(session_id: str, user_id: str) -> Dict:
    """Obtiene una sesión de chat desde Supabase verificando permisos."""
    try:
        print(f"🔍 Buscando sesión de chat para session_id: {session_id}, user_id: {user_id}")
        
        # Obtener el perfil del abogado
        abogado_response = supabase.table('abogados')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        
        if not abogado_response.data or len(abogado_response.data) == 0:
            print(f"❌ No se encontró perfil de abogado para user_id: {user_id}")
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data[0]['id']
        print(f"✅ Abogado encontrado: {abogado_id}")
        
        # Obtener sesión de chat
        response = supabase.table('chat_sesiones')\
            .select('*')\
            .eq('session_id', session_id)\
            .eq('abogado_id', abogado_id)\
            .execute()
        
        print(f"📊 Sesiones de chat encontradas: {len(response.data) if response.data else 0}")
        
        if not response.data or len(response.data) == 0:
            print(f"❌ No se encontró sesión de chat para session_id: {session_id}")
            raise HTTPException(status_code=404, detail="Sesión de chat no encontrada")
        
        print(f"✅ Sesión de chat encontrada")
        return response.data[0]
    except HTTPException:
        # Re-lanzar HTTPExceptions tal como están
        raise
    except Exception as e:
        print(f"❌ Error obteniendo sesión de chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo sesión: {str(e)}")

@router.post("/inicializar")
async def inicializar_editor_demanda(
    session_data: Dict[str, str],
    current_user: User = Depends(get_current_user)
):
    """Inicializa el editor granular para una demanda generada."""
    try:
        session_id = session_data.get('session_id')
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id requerido")
        
        # Verificar que la sesión de chat existe en Supabase
        chat_session = await obtener_sesion_chat_supabase(session_id, current_user.id)
        
        # TODO: Integrar con sistema de análisis de párrafos
        # Por ahora, crear párrafos de ejemplo
        texto_ejemplo = """
        **DEMANDA LABORAL**
        
        I. HECHOS
        El demandante trabajó para la empresa desde enero de 2020 hasta diciembre de 2023.
        Fue despedido sin causa justificada el día 15 de diciembre de 2023.
        
        II. DERECHO
        El despido sin causa configura una violación al derecho laboral argentino.
        Corresponde indemnización según el artículo 245 de la LCT.
        
        III. PETITORIO
        Solicito se condene al demandado al pago de indemnización por despido.
        """
        
        # Simular análisis en párrafos
        parrafos = [
            {
                "numero": 1,
                "contenido": "El demandante trabajó para la empresa desde enero de 2020 hasta diciembre de 2023.",
                "tipo": "hechos",
                "modificado": False
            },
            {
                "numero": 2, 
                "contenido": "Fue despedido sin causa justificada el día 15 de diciembre de 2023.",
                "tipo": "hechos",
                "modificado": False
            },
            {
                "numero": 3,
                "contenido": "El despido sin causa configura una violación al derecho laboral argentino.",
                "tipo": "derecho", 
                "modificado": False
            },
            {
                "numero": 4,
                "contenido": "Corresponde indemnización según el artículo 245 de la LCT.",
                "tipo": "derecho",
                "modificado": False
            },
            {
                "numero": 5,
                "contenido": "Solicito se condene al demandado al pago de indemnización por despido.",
                "tipo": "petitorio",
                "modificado": False
            }
        ]
        
        # Inicializar sesión del editor
        editor_sessions[session_id] = {
            "parrafos": parrafos,
            "historial_ediciones": [],
            "texto_original": texto_ejemplo,
            "texto_actual": texto_ejemplo,
            "user_id": current_user.id,
            "initialized_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "mensaje": "Editor inicializado correctamente",
            "parrafos": parrafos,
            "total_parrafos": len(parrafos)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error inicializando editor: {str(e)}"
        }

@router.post("/procesar-comando")
async def procesar_comando_edicion(
    comando_data: ComandoEdicion,
    current_user: User = Depends(get_current_user)
):
    """Procesa un comando de edición en lenguaje natural."""
    try:
        session_id = comando_data.session_id
        
        # Verificar que la sesión del editor existe
        if session_id not in editor_sessions:
            raise HTTPException(status_code=404, detail="Sesión del editor no encontrada")
        
        editor_session = editor_sessions[session_id]
        
        # Verificar permisos
        if editor_session.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="Sin permisos para esta sesión")
        
        # Verificar si es un comando de edición global
        if comando_data.comando.startswith("GLOBAL:"):
            print("🌍 Detectada solicitud de modificación global desde editor...")
            try:
                instruccion_global = comando_data.comando.replace("GLOBAL:", "").strip()
                
                from rag.editor_demandas import procesar_edicion_global
                
                print(f"🎯 [EDITOR] Procesando edición global:")
                print(f"   💭 Instrucción: '{instruccion_global}'")
                
                resultado_global = procesar_edicion_global(instruccion_global, session_id)
                
                # Convertir formato del resultado para la API del editor
                if resultado_global.get('exito'):
                    resultado = {
                        "success": True,
                        "message": resultado_global.get('mensaje', 'Modificación global aplicada exitosamente'),
                        "cambios_realizados": f"{resultado_global.get('parrafos_modificados', 0)} párrafos modificados",
                        "metodo_usado": resultado_global.get('metodo_usado', 'edicion_global_ia')
                    }
                else:
                    resultado = {
                        "success": False,
                        "error": resultado_global.get('error', 'Error en modificación global')
                    }
                    
            except Exception as e:
                print(f"⚠️ Error procesando modificación global: {e}")
                resultado = {
                    "success": False,
                    "error": f"Error en modificación global: {str(e)}"
                }
        else:
            # TODO: Integrar con IA para procesar comandos normales
            # Por ahora, simulación simple
            resultado = {
                "success": True,
                "message": f"Comando procesado: '{comando_data.comando[:50]}...'",
                "cambios_realizados": "Simulación de edición aplicada",
                "parrafos_modificados": []
            }
        
        # Agregar al historial
        historial_item = {
            "id": str(len(editor_session["historial_ediciones"]) + 1),
            "comando": comando_data.comando,
            "operacion": "edicion_global" if comando_data.comando.startswith("GLOBAL:") else "edicion_ia",
            "timestamp": datetime.now().isoformat(),
            "exito": resultado.get("success", False),
            "mensaje": resultado.get("message", resultado.get("error", "Comando procesado"))
        }
        
        editor_session["historial_ediciones"].append(historial_item)
        
        return resultado
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error procesando comando: {str(e)}"
        }

@router.get("/parrafos/{session_id}")
async def obtener_parrafos_demanda(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtiene los párrafos estructurados de una demanda."""
    try:
        if session_id not in editor_sessions:
            raise HTTPException(status_code=404, detail="Sesión del editor no encontrada")
        
        editor_session = editor_sessions[session_id]
        
        # Verificar permisos
        if editor_session.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="Sin permisos para esta sesión")
        
        return {
            "success": True,
            "parrafos": editor_session["parrafos"],
            "total_parrafos": len(editor_session["parrafos"])
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error obteniendo párrafos: {str(e)}"
        }

@router.get("/historial/{session_id}")
async def obtener_historial_ediciones(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtiene el historial de ediciones de una demanda."""
    try:
        if session_id not in editor_sessions:
            raise HTTPException(status_code=404, detail="Sesión del editor no encontrada")
        
        editor_session = editor_sessions[session_id]
        
        # Verificar permisos
        if editor_session.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="Sin permisos para esta sesión")
        
        return {
            "success": True,
            "historial": editor_session["historial_ediciones"],
            "total_ediciones": len(editor_session["historial_ediciones"])
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error obteniendo historial: {str(e)}"
        }

@router.get("/texto-completo/{session_id}")
async def obtener_texto_completo_actualizado(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtiene el texto completo actualizado con todas las ediciones."""
    try:
        # Primero intentar obtener desde la sesión del editor en memoria
        if session_id in editor_sessions:
            editor_session = editor_sessions[session_id]
            
            # Verificar permisos
            if editor_session.get("user_id") != current_user.id:
                raise HTTPException(status_code=403, detail="Sin permisos para esta sesión")
            
            return {
                "success": True,
                "texto_completo": editor_session.get("texto_actual", editor_session.get("texto_original", "")),
                "timestamp": datetime.now().isoformat()
            }
        
        # Si no hay sesión de editor, obtener demanda desde base de datos
        try:
            print(f"🔍 Buscando demanda para session_id: {session_id}, user_id: {current_user.id}")
            
            # Primero hacer una consulta sin .single() para ver qué hay
            test_response = supabase.table('demandas_generadas')\
                .select('*')\
                .eq('session_id', session_id)\
                .execute()
            
            print(f"📊 Total de demandas con session_id {session_id}: {len(test_response.data) if test_response.data else 0}")
            if test_response.data:
                for i, demanda in enumerate(test_response.data):
                    print(f"   Demanda {i+1}: user_id={demanda.get('user_id')}, abogado_id={demanda.get('abogado_id')}, tipo={demanda.get('tipo_demanda')}")
            
            # Buscar demanda generada por session_id y user_id
            demanda_response = supabase.table('demandas_generadas')\
                .select('*')\
                .eq('session_id', session_id)\
                .eq('user_id', current_user.id)\
                .execute()
            
            print(f"📊 Demandas encontradas por user_id: {len(demanda_response.data) if demanda_response.data else 0}")
            
            # Si no se encuentra por user_id, intentar por abogado_id como fallback
            if not demanda_response.data:
                print(f"⚠️ No encontrado por user_id, intentando por abogado_id...")
                
                # Obtener el perfil del abogado
                abogado_response = supabase.table('abogados')\
                    .select('*')\
                    .eq('user_id', current_user.id)\
                    .single()\
                    .execute()
                
                if abogado_response.data:
                    abogado_id = abogado_response.data['id']
                    print(f"🔍 Buscando por abogado_id: {abogado_id}")
                    
                    # Buscar por abogado_id
                    demanda_response = supabase.table('demandas_generadas')\
                        .select('*')\
                        .eq('session_id', session_id)\
                        .eq('abogado_id', abogado_id)\
                        .execute()
                    
                    print(f"📊 Demandas encontradas por abogado_id: {len(demanda_response.data) if demanda_response.data else 0}")
            
            # Tomar la primera demanda si encontramos alguna
            demanda_data = None
            if demanda_response.data and len(demanda_response.data) > 0:
                demanda_data = demanda_response.data[0]  # Tomar la primera demanda
                print(f"✅ Usando demanda: ID={demanda_data.get('id')}, tipo={demanda_data.get('tipo_demanda')}")
            
            if demanda_data and demanda_data.get('texto_demanda'):
                
                # Intentar obtener archivo desde Supabase Storage si existe
                archivo_url = demanda_data.get('archivo_docx_url')
                if archivo_url:
                    try:
                        # Si hay URL de Storage, intentar descargar el archivo
                        print(f"🔍 Intentando obtener archivo desde Storage: {archivo_url}")
                        # Extraer nombre del archivo de la URL
                        import re
                        match = re.search(r'/([^/]+\.docx)$', archivo_url)
                        if match:
                            nombre_archivo = match.group(1)
                            storage_response = supabase.storage.from_('demandas-generadas').download(nombre_archivo)
                            if storage_response:
                                print(f"✅ Archivo descargado desde Storage")
                                # Aquí podrías procesar el archivo si necesitas mostrar contenido específico
                    except Exception as storage_error:
                        print(f"⚠️ Error descargando desde Storage: {storage_error}")
                
                print(f"✅ Demanda encontrada: {demanda_data.get('tipo_demanda', 'N/A')}")
                print(f"📝 Contenido encontrado: {len(demanda_data['texto_demanda'])} caracteres")
                
                return {
                    "success": True,
                    "texto_completo": demanda_data['texto_demanda'],
                    "timestamp": datetime.now().isoformat(),
                    "desde_base_datos": True,
                    "tipo_demanda": demanda_data.get('tipo_demanda', 'N/A'),
                    "estado": demanda_data.get('estado', 'N/A'),
                    "archivo_url": archivo_url,
                    "tiene_archivo_storage": bool(archivo_url)
                }
            
            # No se encontró la demanda
            print(f"❌ No se encontró demanda para session_id: {session_id}")
            return {
                "success": False,
                "error": f"No se encontró demanda para session_id {session_id}",
                "session_id": session_id,
                "user_id": current_user.id,
                "consulta_fallida": True
            }
            
        except Exception as e:
            print(f"❌ Error en consulta de demanda: {str(e)}")
            return {
                "success": False,
                "error": f"Error en consulta de demanda: {str(e)}",
                "session_id": session_id,
                "user_id": current_user.id
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error obteniendo texto: {str(e)}"
        } 