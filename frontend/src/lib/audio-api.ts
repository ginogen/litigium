import { getAuthHeaders } from './auth-api';

export interface TranscripcionResponse {
  exito: boolean;
  texto_transcrito: string;
  duracion_audio: number;
  idioma_detectado: string;
  confianza: number;
  timestamp: string;
}

export interface AudioProcessingResult {
  success: boolean;
  transcription?: string;
  error?: string;
  duration?: number;
}

class AudioAPI {

  async transcribirAudio(audioBlob: Blob, sessionId?: string): Promise<AudioProcessingResult> {
    try {
      console.log('🎤 Iniciando transcripción:', {
        audioSize: audioBlob.size,
        audioType: audioBlob.type,
        sessionId: sessionId || 'sin sesión'
      });

      const formData = new FormData();
      formData.append('archivo_audio', audioBlob, 'audio.webm');
      
      if (sessionId) {
        formData.append('session_id', sessionId);
        console.log('📎 Enviando con session_id:', sessionId);
      } else {
        console.log('📎 Enviando sin session_id');
      }

      const headers = await getAuthHeaders();
      delete headers['Content-Type']; // Let browser set Content-Type for FormData

      const response = await fetch('/api/audio/transcribir', {
        method: 'POST',
        headers,
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Error del servidor' }));
        throw new Error(errorData.detail || `Error del servidor: ${response.status}`);
      }

      const data: TranscripcionResponse = await response.json();
      console.log('✅ Respuesta del servidor:', data);
      
      if (data.exito) {
        console.log('🎯 Transcripción exitosa:', data.texto_transcrito);
        return {
          success: true,
          transcription: data.texto_transcrito,
          duration: data.duracion_audio
        };
      } else {
        console.warn('⚠️ Transcripción falló');
        return {
          success: false,
          error: 'Error en la transcripción'
        };
      }
    } catch (error) {
      console.error('Error transcribiendo audio:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Error desconocido'
      };
    }
  }

  async obtenerFormatosSoportados(): Promise<string[]> {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch('/api/audio/formatos-soportados', {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`Error del servidor: ${response.status}`);
      }

      const data = await response.json();
      return data.formatos || ['audio/webm', 'audio/mp3', 'audio/wav'];
    } catch (error) {
      console.error('Error obteniendo formatos soportados:', error);
      return ['audio/webm', 'audio/mp3', 'audio/wav'];
    }
  }

  // Validación del lado cliente
  isValidAudioFile(file: File): { valid: boolean; error?: string } {
    // Verificar tipo MIME
    if (!file.type.startsWith('audio/')) {
      return { valid: false, error: 'El archivo debe ser de audio' };
    }

    // Verificar tamaño (25MB máximo)
    const maxSize = 25 * 1024 * 1024;
    if (file.size > maxSize) {
      return { valid: false, error: 'El archivo es demasiado grande (máximo 25MB)' };
    }

    return { valid: true };
  }
}

export const audioAPI = new AudioAPI(); 