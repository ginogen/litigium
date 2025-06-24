from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
from pydantic import BaseModel, Field

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ..auth.dependencies import get_current_user
from ..models.user import User
from supabase_integration import (
    ChatService, 
    ChatSesionCreate,
    supabase,
    supabase_admin
)

# Importar el chat agent inteligente
try:
    from rag.chat_agent import get_chat_agent, reset_chat_agent
    CHAT_AGENT_AVAILABLE = True
    print("✅ ChatAgent inteligente disponible")
    # Resetear la instancia para asegurar logs actuales
    reset_chat_agent()
    print("🔄 ChatAgent reseteado para aplicar cambios")
except ImportError as e:
    print(f"⚠️ ChatAgent no disponible: {e}")
    CHAT_AGENT_AVAILABLE = False

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Ya no necesitamos almacenamiento temporal - todo va a Supabase

# Modelos Pydantic
class DatosCliente(BaseModel):
    nombre_completo: str = Field(..., description="Nombre completo del cliente")
    dni: str = Field(..., description="DNI del cliente")
    domicilio: str = Field(..., description="Domicilio del cliente")
    telefono: Optional[str] = Field(None, description="Teléfono del cliente")
    email: Optional[str] = Field(None, description="Email del cliente")
    fecha_nacimiento: Optional[str] = Field(None, description="Fecha de nacimiento")
    estado_civil: Optional[str] = Field(None, description="Estado civil")
    ocupacion: Optional[str] = Field(None, description="Ocupación")
    motivo_demanda: Optional[str] = Field(None, description="Motivo principal de la demanda")

class MensajeChat(BaseModel):
    session_id: str
    mensaje: str
    tipo: str = Field(default="user", description="Tipo de mensaje: user, bot, system")

class SolicitudDemanda(BaseModel):
    session_id: str
    tipo_demanda: str
    datos_cliente: DatosCliente
    hechos_adicionales: str = ""
    notas_abogado: str = ""

class RespuestaChat(BaseModel):
    session_id: str
    respuesta: str
    tipo: str
    timestamp: str
    opciones: Optional[List[str]] = None
    requiere_datos: Optional[bool] = False
    mostrar_descarga: Optional[bool] = False
    mostrar_preview: Optional[bool] = False
    mostrar_refrescar: Optional[bool] = False

async def obtener_sesion_con_abogado_id(session_id: str, abogado_id: str) -> Dict:
    """Obtiene una sesión específica verificando que pertenezca al abogado."""
    try:
        print(f"🔍 Buscando sesión - session_id: {session_id}, abogado_id: {abogado_id}")
        
        # Primero, listar todas las sesiones del abogado para debugging
        all_sessions = supabase_admin.table('chat_sesiones')\
            .select('session_id, id, titulo')\
            .eq('abogado_id', abogado_id)\
            .execute()
        
        print(f"🔍 Sesiones disponibles del abogado: {len(all_sessions.data)} sesiones")
        for sesion in all_sessions.data:
            print(f"   - session_id: {sesion['session_id']}, id: {sesion['id']}, titulo: {sesion['titulo']}")
        
        response = supabase_admin.table('chat_sesiones')\
            .select('*')\
            .eq('session_id', session_id)\
            .eq('abogado_id', abogado_id)\
            .single()\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        print(f"✅ Sesión encontrada correctamente")
        return response.data
    except Exception as e:
        print(f"❌ Error en obtener_sesion_con_abogado_id: {str(e)}")
        if "No rows found" in str(e) or "0 rows" in str(e):
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        raise HTTPException(status_code=500, detail=f"Error obteniendo sesión: {str(e)}")

async def actualizar_datos_sesion(sesion_db_id: str, datos_cliente: Dict, tipo_demanda: str = None, hechos_adicionales: str = None):
    """Actualiza los datos de una sesión en la base de datos."""
    try:
        update_data = {
            "updated_at": datetime.now().isoformat()
        }
        
        if datos_cliente:
            update_data["cliente_datos"] = datos_cliente
            if datos_cliente.get("nombre_completo"):
                update_data["cliente_nombre"] = datos_cliente["nombre_completo"]
            if datos_cliente.get("dni"):
                update_data["cliente_dni"] = datos_cliente["dni"]
        
        if tipo_demanda:
            update_data["tipo_demanda"] = tipo_demanda
        
        if hechos_adicionales:
            update_data["hechos_adicionales"] = hechos_adicionales
        
        supabase_admin.table('chat_sesiones')\
            .update(update_data)\
            .eq('id', sesion_db_id)\
            .execute()
    except Exception as e:
        print(f"❌ Error actualizando sesión: {str(e)}")

