"""
Servicio de procesamiento de audio usando Whisper AI
"""

import os
import tempfile
import aiofiles
from typing import Optional
import logging
from openai import OpenAI
from pydub import AudioSegment
import io

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        
    async def transcribir_audio(self, audio_data: bytes, formato: str = "webm") -> Optional[str]:
        """
        Transcribe audio usando Whisper AI de OpenAI
        
        Args:
            audio_data: Datos binarios del audio
            formato: Formato del audio (webm, mp3, wav, etc.)
            
        Returns:
            Texto transcrito o None si hay error
        """
        try:
            # Primero intentar convertir el audio a un formato óptimo
            audio_optimizado = await self.convertir_audio_format(audio_data, formato, "mp3")
            if audio_optimizado:
                audio_data = audio_optimizado
                formato = "mp3"
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(suffix=f".{formato}", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Procesar con Whisper
                with open(temp_file_path, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="es",  # Español
                        prompt="Este es un mensaje de voz de un abogado discutiendo casos legales, demandas laborales, y asuntos jurídicos en Argentina."
                    )
                
                texto = transcript.text.strip()
                logger.info(f"Audio transcrito exitosamente: {len(texto)} caracteres")
                return texto
                
            finally:
                # Limpiar archivo temporal
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error transcribiendo audio: {str(e)}")
            return None
    
    async def convertir_audio_format(self, audio_data: bytes, formato_origen: str, formato_destino: str = "wav") -> Optional[bytes]:
        """
        Convierte audio de un formato a otro usando pydub
        
        Args:
            audio_data: Datos binarios del audio original
            formato_origen: Formato del audio original
            formato_destino: Formato deseado
            
        Returns:
            Datos binarios del audio convertido o None si hay error
        """
        try:
            # Cargar audio desde bytes
            audio_io = io.BytesIO(audio_data)
            audio = AudioSegment.from_file(audio_io, format=formato_origen)
            
            # Optimizar para transcripción (mono, 16kHz)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            
            # Exportar al formato destino
            output_io = io.BytesIO()
            audio.export(output_io, format=formato_destino)
            
            return output_io.getvalue()
            
        except Exception as e:
            logger.error(f"Error convirtiendo audio: {str(e)}")
            return None
    
    def validar_audio(self, audio_data: bytes, max_size_mb: int = 25) -> bool:
        """
        Valida que el archivo de audio sea válido
        
        Args:
            audio_data: Datos binarios del audio
            max_size_mb: Tamaño máximo en MB
            
        Returns:
            True si es válido, False si no
        """
        try:
            # Verificar tamaño
            size_mb = len(audio_data) / (1024 * 1024)
            if size_mb > max_size_mb:
                logger.warning(f"Audio demasiado grande: {size_mb:.2f}MB")
                return False
            
            # Verificar que sea un audio válido
            audio_io = io.BytesIO(audio_data)
            audio = AudioSegment.from_file(audio_io)
            
            # Verificar duración (máximo 10 minutos)
            duration_minutes = len(audio) / (1000 * 60)
            if duration_minutes > 10:
                logger.warning(f"Audio demasiado largo: {duration_minutes:.2f} minutos")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validando audio: {str(e)}")
            return False
    
    def detectar_formato_audio(self, audio_data: bytes) -> str:
        """
        Detecta el formato del audio basándose en los magic bytes
        
        Args:
            audio_data: Datos binarios del audio
            
        Returns:
            Formato detectado como string
        """
        # Magic bytes para diferentes formatos
        if audio_data.startswith(b'\x1a\x45\xdf\xa3'):
            return "webm"
        elif audio_data.startswith(b'ID3') or audio_data.startswith(b'\xff\xfb'):
            return "mp3"
        elif audio_data.startswith(b'RIFF') and b'WAVE' in audio_data[:12]:
            return "wav"
        elif audio_data.startswith(b'\x00\x00\x00\x20ftypM4A'):
            return "m4a"
        elif audio_data.startswith(b'OggS'):
            return "ogg"
        else:
            return "webm"  # Default para grabaciones del navegador

    async def procesar_audio_completo(self, audio_data: bytes, formato_original: Optional[str] = None) -> dict:
        """
        Procesa un archivo de audio completo: validación, conversión y transcripción
        
        Args:
            audio_data: Datos binarios del audio
            formato_original: Formato original del audio (opcional, se autodetecta)
            
        Returns:
            Diccionario con resultado del procesamiento
        """
        try:
            # Detectar formato si no se proporciona
            if not formato_original:
                formato_original = self.detectar_formato_audio(audio_data)
            
            # Validar el audio
            if not self.validar_audio(audio_data):
                return {
                    "success": False,
                    "error": "Audio inválido o demasiado grande",
                    "codigo_error": "AUDIO_INVALID"
                }
            
            # Transcribir
            texto_transcrito = await self.transcribir_audio(audio_data, formato_original)
            
            if texto_transcrito:
                return {
                    "success": True,
                    "texto": texto_transcrito,
                    "formato_detectado": formato_original,
                    "tamaño_audio": len(audio_data),
                    "mensaje": "Audio procesado exitosamente"
                }
            else:
                return {
                    "success": False,
                    "error": "No se pudo transcribir el audio",
                    "codigo_error": "TRANSCRIPTION_FAILED"
                }
                
        except Exception as e:
            logger.error(f"Error procesando audio: {str(e)}")
            return {
                "success": False,
                "error": f"Error procesando audio: {str(e)}",
                "codigo_error": "PROCESSING_ERROR"
            }

# Instancia global del servicio de audio
_audio_service = None

def get_audio_service() -> AudioService:
    """Obtiene la instancia del servicio de audio"""
    global _audio_service
    if _audio_service is None:
        # Obtener API key directamente de variables de entorno primero
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        
        # Si no está en variables de entorno, intentar desde configuraciones
        if not api_key:
            try:
                # Intentar importar desde config.py de la raíz
                from config import OpenAIConfig
                api_key = OpenAIConfig.API_KEY
            except (ImportError, AttributeError):
                try:
                    # Intentar importar desde backend/config.py
                    from backend.config import settings
                    api_key = settings.OPENAI_API_KEY
                except (ImportError, AttributeError):
                    pass
        
        if not api_key:
            raise ValueError("No se pudo obtener OPENAI_API_KEY desde ninguna fuente de configuración. Verifica que esté configurada en las variables de entorno.")
        
        _audio_service = AudioService(api_key)
    return _audio_service 