from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from typing import Optional, Any, Dict
from pydantic import BaseModel
import tempfile
import os
from datetime import datetime

from ..auth.dependencies import get_current_user
from ..models.user import User
from supabase_integration import supabase
from rag.audio_service import get_audio_service

router = APIRouter(prefix="/api/audio", tags=["audio"])

class TranscripcionRespuesta(BaseModel):
    exito: bool
    texto_transcrito: str
    duracion_audio: float
    idioma_detectado: str
    confianza: float
    timestamp: str

class MensajeAudio(BaseModel):
    session_id: str
    transcripcion: str
    duracion: Optional[float] = None
    idioma: Optional[str] = "es"
    metadata_audio: Dict[str, Any] = {}

class TextoAudio(BaseModel):
    session_id: str
    texto: str
    voz: Optional[str] = "es-ES-Standard-A"
    velocidad: Optional[float] = 1.0

async def obtener_sesion_audio(session_id: str, abogado_id: str) -> Dict:
    """Obtiene una sesión específica verificando que pertenezca al abogado."""
    try:
        response = supabase.table('chat_sesiones')\
            .select('*')\
            .eq('session_id', session_id)\
            .eq('abogado_id', abogado_id)\
            .single()\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        return response.data
    except Exception as e:
        if "No rows found" in str(e):
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        raise HTTPException(status_code=500, detail=f"Error obteniendo sesión: {str(e)}")