def procesar_mensaje_inteligente(mensaje: str, datos_sesion: Dict) -> Dict:
    """Función de procesamiento inteligente simplificada sin dependencias externas."""
    
    # Detectar tipos de demanda por palabras clave
    tipos_demanda = {
        "despido": "Despido injustificado",
        "accidente": "Accidente de trabajo", 
        "divorcio": "Divorcio contencioso",
        "daños": "Reclamo de daños y perjuicios",
        "blanco": "Empleados En Blanco",
        "negro": "Empleados En Negro",
        "licencia": "Demanda Licencia Médica",
        "solidaridad": "Demanda Solidaridad Laboral"
    }
    
    mensaje_lower = mensaje.lower()
    tipo_detectado = None
    
    # Detectar tipo de demanda
    for palabra, tipo in tipos_demanda.items():
        if palabra in mensaje_lower:
            tipo_detectado = tipo
            break
    
    # Detectar información del cliente básica
    import re
    datos_detectados = {}
    
    # Detectar nombres (2-3 palabras que empiecen con mayúscula)
    match_nombre = re.search(r'\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})\b', mensaje)
    if match_nombre and 'quiero' not in match_nombre.group(1).lower():
        datos_detectados["nombre_completo"] = match_nombre.group(1)
    
    # Detectar DNI (7-8 dígitos)
    match_dni = re.search(r'\b(\d{7,8})\b', mensaje)
    if match_dni:
        datos_detectados["dni"] = match_dni.group(1)
    
    # Detectar direcciones básicas
    match_direccion = re.search(r'\b((?:Paraguay|Rivadavia|Av\.|Avenida|Calle)\s+[^,\n]+?\s*\d+[^,\n]*)', mensaje, re.IGNORECASE)
    if match_direccion:
        datos_detectados["domicilio"] = match_direccion.group(1).strip()
    
    # Obtener datos existentes de la sesión
    datos_cliente_existentes = datos_sesion.get("cliente_datos", {})
    if isinstance(datos_cliente_existentes, str):
        import json
        try:
            datos_cliente_existentes = json.loads(datos_cliente_existentes)
        except:
            datos_cliente_existentes = {}
    
    # Actualizar datos con los nuevos detectados
    datos_cliente_actualizados = {**datos_cliente_existentes, **datos_detectados}
    
    # Detectar hechos relevantes
    hechos_keywords = []
    if "despid" in mensaje_lower:
        hechos_keywords.append("despido")
    if "sin causa" in mensaje_lower:
        hechos_keywords.append("sin causa justificada")
    if "licencia" in mensaje_lower:
        hechos_keywords.append("licencia médica")
    if "empresa" in mensaje_lower:
        hechos_keywords.append("problemas laborales")
    
    hechos_adicionales = datos_sesion.get("hechos_adicionales", "")
    if hechos_keywords:
        hechos_texto = f"Cliente reporta: {', '.join(hechos_keywords)}. Contexto: {mensaje[:200]}"
        hechos_adicionales = hechos_texto
    
    # Determinar respuesta basada en información disponible
    tiene_nombre = bool(datos_cliente_actualizados.get("nombre_completo"))
    tiene_dni = bool(datos_cliente_actualizados.get("dni"))
    tiene_tipo = bool(tipo_detectado or datos_sesion.get("tipo_demanda"))
    tiene_hechos = bool(hechos_adicionales)
    
    # Retornar datos para actualizar la sesión
    respuesta = {
        "datos_cliente": datos_cliente_actualizados,
        "tipo_demanda": tipo_detectado or datos_sesion.get("tipo_demanda"),
        "hechos_adicionales": hechos_adicionales
    }
    
    if tiene_nombre and tiene_dni and tiene_tipo and tiene_hechos:
        respuesta["mensaje"] = f"✅ **Información completa recibida**\n\n**Cliente:** {datos_cliente_actualizados.get('nombre_completo')}\n**DNI:** {datos_cliente_actualizados.get('dni')}\n**Tipo:** {respuesta['tipo_demanda']}\n**Situación:** {hechos_keywords[0] if hechos_keywords else 'No especificada'}\n\n¿Deseas que proceda a generar la demanda?\n\n*Nota: Funcionalidad completa disponible con configuración de OpenAI*"
        respuesta["opciones"] = ["Sí, generar demanda", "Agregar más información", "Cambiar tipo de demanda"]
    elif tipo_detectado or datos_sesion.get("tipo_demanda"):
        info_faltante = []
        if not tiene_nombre:
            info_faltante.append("nombre completo del cliente")
        if not tiene_dni:
            info_faltante.append("DNI")
        if not tiene_hechos:
            info_faltante.append("detalles del caso")
        
        respuesta["mensaje"] = f"He detectado que necesitas ayuda con: **{respuesta['tipo_demanda']}**\n\nPara generar la demanda necesito:\n• {chr(10).join(['• ' + info for info in info_faltante])}\n\nPuedes proporcionarme toda la información junta."
    else:
        respuesta["mensaje"] = "¡Hola! Soy tu asistente legal. Para ayudarte mejor, cuéntame:\n\n• ¿Qué tipo de demanda necesitas?\n• Datos del cliente (nombre, DNI, dirección)\n• Detalles del caso\n\nPuedes escribir todo junto de forma natural.\n\n*Ejemplos:*\n- \"Despido injustificado, Juan Pérez, DNI 12345678\"\n- \"Accidente laboral, necesito demanda\""
        respuesta["opciones"] = ["Despido injustificado", "Accidente de trabajo", "Divorcio", "Empleados en blanco", "Empleados en negro"]
    
    respuesta["mostrar_descarga"] = False
    respuesta["mostrar_preview"] = False
    respuesta["demanda_generada"] = False
    
    return respuesta

