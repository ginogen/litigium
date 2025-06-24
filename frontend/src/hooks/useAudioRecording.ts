import { useState, useRef, useCallback } from 'react';
import { audioAPI } from '@/lib/audio-api';

export interface AudioRecordingState {
  isRecording: boolean;
  isProcessing: boolean;
  duration: number;
  error: string | null;
  permissionDenied: boolean;
}

export interface UseAudioRecordingResult {
  state: AudioRecordingState;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
  cancelRecording: () => void;
  resetState: () => void;
  setProcessing: (processing: boolean) => void;
}

export function useAudioRecording(): UseAudioRecordingResult {
  const [state, setState] = useState<AudioRecordingState>({
    isRecording: false,
    isProcessing: false,
    duration: 0,
    error: null,
    permissionDenied: false,
  });

  const setProcessing = useCallback((processing: boolean) => {
    setState(prev => ({ ...prev, isProcessing: processing }));
  }, []);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const resetState = useCallback(() => {
    setState({
      isRecording: false,
      isProcessing: false,
      duration: 0,
      error: null,
      permissionDenied: false,
    });
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startTimer = useCallback(() => {
    let seconds = 0;
    timerRef.current = setInterval(() => {
      seconds += 1;
      setState(prev => ({ ...prev, duration: seconds }));
    }, 1000);
  }, []);

  const cleanupRecording = useCallback(() => {
    stopTimer();
    
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    mediaRecorderRef.current = null;
    chunksRef.current = [];
  }, [stopTimer]);

  const detectBrowser = useCallback(() => {
    const userAgent = navigator.userAgent.toLowerCase();
    return {
      isSafari: userAgent.includes('safari') && !userAgent.includes('chrome'),
      isChrome: userAgent.includes('chrome') && !userAgent.includes('edg'),
      isFirefox: userAgent.includes('firefox'),
      isEdge: userAgent.includes('edg')
    };
  }, []);

  const getSupportedMimeType = useCallback(() => {
    const browser = detectBrowser();
    
    // Lista de mimeTypes en orden de preferencia según el navegador
    let mimeTypes: string[] = [];
    
    if (browser.isSafari) {
      // Safari: Priorizar MP4/AAC y WAV
      mimeTypes = [
        'audio/mp4;codecs=mp4a.40.2', // AAC en MP4 (preferido en Safari)
        'audio/mp4',                  // MP4 genérico
        'audio/wav',                  // WAV
        'audio/mpeg',                 // MP3
        ''                           // Sin restricción
      ];
    } else if (browser.isChrome || browser.isEdge) {
      // Chrome/Edge: WebM primero, luego MP4
      mimeTypes = [
        'audio/webm;codecs=opus',    // Mejor calidad
        'audio/webm',                 // Fallback WebM
        'audio/mp4;codecs=mp4a.40.2', // AAC en MP4
        'audio/mp4',                  // MP4 genérico
        'audio/wav',                  // WAV
        ''                           // Sin restricción
      ];
    } else if (browser.isFirefox) {
      // Firefox: WebM y Ogg
      mimeTypes = [
        'audio/webm;codecs=opus',    // Mejor calidad
        'audio/webm',                 // Fallback WebM
        'audio/ogg;codecs=opus',     // Ogg Opus
        'audio/wav',                  // WAV
        ''                           // Sin restricción
      ];
    } else {
      // Otros navegadores: orden universal
      mimeTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4;codecs=mp4a.40.2',
        'audio/mp4',
        'audio/wav',
        'audio/ogg;codecs=opus',
        'audio/mpeg',
        ''
      ];
    }

    console.log('🎤 Navegador detectado:', browser);
    console.log('🎤 Probando mimeTypes:', mimeTypes);

    for (const mimeType of mimeTypes) {
      const isSupported = mimeType === '' || MediaRecorder.isTypeSupported(mimeType);
      console.log(`🎤 ${mimeType || 'default'}: ${isSupported ? '✅' : '❌'}`);
      
      if (isSupported) {
        console.log('🎤 Usando mimeType:', mimeType || 'default');
        return mimeType;
      }
    }
    
    console.warn('⚠️ No se encontró mimeType compatible, usando configuración por defecto');
    return '';
  }, [detectBrowser]);

  const startRecording = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, error: null, permissionDenied: false }));

      // Verificar soporte del navegador
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Tu navegador no soporta grabación de audio');
      }

      // Verificar soporte de MediaRecorder
      if (!window.MediaRecorder) {
        throw new Error('Tu navegador no soporta grabación de audio (MediaRecorder no disponible)');
      }

      // Solicitar permisos de micrófono con configuración optimizada
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          // Removemos sampleRate para mayor compatibilidad
          // sampleRate: 16000, // Safari puede tener problemas con esto
        }
      });

      streamRef.current = stream;

      // Obtener mimeType compatible
      const supportedMimeType = getSupportedMimeType();
      
      // Configurar MediaRecorder con mimeType compatible
      const options: MediaRecorderOptions = {};
      if (supportedMimeType) {
        options.mimeType = supportedMimeType;
      }
      
      const mediaRecorder = new MediaRecorder(stream, options);

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstart = () => {
        setState(prev => ({ ...prev, isRecording: true, duration: 0 }));
        startTimer();
      };

      mediaRecorder.onstop = () => {
        setState(prev => ({ ...prev, isRecording: false }));
        stopTimer();
      };

      mediaRecorder.onerror = (event) => {
        console.error('Error en MediaRecorder:', event);
        setState(prev => ({ 
          ...prev, 
          error: 'Error durante la grabación',
          isRecording: false 
        }));
        cleanupRecording();
      };

      // Iniciar grabación
      mediaRecorder.start(250); // Recopilar datos cada 250ms

    } catch (error: any) {
      console.error('Error iniciando grabación:', error);
      
      let errorMessage = 'Error iniciando grabación';
      let permissionDenied = false;
      const browser = detectBrowser();

      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        errorMessage = 'Permiso de micrófono denegado. Por favor, permite el acceso al micrófono.';
        permissionDenied = true;
      } else if (error.name === 'NotFoundError') {
        errorMessage = 'No se encontró ningún micrófono. Verifica que tengas un micrófono conectado.';
      } else if (error.name === 'NotSupportedError') {
        if (browser.isSafari) {
          errorMessage = 'Problema con Safari. Intenta actualizar Safari o usar Chrome/Firefox para mejor compatibilidad.';
        } else {
          errorMessage = 'Tu navegador no soporta grabación de audio. Intenta usar Chrome, Firefox o Safari actualizado.';
        }
      } else if (error.message && error.message.includes('mimeType')) {
        errorMessage = `Formato de audio no compatible. ${browser.isSafari ? 'Safari tiene soporte limitado para algunos formatos.' : 'Intenta usar un navegador más reciente.'}`;
      }

      setState(prev => ({ 
        ...prev, 
        error: errorMessage,
        permissionDenied,
        isRecording: false 
      }));
    }
  }, [startTimer, stopTimer, cleanupRecording, getSupportedMimeType, detectBrowser]);

  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
        resolve(null);
        return;
      }

      const mediaRecorder = mediaRecorderRef.current;

      const handleStop = () => {
        mediaRecorder.removeEventListener('stop', handleStop);
        
        if (chunksRef.current.length > 0) {
          // Usar el mimeType del MediaRecorder o detectar automáticamente
          let mimeType = 'audio/wav'; // Fallback universal
          
          if (mediaRecorder.mimeType) {
            mimeType = mediaRecorder.mimeType;
          } else {
            // Intentar detectar el mejor mimeType disponible
            mimeType = getSupportedMimeType() || 'audio/wav';
          }
          
          const audioBlob = new Blob(chunksRef.current, { 
            type: mimeType 
          });
          
          console.log('🎤 Audio grabado:', {
            size: audioBlob.size,
            type: audioBlob.type,
            chunks: chunksRef.current.length
          });
          
          cleanupRecording();
          resolve(audioBlob);
        } else {
          cleanupRecording();
          resolve(null);
        }
      };

      mediaRecorder.addEventListener('stop', handleStop);
      mediaRecorder.stop();
    });
  }, [cleanupRecording, getSupportedMimeType]);

  const cancelRecording = useCallback(() => {
    cleanupRecording();
    setState(prev => ({
      ...prev,
      isRecording: false,
      duration: 0,
    }));
  }, [cleanupRecording]);

  return {
    state,
    startRecording,
    stopRecording,
    cancelRecording,
    resetState,
    setProcessing,
  };
} 