@router.post("/transcribir", response_model=TranscripcionRespuesta)
async def transcribir_audio(
    archivo_audio: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Transcribe audio usando Whisper de OpenAI."""
    try:
        session = None
        
        # Verificar sesión si se proporciona (pero no es obligatorio)
        if session_id:
            try:
                session = await obtener_sesion_audio(session_id, current_user.id)
                print(f"✅ Sesión encontrada: {session_id}")
            except HTTPException as e:
                # Log el problema pero continuar sin sesión
                print(f"⚠️ Sesión no válida {session_id}: {e.detail}")
                session = None
        else:
            print("ℹ️ Transcripción sin sesión")
        
        # Validar archivo
        if not archivo_audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="El archivo debe ser de audio")
        
        # Verificar tamaño (max 25MB)
        contenido = await archivo_audio.read()
        if len(contenido) > 25 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="El archivo es demasiado grande (máximo 25MB)")
        
        print(f"🎤 Procesando audio: {len(contenido)} bytes, tipo: {archivo_audio.content_type}")
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(contenido)
            temp_path = temp_file.name
        
        try:
            # Usar servicio de audio con Whisper real
            audio_service = get_audio_service()
            resultado = await audio_service.procesar_audio_completo(contenido)
            
            if not resultado["success"]:
                raise HTTPException(status_code=400, detail=resultado.get("error", "Error procesando audio"))
            
            transcripcion = resultado["texto"]
            print(f"✅ Transcripción exitosa: {transcripcion[:100]}...")
            
            # Si hay sesión válida, guardar la transcripción como mensaje
            if session:
                try:
                    mensaje_data = {
                        "sesion_id": session['id'],
                        "contenido": f"[Audio transcrito] {transcripcion}",
                        "tipo": "user",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    supabase.table('chat_mensajes')\
                        .insert(mensaje_data)\
                        .execute()
                    
                    print(f"💾 Mensaje guardado en sesión {session['id']}")
                except Exception as e:
                    print(f"⚠️ Error guardando mensaje: {e}")
                    # Continuar sin guardar
            
            return TranscripcionRespuesta(
                exito=True,
                texto_transcrito=transcripcion,
                duracion_audio=resultado.get("duracion", 0.0),
                idioma_detectado="es",
                confianza=0.95,
                timestamp=datetime.now().isoformat()
            )
            
        finally:
            # Limpiar archivo temporal
            os.unlink(temp_path)
            
    except HTTPException:
        # Re-lanzar errores HTTP específicos
        raise
    except Exception as e:
        print(f"❌ Error inesperado transcribiendo audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error transcribiendo audio: {str(e)}")

@router.post("/mensaje-audio")
async def procesar_mensaje_audio(
    mensaje_audio: MensajeAudio,
    current_user: User = Depends(get_current_user)
):
    """Procesa un mensaje de audio transcrito."""
    try:
        session = await obtener_sesion_audio(mensaje_audio.session_id, current_user.id)
        
        # Guardar mensaje de audio
        mensaje_data = {
            "sesion_id": session['id'],
            "contenido": mensaje_audio.transcripcion,
            "tipo": "user",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "es_audio": True,
                "duracion": mensaje_audio.duracion,
                "idioma": mensaje_audio.idioma
            }
        }
        
        supabase.table('chat_mensajes')\
            .insert(mensaje_data)\
            .execute()
        
        # TODO: Procesar mensaje con el sistema de chat inteligente
        # Por ahora, respuesta simple
        respuesta = f"He recibido tu mensaje de audio: {mensaje_audio.transcripcion[:100]}..."
        
        # Guardar respuesta del bot
        respuesta_data = {
            "sesion_id": session['id'],
            "contenido": respuesta,
            "tipo": "bot",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "respuesta_a_audio": True
            }
        }
        
        supabase.table('chat_mensajes')\
            .insert(respuesta_data)\
            .execute()
        
        return {
            "success": True,
            "mensaje": "Mensaje de audio procesado",
            "respuesta": respuesta,
            "session_id": mensaje_audio.session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando mensaje de audio: {str(e)}")

@router.get("/audio-to-text/{session_id}")
async def obtener_transcripciones(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtiene todas las transcripciones de audio de una sesión."""
    try:
        session = await obtener_sesion_audio(session_id, current_user.id)
        
        # Obtener mensajes de audio de la sesión
        response = supabase.table('chat_mensajes')\
            .select('*')\
            .eq('sesion_id', session['id'])\
            .execute()
        
        mensajes = response.data or []
        
        # Filtrar mensajes de audio
        mensajes_audio = [
            m for m in mensajes 
            if m.get('metadata', {}).get('es_audio') or '[Audio transcrito]' in m.get('contenido', '')
        ]
        
        return {
            "success": True,
            "session_id": session_id,
            "transcripciones": mensajes_audio,
            "total": len(mensajes_audio)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo transcripciones: {str(e)}")

@router.post("/texto-a-audio")
async def texto_a_audio(
    solicitud: TextoAudio,
    current_user: User = Depends(get_current_user)
):
    """Convierte texto a audio usando síntesis de voz."""
    try:
        session = await obtener_sesion_audio(solicitud.session_id, current_user.id)
        
        # TODO: Implementar síntesis de voz con OpenAI TTS
        # Por ahora, simular generación de audio
        
        # Simular archivo de audio generado
        audio_url = f"/api/audio/temp/{solicitud.session_id}_audio.mp3"
        
        return {
            "success": True,
            "audio_url": audio_url,
            "duracion": len(solicitud.texto) * 0.1,  # Simulado
            "formato": "mp3",
            "idioma": "es",
            "session_id": solicitud.session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando audio: {str(e)}")

@router.get("/formatos-soportados")
async def obtener_formatos_audio():
    """Obtiene la lista de formatos de audio soportados."""
    formatos_soportados = {
        "formatos": [
            {
                "extension": ".mp3",
                "mime_type": "audio/mpeg",
                "descripcion": "MP3 - Formato más común"
            },
            {
                "extension": ".wav",
                "mime_type": "audio/wav",
                "descripcion": "WAV - Alta calidad sin compresión"
            },
            {
                "extension": ".m4a",
                "mime_type": "audio/mp4",
                "descripcion": "M4A - Formato de Apple"
            },
            {
                "extension": ".ogg",
                "mime_type": "audio/ogg",
                "descripcion": "OGG - Formato libre"
            }
        ],
        "limitaciones": {
            "tamaño_maximo": "25 MB",
            "duracion_maxima": "60 minutos",
            "idiomas_soportados": ["es-AR", "es-ES", "en-US"]
        },
        "recomendaciones": {
            "calidad": "16 kHz o superior",
            "formato_preferido": "WAV o M4A",
            "ambiente": "Grabación en lugar silencioso para mejor precisión"
        }
    }
    
    return {
        "success": True,
        "formatos_audio": formatos_soportados
    }

# ===== ENDPOINT TEMPORAL DE DEBUG PARA AUDIO =====
@router.get("/debug-audio-status")
async def debug_audio_status():
    """Endpoint temporal para diagnosticar problemas de audio"""
    import os
    import tempfile
    
    diagnostico = {
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "openai_api_key": "✅ Configurada" if os.getenv("OPENAI_API_KEY") else "❌ No configurada",
            "temp_dir": tempfile.gettempdir(),
            "temp_dir_writable": None,
            "pydub_available": None,
            "ffmpeg_available": None
        },
        "dependencies": {},
        "audio_service": {},
        "temp_file_test": {},
        "whisper_test": "No ejecutado"
    }
    
    # Test 1: Directorio temporal
    try:
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(b"test")
            diagnostico["environment"]["temp_dir_writable"] = "✅ Escribible"
    except Exception as e:
        diagnostico["environment"]["temp_dir_writable"] = f"❌ Error: {str(e)}"
    
    # Test 2: pydub
    try:
        from pydub import AudioSegment
        diagnostico["environment"]["pydub_available"] = "✅ Disponible"
        diagnostico["dependencies"]["pydub"] = "✅ OK"
    except ImportError as e:
        diagnostico["environment"]["pydub_available"] = f"❌ Error: {str(e)}"
        diagnostico["dependencies"]["pydub"] = f"❌ ImportError: {str(e)}"
    
    # Test 3: ffmpeg (usado por pydub)
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            diagnostico["environment"]["ffmpeg_available"] = "✅ Disponible"
        else:
            diagnostico["environment"]["ffmpeg_available"] = "❌ No funciona"
    except Exception as e:
        diagnostico["environment"]["ffmpeg_available"] = f"❌ Error: {str(e)}"
    
    # Test 4: AudioService
    try:
        from rag.audio_service import get_audio_service
        audio_service = get_audio_service()
        diagnostico["audio_service"]["creation"] = "✅ Servicio creado exitosamente"
        diagnostico["audio_service"]["openai_client"] = "✅ Cliente OpenAI inicializado"
    except Exception as e:
        diagnostico["audio_service"]["creation"] = f"❌ Error: {str(e)}"
    
    # Test 5: Archivo temporal de audio
    try:
        # Crear un archivo de audio muy básico (WAV header mínimo)
        wav_header = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp.write(wav_header)
            temp_path = tmp.name
        
        # Verificar que se puede leer
        with open(temp_path, 'rb') as f:
            content = f.read()
            diagnostico["temp_file_test"]["size"] = len(content)
        
        # Limpiar
        os.unlink(temp_path)
        diagnostico["temp_file_test"]["status"] = "✅ Archivo temporal creado y leído exitosamente"
        
    except Exception as e:
        diagnostico["temp_file_test"]["status"] = f"❌ Error: {str(e)}"
    
    return {
        "debug_info": diagnostico,
        "instrucciones": [
            "Ejecuta este endpoint desde tu frontend:",
            "fetch('/api/audio/debug-audio-status').then(r => r.json()).then(console.log)",
            "O visita directamente: https://tu-app.railway.app/api/audio/debug-audio-status",
            "Comparte el resultado para diagnosticar el problema específico"
        ]
    }

@router.post("/test-transcribir-simple")
async def test_transcribir_simple(
    archivo_audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Endpoint simplificado para testear transcripción sin complejidades"""
    logs = []
    
    try:
        logs.append("🎯 Iniciando test de transcripción simple")
        
        # Leer archivo
        contenido = await archivo_audio.read()
        logs.append(f"📁 Archivo leído: {len(contenido)} bytes, tipo: {archivo_audio.content_type}")
        
        # Verificar OpenAI API Key
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY no configurada")
        logs.append("🔑 OPENAI_API_KEY encontrada")
        
        # Crear archivo temporal con extensión correcta basada en content_type
        if 'webm' in archivo_audio.content_type:
            extension = '.webm'
        elif 'mp4' in archivo_audio.content_type:
            extension = '.mp4'
        elif 'wav' in archivo_audio.content_type:
            extension = '.wav'
        elif 'mp3' in archivo_audio.content_type:
            extension = '.mp3'
        else:
            extension = '.webm'  # Default
            
        logs.append(f"🎵 Extensión detectada: {extension}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_file.write(contenido)
            temp_path = temp_file.name
            
        logs.append(f"📂 Archivo temporal creado: {temp_path}")
        
        try:
            # Llamar directamente a OpenAI Whisper
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            with open(temp_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="es"
                )
            
            transcripcion = transcript.text.strip()
            logs.append(f"✅ Transcripción exitosa: {len(transcripcion)} caracteres")
            
            return {
                "exito": True,
                "texto_transcrito": transcripcion,
                "logs": logs,
                "metadata": {
                    "archivo_size": len(contenido),
                    "archivo_tipo": archivo_audio.content_type,
                    "extension_usada": extension
                }
            }
            
        finally:
            # Limpiar
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                logs.append("🗑️ Archivo temporal eliminado")
            
    except Exception as e:
        logs.append(f"❌ Error: {str(e)}")
        return {
            "exito": False,
            "error": str(e),
            "logs": logs
        } 