@router.post("/iniciar")
async def iniciar_chat(current_user: User = Depends(get_current_user)):
    """Inicia una nueva sesión de chat en Supabase."""
    try:
        print(f"🔍 Iniciando chat para usuario: {current_user.id if current_user else 'None'}")
        
        # VERIFICAR CATEGORÍAS PRIMERO
        print("🔍 Verificando categorías disponibles...")
        try:
            from core.category_manager import CategoryManager
            category_manager = CategoryManager()
            
            # Obtener categorías del usuario
            categorias = category_manager.get_user_categories(current_user.id)
            print(f"📊 Categorías encontradas: {len(categorias)}")
            
            if not categorias:
                raise HTTPException(
                    status_code=400,
                    detail="No tienes categorías creadas. Ve a 'Entrenar' → 'Gestionar Categorías' para crear al menos una categoría."
                )
            
            # Verificar si hay categorías con documentos procesados
            stats = category_manager.get_category_statistics(current_user.id)
            categorias_con_documentos = [s for s in stats['categories'] if s['documentos_procesados'] > 0]
            
            print(f"📋 Categorías con documentos procesados: {len(categorias_con_documentos)}")
            
            if not categorias_con_documentos:
                nombres_categorias = [c['nombre'] for c in categorias]
                raise HTTPException(
                    status_code=400,
                    detail=f"Tienes {len(categorias)} categorías ({', '.join(nombres_categorias)}) pero ninguna tiene documentos procesados. Ve a 'Entrenar' para subir documentos primero."
                )
            
            print(f"✅ Categorías válidas para chat: {[c['nombre'] for c in categorias_con_documentos]}")
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Error verificando categorías: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error verificando categorías: {str(e)}"
            )
        
        # Obtener el perfil del abogado
        print("🔍 Buscando perfil de abogado...")
        try:
            abogado_response = supabase_admin.table('abogados')\
                .select('*')\
                .eq('user_id', current_user.id)\
                .single()\
                .execute()
            
            if not abogado_response.data:
                raise HTTPException(
                    status_code=404, 
                    detail="Perfil de abogado no encontrado. Completa tu perfil primero."
                )
            
            abogado_id = abogado_response.data['id']
            print(f"✅ Perfil encontrado: {abogado_id}")
            
        except Exception as db_error:
            print(f"❌ Error consultando abogado: {str(db_error)}")
            print("🔍 Creando perfil temporal...")
            # Si no existe perfil, crear uno temporal
            temp_abogado = {
                'id': str(uuid.uuid4()),
                'user_id': current_user.id,
                'nombre_completo': current_user.email.split('@')[0],
                'matricula_profesional': 'TEMP-001',
                'email': current_user.email,
                'activo': True
            }
            
            try:
                create_response = supabase_admin.table('abogados')\
                    .insert(temp_abogado)\
                    .execute()
                
                abogado_id = create_response.data[0]['id']
                print(f"✅ Perfil temporal creado para {current_user.email}: {abogado_id}")
                
            except Exception as create_error:
                print(f"❌ Error creando perfil temporal: {str(create_error)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error accediendo al perfil de abogado: {str(create_error)}"
                )
        
        session_id = str(uuid.uuid4())
        print(f"🔍 Generando session_id: {session_id}")
        
        # Crear sesión en Supabase
        print("🔍 Creando sesión en Supabase...")
        datos_sesion = ChatSesionCreate(
            titulo=f"Chat {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            tipo_demanda=None,
            carpeta_id=None,
            cliente_nombre=None,
            cliente_dni=None
        )
        
        sesion = await ChatService.crear_sesion(abogado_id, session_id, datos_sesion)
        print(f"✅ Sesión creada en DB: {sesion.get('id', 'N/A')}")
        
        print(f"✅ Nueva sesión creada: {session_id}")
        
        response_data = {
            "success": True,
            "session_id": session_id,
            "mensaje": session_id,  # El frontend maneja el mensaje de bienvenida
            "sesion_db": sesion
        }
        print(f"🔍 Retornando respuesta: {response_data}")
        
        return response_data
        
    except Exception as e:
        import traceback
        error_detail = str(e) if str(e) else "Error desconocido"
        error_traceback = traceback.format_exc()
        
        print(f"❌ Error iniciando chat: {error_detail}")
        print(f"❌ Traceback completo: {error_traceback}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error iniciando chat: {error_detail} | Type: {type(e).__name__}"
        )

@router.post("/mensaje")
async def procesar_mensaje(
    mensaje: MensajeChat,
    current_user: User = Depends(get_current_user)
):
    """Procesa un mensaje en el chat y guarda en Supabase."""
    try:
        print(f"🔍 Procesando mensaje para usuario: {current_user.id}")
        print(f"🔍 Session ID: {mensaje.session_id}")
        print(f"🔍 Mensaje: {mensaje.mensaje[:100]}...")
        
        # Obtener el perfil del abogado
        print("🔍 Buscando perfil de abogado para mensaje...")
        abogado_response = supabase_admin.table('abogados')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        print(f"✅ Perfil encontrado para mensaje: {abogado_id}")
        
        # Obtener sesión de la base de datos
        print("🔍 Obteniendo sesión de la base de datos...")
        sesion = await obtener_sesion_con_abogado_id(mensaje.session_id, abogado_id)
        print(f"✅ Sesión encontrada: {sesion.get('id', 'N/A')}")
        
        # Guardar mensaje del usuario en Supabase
        print("🔍 Guardando mensaje del usuario...")
        await ChatService.guardar_mensaje(
            sesion_id=sesion['id'],  # UUID de la sesión en DB
            tipo="user",
            mensaje=mensaje.mensaje,
            metadata={"timestamp": datetime.now().isoformat()}
        )
        
        print(f"✅ Mensaje de usuario guardado: {mensaje.mensaje[:50]}...")
        
        # Detectar si es un mensaje de edición con contexto O una modificación global
        es_edicion = (
            mensaje.mensaje.startswith("Modificar el siguiente texto:") or 
            mensaje.mensaje.startswith("[Error editando]") or
            mensaje.mensaje.startswith("GLOBAL:")
        )
        
        if es_edicion:
            # Verificar si es un mensaje de error de edición
            if mensaje.mensaje.startswith("[Error editando]"):
                print("🚨 Detectado mensaje de error de edición - NO procesar como consulta normal")
                # Extraer el error específico del mensaje
                error_msg = mensaje.mensaje.replace("[Error editando]", "").strip()
                
                respuesta_data = {
                    "mensaje": f"❌ **Error en la edición**\n\n{error_msg}\n\n💡 **Sugerencias:**\n- Asegúrate de que existe un documento generado\n- Verifica que el texto a modificar esté en el documento\n- Intenta con una instrucción más específica\n- Si el problema persiste, prueba regenerar el documento",
                    "datos_cliente": sesion.get('cliente_datos', {}),
                    "tipo_demanda": sesion.get('tipo_demanda', ''),
                    "hechos_adicionales": sesion.get('hechos_adicionales', '')
                }
                print(f"❌ Error de edición procesado sin generar nueva demanda")
                
            elif mensaje.mensaje.startswith("GLOBAL:"):
                print("🌍 Detectada solicitud de modificación global...")
                try:
                    instruccion_global = mensaje.mensaje.replace("GLOBAL:", "").strip()
                    
                    from rag.editor_demandas import procesar_edicion_global
                    
                    print(f"🎯 [CHAT] Procesando edición global:")
                    print(f"   💭 Instrucción: '{instruccion_global}'")
                    
                    resultado = procesar_edicion_global(instruccion_global, mensaje.session_id)
                    
                    if resultado.get('exito'):
                        respuesta_data = {
                            "mensaje": f"✅ Modificación global aplicada exitosamente.\n\n{resultado.get('mensaje', '')}",
                            "mostrar_preview": True,
                            "mostrar_descarga": True,
                            "datos_cliente": sesion.get('cliente_datos', {}),
                            "tipo_demanda": sesion.get('tipo_demanda', ''),
                            "hechos_adicionales": sesion.get('hechos_adicionales', '')
                        }
                        print(f"✅ Modificación global procesada exitosamente")
                    else:
                        respuesta_data = {
                            "mensaje": f"❌ No se pudo aplicar la modificación global: {resultado.get('error', 'Error desconocido')}",
                            "datos_cliente": sesion.get('cliente_datos', {}),
                            "tipo_demanda": sesion.get('tipo_demanda', ''),
                            "hechos_adicionales": sesion.get('hechos_adicionales', '')
                        }
                        print(f"❌ Error en modificación global: {resultado.get('error')}")
                        
                except Exception as e:
                    print(f"⚠️ Error procesando modificación global: {e}")
                    respuesta_data = {
                        "mensaje": f"❌ **Error en modificación global**\n\nNo se pudo procesar: {str(e)}\n\n💡 **Sugerencias:**\n- Asegúrate de que existe un documento generado\n- Verifica que el texto a modificar existe en el documento\n- Intenta con una instrucción más específica",
                        "datos_cliente": sesion.get('cliente_datos', {}),
                        "tipo_demanda": sesion.get('tipo_demanda', ''),
                        "hechos_adicionales": sesion.get('hechos_adicionales', '')
                    }
                    
            else:
                print("🔍 Detectada solicitud de edición válida, procesando con EditorDemandas...")
                try:
                    # Extraer el texto a modificar y la instrucción
                    lineas = mensaje.mensaje.split('\n')
                    texto_a_modificar = ""
                    instruccion = ""
                    
                    for i, linea in enumerate(lineas):
                        if linea.startswith("Modificar el siguiente texto:"):
                            # Extraer texto entre comillas
                            import re
                            match = re.search(r'"([^"]*)"', linea)
                            if match:
                                texto_a_modificar = match.group(1)
                        elif linea.startswith("Instrucción:"):
                            instruccion = linea.replace("Instrucción:", "").strip()
                    
                    if texto_a_modificar and instruccion:
                        # Usar EditorDemandas para procesar la edición contextual
                        from rag.editor_demandas import procesar_edicion_contextual
                        
                        print(f"🎯 [CHAT] Procesando edición contextual:")
                        print(f"   📝 Texto: '{texto_a_modificar}'")
                        print(f"   💭 Instrucción: '{instruccion}'")
                        
                        # Usar la función correcta para edición contextual
                        resultado = procesar_edicion_contextual(texto_a_modificar, instruccion, mensaje.session_id)
                        
                        if resultado.get('exito'):
                            respuesta_data = {
                                "mensaje": f"✅ Edición aplicada exitosamente.\n\n{resultado.get('mensaje', '')}",
                                "mostrar_preview": True,  # Mostrar preview actualizado
                                "mostrar_descarga": True,
                                "datos_cliente": sesion.get('cliente_datos', {}),
                                "tipo_demanda": sesion.get('tipo_demanda', ''),
                                "hechos_adicionales": sesion.get('hechos_adicionales', '')
                            }
                            print(f"✅ Edición procesada exitosamente con EditorDemandas")
                        else:
                            respuesta_data = {
                                "mensaje": f"❌ No se pudo aplicar la edición: {resultado.get('error', 'Error desconocido')}",
                                "datos_cliente": sesion.get('cliente_datos', {}),
                                "tipo_demanda": sesion.get('tipo_demanda', ''),
                                "hechos_adicionales": sesion.get('hechos_adicionales', '')
                            }
                            print(f"❌ Error en EditorDemandas: {resultado.get('error')}")
                    else:
                        raise Exception("No se pudo extraer texto a modificar o instrucción")
                        
                except Exception as e:
                    print(f"⚠️ Error procesando edición: {e}")
                    
                    # NO hacer fallback al ChatAgent para ediciones fallidas
                    # Las ediciones NUNCA deben generar nuevas demandas
                    respuesta_data = {
                        "mensaje": f"❌ **Error en la edición**\n\nNo se pudo procesar la edición solicitada: {str(e)}\n\n💡 **Sugerencias:**\n- Asegúrate de que existe un documento generado\n- Verifica que el texto a modificar esté en el documento\n- Intenta con una instrucción más específica",
                        "datos_cliente": sesion.get('cliente_datos', {}),
                        "tipo_demanda": sesion.get('tipo_demanda', ''),
                        "hechos_adicionales": sesion.get('hechos_adicionales', '')
                    }
                    print(f"❌ Error de edición manejado sin generar nueva demanda")
                    
                    # Marcar que NO debe procesar como mensaje normal
                    es_edicion = True  # Mantener como edición fallida, no procesar como nuevo mensaje
        
        if not es_edicion:
            # Procesar mensaje con ChatAgent inteligente o función básica
            print("🔍 Procesando mensaje con IA...")
            
            if CHAT_AGENT_AVAILABLE:
                try:
                    chat_agent = get_chat_agent()
                    if not chat_agent:
                        raise Exception("ChatAgent no pudo inicializarse - verifique OPENAI_API_KEY")
                    
                    # Adaptar estructura de sesión para ChatAgent
                    sesion_adaptada = {
                        'datos_cliente': sesion.get('cliente_datos', {}) if isinstance(sesion.get('cliente_datos'), dict) else {},
                        'tipo_demanda': sesion.get('tipo_demanda', ''),
                        'hechos_adicionales': sesion.get('hechos_adicionales', ''),
                        'notas_abogado': sesion.get('notas_abogado', ''),
                        'estado': 'conversando',
                        'user_id': current_user.id  # NUEVO: Pasar user_id para contexto enriquecido
                    }
                    
                    # Procesar datos JSON si es string
                    if isinstance(sesion.get('cliente_datos'), str):
                        import json
                        try:
                            sesion_adaptada['datos_cliente'] = json.loads(sesion.get('cliente_datos', '{}'))
                        except:
                            sesion_adaptada['datos_cliente'] = {}
                    
                    print(f"🤖 Usando ChatAgent inteligente con OpenAI")
                    respuesta_ia = chat_agent.procesar_mensaje(sesion_adaptada, mensaje.mensaje, mensaje.session_id)
                    
                    # Validar que la respuesta de la IA sea válida
                    if not respuesta_ia or not isinstance(respuesta_ia, dict):
                        raise Exception(f"ChatAgent devolvió respuesta inválida: {type(respuesta_ia)}")
                    
                    # Convertir respuesta del ChatAgent al formato esperado
                    respuesta_data = {
                        "mensaje": respuesta_ia.get("mensaje", "¿En qué puedo ayudarte?"),
                        "opciones": respuesta_ia.get("opciones"),
                        "mostrar_descarga": respuesta_ia.get("demanda_generada", False),
                        "mostrar_preview": respuesta_ia.get("demanda_generada", False),
                        "datos_cliente": sesion_adaptada.get('datos_cliente', {}),
                        "tipo_demanda": sesion_adaptada.get('tipo_demanda', ''),
                        "hechos_adicionales": sesion_adaptada.get('hechos_adicionales', '')
                    }
                    
                    print(f"✅ Respuesta IA generada con OpenAI: ChatAgent procesado exitosamente")
                except Exception as e:
                    print(f"⚠️ Error con ChatAgent, usando fallback: {e}")
                    respuesta_data = procesar_mensaje_inteligente(mensaje.mensaje, sesion)
                    print(f"✅ Respuesta fallback generada: {len(respuesta_data)} items")
            else:
                # Usar función básica si ChatAgent no está disponible
                respuesta_data = procesar_mensaje_inteligente(mensaje.mensaje, sesion)
                print(f"✅ Respuesta básica generada: {len(respuesta_data)} items")
        
        respuesta_bot = respuesta_data.get("mensaje", "¿En qué puedo ayudarte?")
        opciones = respuesta_data.get("opciones")
        print(f"🔍 Respuesta bot: {respuesta_bot[:50]}...")
        
        # Actualizar datos de la sesión si se detectaron cambios
        if respuesta_data.get("datos_cliente") or respuesta_data.get("tipo_demanda") or respuesta_data.get("hechos_adicionales"):
            await actualizar_datos_sesion(
                sesion['id'],
                respuesta_data.get("datos_cliente"),
                respuesta_data.get("tipo_demanda"),
                respuesta_data.get("hechos_adicionales")
            )
        
        # Guardar respuesta del bot en Supabase
        print("🔍 Guardando respuesta del bot...")
        await ChatService.guardar_mensaje(
            sesion_id=sesion['id'],  # UUID de la sesión en DB
            tipo="bot",
            mensaje=respuesta_bot,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "opciones": opciones,
                "mostrar_descarga": respuesta_data.get("mostrar_descarga", False),
                "mostrar_preview": respuesta_data.get("mostrar_preview", False)
            }
        )
        
        print(f"✅ Respuesta del bot guardada: {respuesta_bot[:50]}...")
        
        return {
            "success": True,
            "session_id": mensaje.session_id,
            "respuesta": respuesta_bot,
            "tipo": "bot",
            "timestamp": datetime.now().isoformat(),
            "opciones": opciones,
            "mostrar_descarga": respuesta_data.get("mostrar_descarga", False),
            "mostrar_preview": respuesta_data.get("mostrar_preview", False)
        }
        
    except HTTPException as e:
        print(f"❌ HTTPException en mensaje: {e.detail}")
        raise e
    except Exception as e:
        import traceback
        error_detail = str(e) if str(e) else "Error desconocido"
        error_traceback = traceback.format_exc()
        
        print(f"❌ Error procesando mensaje: {error_detail}")
        print(f"❌ Traceback completo: {error_traceback}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando mensaje: {error_detail} | Type: {type(e).__name__}"
        )

@router.get("/mensajes/{session_id}")
async def obtener_mensajes(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtiene todos los mensajes de una sesión específica."""
    try:
        print(f"🔍 Obteniendo mensajes para session_id: {session_id}")
        
        # Obtener el perfil del abogado
        abogado_response = supabase_admin.table('abogados')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            print(f"❌ Perfil de abogado no encontrado para user_id: {current_user.id}")
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        print(f"✅ Perfil encontrado: {abogado_id}")
        
        # Obtener sesión de la base de datos
        sesion = await obtener_sesion_con_abogado_id(session_id, abogado_id)
        print(f"✅ Sesión encontrada: {sesion.get('id', 'N/A')}")
        
        # Obtener mensajes de la sesión usando el ID interno de la sesión
        print(f"🔍 Buscando mensajes para sesion DB ID: {sesion['id']}")
        mensajes_response = supabase_admin.table('chat_mensajes')\
            .select('*')\
            .eq('sesion_id', sesion['id'])\
            .order('created_at', desc=False)\
            .execute()
        
        mensajes = mensajes_response.data or []
        print(f"✅ Mensajes encontrados: {len(mensajes)}")
        
        # Debug: mostrar algunos mensajes
        for i, msg in enumerate(mensajes[:3]):
            print(f"  {i+1}. {msg.get('tipo', 'N/A')}: {msg.get('mensaje', 'N/A')[:50]}...")
        
        return {
            "success": True,
            "session_id": session_id,
            "mensajes": mensajes,
            "sesion_info": sesion
        }
        
    except HTTPException as e:
        print(f"❌ HTTPException en obtener_mensajes: {e.detail}")
        raise e
    except Exception as e:
        import traceback
        error_detail = str(e) if str(e) else "Error desconocido"
        error_traceback = traceback.format_exc()
        
        print(f"❌ Error obteniendo mensajes: {error_detail}")
        print(f"❌ Traceback completo: {error_traceback}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo mensajes: {error_detail}"
        )

@router.post("/generar-demanda")
async def generar_demanda_endpoint(
    solicitud: SolicitudDemanda,
    current_user: User = Depends(get_current_user)
):
    """Genera una demanda con datos completos del cliente."""
    try:
        # Obtener el perfil del abogado
        abogado_response = supabase_admin.table('abogados')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        
        # Obtener sesión de la base de datos
        sesion = await obtener_sesion_con_abogado_id(solicitud.session_id, abogado_id)

        # Actualizar datos de la sesión en Supabase
        await actualizar_datos_sesion(
            sesion['id'],
            solicitud.datos_cliente.dict(),
            solicitud.tipo_demanda,
            solicitud.hechos_adicionales
        )

        # Generar demanda usando IA si está disponible
        if CHAT_AGENT_AVAILABLE:
            try:
                from rag.qa_agent import generar_demanda
                
                print(f"🔄 Generando demanda con IA para {solicitud.datos_cliente.nombre_completo}")
                
                resultado_demanda = generar_demanda(
                    tipo_demanda=solicitud.tipo_demanda,
                    datos_cliente=solicitud.datos_cliente.dict(),
                    hechos_adicionales=solicitud.hechos_adicionales,
                    notas_abogado=solicitud.notas_abogado,
                    user_id=current_user.id  # NUEVO: Pasar user_id para contexto enriquecido
                )
                
                if resultado_demanda.get("success"):
                    respuesta = f"""✅ **Demanda generada exitosamente con IA**

**Cliente:** {solicitud.datos_cliente.nombre_completo}
**DNI:** {solicitud.datos_cliente.dni}
**Tipo:** {solicitud.tipo_demanda}

🎯 **Demanda creada usando:**
• Base de datos de casos similares
• Jurisprudencia actualizada
• Plantillas profesionales optimizadas

📄 La demanda incluye todas las secciones legales requeridas y está lista para presentar.

**Opciones disponibles:**
🔍 **Vista previa** - Revisar antes de descargar
📥 **Descargar** - Obtener archivo Word
🔄 **Regenerar** - Crear nueva versión"""
                    
                    # Marcar que la demanda fue generada exitosamente
                    mostrar_descarga = True
                    mostrar_preview = True
                else:
                    respuesta = f"""⚠️ **Error generando demanda con IA**

{resultado_demanda.get('error', 'Error desconocido')}

**Datos recibidos:**
• Cliente: {solicitud.datos_cliente.nombre_completo}
• DNI: {solicitud.datos_cliente.dni}
• Tipo: {solicitud.tipo_demanda}

*Reintentando con método básico...*"""
                    mostrar_descarga = False
                    mostrar_preview = False
                    
            except Exception as e:
                print(f"❌ Error generando demanda con IA: {e}")
                respuesta = f"""⚠️ **Sistema de IA temporalmente no disponible**
                
**Datos recibidos correctamente:**
• Cliente: {solicitud.datos_cliente.nombre_completo}
• DNI: {solicitud.datos_cliente.dni}
• Domicilio: {solicitud.datos_cliente.domicilio}
• Tipo: {solicitud.tipo_demanda}

Los datos se han guardado y podrás generar la demanda cuando el sistema esté disponible."""
                mostrar_descarga = False
                mostrar_preview = False
        else:
            # Respuesta básica si no hay IA disponible
            respuesta = f"""✅ **Datos recibidos correctamente:**
            
**Cliente:** {solicitud.datos_cliente.nombre_completo}
**DNI:** {solicitud.datos_cliente.dni}
**Domicilio:** {solicitud.datos_cliente.domicilio}
**Tipo de demanda:** {solicitud.tipo_demanda}

*Nota: Configure OpenAI API para activar generación automática de demandas.*"""
            mostrar_descarga = False
            mostrar_preview = False

        # Guardar mensaje de confirmación en Supabase
        await ChatService.guardar_mensaje(
            sesion_id=sesion['id'],
            tipo="system",
            mensaje=respuesta,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "tipo_accion": "generacion_demanda",
                "datos_cliente": solicitud.datos_cliente.dict()
            }
        )

        return {
            "success": True,
            "respuesta": respuesta,
            "demanda_generada": mostrar_descarga,
            "mostrar_descarga": mostrar_descarga,
            "mostrar_preview": mostrar_preview,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando demanda: {str(e)}"
        )

@router.get("/tipos-demanda")
async def obtener_tipos():
    """Obtiene los tipos de demanda disponibles."""
    tipos = [
        "Despido injustificado",
        "Accidente de trabajo",
        "Divorcio contencioso", 
        "Reclamo de daños y perjuicios",
        "Empleados En Blanco",
        "Empleados En Negro",
        "Demanda Licencia Médica",
        "Demanda Solidaridad Laboral"
    ]
    return {"tipos": tipos}

@router.get("/sesion/{session_id}")
async def obtener_sesion(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtiene información de una sesión específica."""
    try:
        # Obtener el perfil del abogado
        abogado_response = supabase_admin.table('abogados')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        
        # Obtener sesión de la base de datos
        sesion = await obtener_sesion_con_abogado_id(session_id, abogado_id)
        
        return {
            "success": True,
            "session": sesion
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Error obteniendo sesión: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo sesión: {str(e)}"
        )

@router.put("/sesion/{session_id}")
async def actualizar_sesion(
    session_id: str,
    datos: dict,
    current_user: User = Depends(get_current_user)
):
    """Actualiza información de una sesión específica."""
    try:
        # Obtener el perfil del abogado
        abogado_response = supabase_admin.table('abogados')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        
        # Obtener sesión de la base de datos para verificar permisos
        sesion = await obtener_sesion_con_abogado_id(session_id, abogado_id)
        
        # Actualizar sesión
        update_data = {
            **datos,
            "updated_at": datetime.now().isoformat()
        }
        
        response = supabase_admin.table('chat_sesiones')\
            .update(update_data)\
            .eq('id', sesion['id'])\
            .execute()
        
        return {
            "success": True,
            "message": "Sesión actualizada exitosamente",
            "session": response.data[0] if response.data else None
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Error actualizando sesión: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando sesión: {str(e)}"
        )

@router.delete("/sesion/{session_id}")
async def eliminar_sesion(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Elimina una sesión específica y todos sus mensajes."""
    try:
        print(f"🗑️ Eliminando sesión: {session_id}")
        
        # Obtener el perfil del abogado
        abogado_response = supabase_admin.table('abogados')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        
        # Obtener sesión de la base de datos para verificar permisos
        sesion = await obtener_sesion_con_abogado_id(session_id, abogado_id)
        
        # Eliminar mensajes de la sesión primero
        supabase_admin.table('chat_mensajes')\
            .delete()\
            .eq('sesion_id', sesion['id'])\
            .execute()
        
        # Eliminar demandas generadas asociadas
        supabase_admin.table('demandas_generadas')\
            .delete()\
            .eq('sesion_id', sesion['id'])\
            .execute()
        
        # Eliminar la sesión
        supabase_admin.table('chat_sesiones')\
            .delete()\
            .eq('id', sesion['id'])\
            .execute()
        
        print(f"✅ Sesión eliminada exitosamente: {session_id}")
        
        return {
            "success": True,
            "message": "Conversación eliminada exitosamente"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Error eliminando sesión: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando sesión: {str(e)}"
        )

@router.put("/sesion/{session_id}/mover")
async def mover_sesion_a_carpeta(
    session_id: str,
    data: dict,
    current_user: User = Depends(get_current_user)
):
    """Mueve una sesión a otra carpeta."""
    try:
        carpeta_id = data.get('carpeta_id')  # Puede ser None para "sin carpeta"
        print(f"📁 Moviendo sesión {session_id} a carpeta: {carpeta_id or 'Sin carpeta'}")
        
        # Obtener el perfil del abogado
        abogado_response = supabase_admin.table('abogados')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        
        # Verificar que la sesión existe y pertenece al abogado
        sesion = await obtener_sesion_con_abogado_id(session_id, abogado_id)
        
        # Si se especifica una carpeta, verificar que existe y pertenece al abogado
        if carpeta_id:
            carpeta_response = supabase_admin.table('carpetas')\
                .select('id')\
                .eq('id', carpeta_id)\
                .eq('abogado_id', abogado_id)\
                .single()\
                .execute()
            
            if not carpeta_response.data:
                raise HTTPException(status_code=404, detail="Carpeta no encontrada")
        
        # Actualizar la sesión
        response = supabase_admin.table('chat_sesiones')\
            .update({
                'carpeta_id': carpeta_id,
                'updated_at': datetime.now().isoformat()
            })\
            .eq('id', sesion['id'])\
            .execute()
        
        destination = carpeta_id or "Sin carpeta"
        print(f"✅ Sesión movida exitosamente a: {destination}")
        
        return {
            "success": True,
            "message": f"Conversación movida exitosamente",
            "session": response.data[0] if response.data else None
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Error moviendo sesión: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error moviendo sesión: {str(e)}"
        )

@router.delete("/sesiones/bulk")
async def eliminar_sesiones_masivo(
    data: dict,
    current_user: User = Depends(get_current_user)
):
    """Elimina múltiples sesiones de una vez."""
    try:
        session_ids = data.get('session_ids', [])
        if not session_ids:
            raise HTTPException(status_code=400, detail="No se proporcionaron sesiones para eliminar")
        
        print(f"🗑️ Eliminación masiva: {len(session_ids)} sesiones")
        
        # Obtener el perfil del abogado
        abogado_response = supabase_admin.table('abogados')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        
        deleted_count = 0
        errors = []
        
        for session_id in session_ids:
            try:
                # Verificar que la sesión pertenece al abogado
                sesion = await obtener_sesion_con_abogado_id(session_id, abogado_id)
                
                # Eliminar mensajes de la sesión
                supabase_admin.table('chat_mensajes')\
                    .delete()\
                    .eq('sesion_id', sesion['id'])\
                    .execute()
                
                # Eliminar demandas generadas asociadas
                supabase_admin.table('demandas_generadas')\
                    .delete()\
                    .eq('sesion_id', sesion['id'])\
                    .execute()
                
                # Eliminar la sesión
                supabase_admin.table('chat_sesiones')\
                    .delete()\
                    .eq('id', sesion['id'])\
                    .execute()
                
                deleted_count += 1
                print(f"✅ Sesión eliminada: {session_id}")
                
            except Exception as e:
                error_msg = f"Error eliminando {session_id}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
        
        print(f"✅ Eliminación masiva completada: {deleted_count} eliminadas, {len(errors)} errores")
        
        return {
            "success": True,
            "message": f"{deleted_count} conversaciones eliminadas exitosamente",
            "deleted_count": deleted_count,
            "errors": errors
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Error en eliminación masiva: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en eliminación masiva: {str(e)}"
        )

@router.get("/verificar-categorias")
async def verificar_categorias_disponibles(
    current_user: User = Depends(get_current_user)
):
    """Verifica si el usuario tiene categorías disponibles para crear conversaciones."""
    try:
        # Importar CategoryManager y DocumentProcessor
        from core.category_manager import CategoryManager
        from core.document_processor import DocumentProcessor
        
        category_manager = CategoryManager()
        doc_processor = DocumentProcessor()
        
        # Obtener categorías del usuario
        categorias = category_manager.get_user_categories(current_user.id)
        print(f"📊 Categorías encontradas: {len(categorias)}")
        
        if not categorias:
            return {
                "success": True,
                "puede_crear_conversacion": False,
                "total_categorias": 0,
                "categorias_con_documentos": 0,
                "categorias_disponibles": [],
                "mensaje": "No tienes categorías creadas. Ve a 'Entrenar' → 'Gestionar Categorías'",
                "detalle": "Sin categorías"
            }
        
        # Verificar documentos en Supabase Y Qdrant
        categorias_con_documentos = []
        stats = category_manager.get_category_statistics(current_user.id)
        
        # Verificar también colección de Qdrant del usuario (con manejo de errores)
        qdrant_stats = {"total_documents": 0, "collection_exists": False, "error": None}
        try:
            qdrant_stats = doc_processor.get_user_collection_stats(current_user.id)
            print(f"📋 Qdrant collection stats: {qdrant_stats}")
        except Exception as qdrant_error:
            print(f"⚠️ Error obteniendo stats de Qdrant (no crítico): {qdrant_error}")
            qdrant_stats["error"] = str(qdrant_error)
        
        for categoria in categorias:
            categoria_stats = next((s for s in stats['categories'] if s['categoria_id'] == categoria['id']), None)
            
            if categoria_stats and categoria_stats['documentos_procesados'] > 0:
                categorias_con_documentos.append({
                    'id': categoria['id'],
                    'nombre': categoria['nombre'],
                    'documentos_procesados': categoria_stats['documentos_procesados'],
                    'documentos_pendientes': categoria_stats.get('documentos_pendientes', 0)
                })
        
        puede_crear_conversacion = len(categorias_con_documentos) > 0
        
        # Mensaje detallado según la situación
        if puede_crear_conversacion:
            mensaje = f"✅ Listo para crear conversaciones con {len(categorias_con_documentos)} categorías entrenadas"
            detalle = f"Colección Qdrant: {qdrant_stats.get('collection_name', 'N/A')} ({qdrant_stats.get('total_documents', 0)} docs)"
        else:
            nombres_categorias = [c['nombre'] for c in categorias]
            mensaje = f"⚠️ Tienes {len(categorias)} categorías ({', '.join(nombres_categorias)}) pero ninguna tiene documentos procesados"
            detalle = "Ve a 'Entrenar' → 'Subir Documentos' para agregar contenido"
        
        return {
            "success": True,
            "puede_crear_conversacion": puede_crear_conversacion,
            "total_categorias": len(categorias),
            "categorias_con_documentos": len(categorias_con_documentos),
            "categorias_disponibles": categorias_con_documentos,
            "mensaje": mensaje,
            "detalle": detalle,
            "qdrant_stats": qdrant_stats
        }
        
    except Exception as e:
        print(f"❌ Error verificando categorías: {str(e)}")
        return {
            "success": False,
            "puede_crear_conversacion": False,
            "error": str(e),
            "mensaje": "Error verificando categorías disponibles"
        } 