import React, { useCallback, useEffect, useState } from 'react';
import { Mic, MicOff, Square, Loader2, Volume2, Play, Pause, RotateCcw } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAudioRecording } from '../../hooks/useAudioRecording';
import { audioAPI } from '../../lib/audio-api';

interface AudioRecorderProps {
  onTranscriptionComplete: (transcription: string) => void;
  onError: (error: string) => void;
  sessionId?: string;
  disabled?: boolean;
}

export function AudioRecorder({ 
  onTranscriptionComplete, 
  onError, 
  sessionId,
  disabled = false 
}: AudioRecorderProps) {
  const { 
    state, 
    startRecording, 
    stopRecording, 
    cancelRecording, 
    resetState,
    setProcessing
  } = useAudioRecording();

  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showRecordingTooltip, setShowRecordingTooltip] = useState(false);

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds}s`;
    }
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs === 0 ? `${mins}m` : `${mins}m ${secs}s`;
  };

  useEffect(() => {
    if (state.isRecording && state.duration > 0) {
      setShowRecordingTooltip(true);
      const timer = setTimeout(() => setShowRecordingTooltip(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [state.isRecording, state.duration]);

  const handleStartRecording = useCallback(async () => {
    resetState();
    setAudioUrl(null);
    await startRecording();
  }, [startRecording, resetState]);

  const handleStopRecording = useCallback(async () => {
    try {
      const audioBlob = await stopRecording();
      
      if (!audioBlob) {
        onError('No se pudo obtener la grabación de audio');
        return;
      }

      // Crear URL para reproducir el audio
      const url = URL.createObjectURL(audioBlob);
      setAudioUrl(url);

      // Activar estado de procesamiento
      setProcessing(true);

      // Procesar audio con Whisper
      const result = await audioAPI.transcribirAudio(audioBlob, sessionId);
      
      if (result.success && result.transcription) {
        onTranscriptionComplete(result.transcription);
      } else {
        onError(result.error || 'Error procesando el audio');
      }
    } catch (error) {
      console.error('Error processing audio:', error);
      onError('Error procesando el audio');
    } finally {
      setProcessing(false);
    }
  }, [stopRecording, onTranscriptionComplete, onError, sessionId, setProcessing]);

  const handleCancelRecording = useCallback(() => {
    cancelRecording();
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setIsPlaying(false);
  }, [cancelRecording, audioUrl]);

  const handlePlayAudio = useCallback(() => {
    if (!audioUrl) return;
    
    const audio = new Audio(audioUrl);
    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      setIsPlaying(true);
      audio.play();
      audio.onended = () => setIsPlaying(false);
    }
  }, [audioUrl, isPlaying]);

  // Si hay error de permisos, mostrar mensaje elegante
  if (state.permissionDenied) {
    return (
      <div className="animate-in slide-in-from-bottom-2 duration-300">
        <div className="bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/20 rounded-2xl p-4 max-w-sm backdrop-blur-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-amber-500/20 rounded-full flex items-center justify-center">
              <MicOff className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <div className="text-amber-300 font-medium text-sm">Micrófono requerido</div>
              <div className="text-amber-400/80 text-xs">Necesitamos acceso para grabar audio</div>
            </div>
          </div>
          <button
            onClick={handleStartRecording}
            className="w-full py-2 px-4 bg-amber-500 hover:bg-amber-600 text-white rounded-xl transition-all duration-200 text-sm font-medium"
          >
            Permitir acceso
          </button>
        </div>
      </div>
    );
  }

  // Si hay error general
  if (state.error) {
    const isSafari = navigator.userAgent.toLowerCase().includes('safari') && !navigator.userAgent.toLowerCase().includes('chrome');
    
    return (
      <div className="animate-in slide-in-from-bottom-2 duration-300">
        <div className="bg-gradient-to-r from-red-500/10 to-rose-500/10 border border-red-500/20 rounded-2xl p-4 max-w-sm backdrop-blur-sm">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-red-500/20 rounded-full flex items-center justify-center">
              <MicOff className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <div className="text-red-300 font-medium text-sm">Error de grabación</div>
              <div className="text-red-400/80 text-xs">{state.error}</div>
            </div>
          </div>
          
          {/* Información adicional para Safari */}
          {isSafari && (
            <div className="mb-3 p-3 bg-red-500/10 rounded-xl">
              <div className="text-xs text-red-300 flex items-center gap-2">
                <span>🦾</span>
                <span><strong>Safari:</strong> Asegúrate de usar la versión más reciente</span>
              </div>
            </div>
          )}
          
          <div className="flex gap-2">
            <button
              onClick={resetState}
              className="flex-1 py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-xl transition-all duration-200 text-sm"
            >
              Cerrar
            </button>
            <button
              onClick={handleStartRecording}
              className="flex-1 py-2 px-4 bg-red-500 hover:bg-red-600 text-white rounded-xl transition-all duration-200 text-sm"
            >
              Reintentar
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Estado de grabación activa - UI mejorada estilo ChatGPT
  if (state.isRecording) {
    return (
      <div className="animate-in slide-in-from-bottom-2 duration-300">
        <div className="bg-gradient-to-r from-red-500/20 to-pink-500/20 border border-red-500/30 rounded-2xl p-5 max-w-sm backdrop-blur-sm relative overflow-hidden">
          {/* Efecto de ondas de fondo */}
          <div className="absolute inset-0 bg-gradient-to-r from-red-500/5 to-pink-500/5 animate-pulse" />
          
          <div className="relative z-10">
            {/* Header con estado y tiempo */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className="w-10 h-10 bg-red-500/30 rounded-full flex items-center justify-center">
                    <Mic className="w-5 h-5 text-red-300" />
                  </div>
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-400 rounded-full animate-pulse border-2 border-white/20" />
                </div>
                <div>
                  <div className="text-red-200 font-semibold text-sm">Grabando...</div>
                  <div className="text-red-300/80 text-xs">Habla claramente</div>
                </div>
              </div>
              <div className="text-red-200 font-mono text-lg font-bold">
                {formatDuration(state.duration)}
              </div>
            </div>
            
            {/* Visualizador de audio mejorado */}
            <div className="flex items-center justify-center mb-4 py-3">
              <div className="flex items-end gap-1 h-12">
                {Array.from({ length: 20 }).map((_, i) => (
                  <div
                    key={i}
                    className="w-1.5 bg-gradient-to-t from-red-400 to-pink-300 rounded-full transition-all duration-100"
                    style={{
                      height: `${Math.random() * 40 + 10}px`,
                      animationDelay: `${i * 0.05}s`,
                      opacity: 0.7 + Math.random() * 0.3
                    }}
                  />
                ))}
              </div>
            </div>

            {/* Tooltip de instrucciones */}
            {showRecordingTooltip && state.duration < 3 && (
              <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 bg-black/80 text-white text-xs px-3 py-1 rounded-lg">
                Presiona Enviar cuando termines
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-2 h-2 bg-black/80 rotate-45 -translate-y-1" />
              </div>
            )}

            {/* Botones de acción */}
            <div className="flex gap-3">
              <button
                onClick={handleStopRecording}
                className="flex-1 flex items-center justify-center gap-2 py-3 px-4 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-xl transition-all duration-200 font-medium text-sm shadow-lg"
              >
                <Square className="w-4 h-4" />
                Enviar
              </button>
              <button
                onClick={handleCancelRecording}
                className="px-4 py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl transition-all duration-200 text-sm border border-white/10"
                title="Cancelar grabación"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>

            {/* Indicador de tiempo de grabación */}
            <div className="mt-3 text-center">
              <div className="text-red-300/60 text-xs">
                {state.duration < 5 ? "Continúa hablando..." : 
                 state.duration < 30 ? `${formatTime(state.duration)} grabados` :
                 state.duration < 60 ? "¡Perfecto! Ya tienes suficiente contenido" :
                 "Considera enviar para mejor procesamiento"}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Estado de procesamiento mejorado
  if (state.isProcessing) {
    return (
      <div className="animate-in slide-in-from-bottom-2 duration-300">
        <div className="bg-gradient-to-r from-blue-500/20 to-indigo-500/20 border border-blue-500/30 rounded-2xl p-5 max-w-sm backdrop-blur-sm">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-12 h-12 bg-blue-500/30 rounded-full flex items-center justify-center">
                <Loader2 className="w-6 h-6 text-blue-300 animate-spin" />
              </div>
              <div className="absolute inset-0 rounded-full border-2 border-blue-400/30 animate-ping" />
            </div>
            <div>
              <div className="text-blue-200 font-semibold text-sm mb-1">Procesando audio...</div>
              <div className="text-blue-300/80 text-xs">Transcribiendo con Whisper AI</div>
              <div className="text-blue-400/60 text-xs mt-1">Esto puede tomar unos segundos</div>
            </div>
          </div>
          
          {/* Preview del audio grabado si está disponible */}
          {audioUrl && (
            <div className="mt-4 pt-4 border-t border-blue-500/20">
              <div className="flex items-center gap-3">
                <button
                  onClick={handlePlayAudio}
                  className="w-8 h-8 bg-blue-500/30 hover:bg-blue-500/50 rounded-full flex items-center justify-center transition-all duration-200"
                >
                  {isPlaying ? (
                    <Pause className="w-4 h-4 text-blue-300" />
                  ) : (
                    <Play className="w-4 h-4 text-blue-300 ml-0.5" />
                  )}
                </button>
                <div className="text-blue-300/80 text-xs">
                  Vista previa del audio grabado
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Botón para iniciar grabación - Mejorado
  return (
    <div className="relative group">
      <button
        onClick={handleStartRecording}
        disabled={disabled}
        className={cn(
          "relative p-3 rounded-2xl transition-all duration-300 transform",
          disabled
            ? "bg-gray-600/50 text-gray-400 cursor-not-allowed"
            : "bg-gradient-to-r from-blue-500 to-indigo-500 text-white hover:from-blue-600 hover:to-indigo-600 shadow-lg hover:shadow-xl hover:scale-105 active:scale-95"
        )}
        title="Grabar mensaje de voz"
      >
        {/* Efecto de ondas cuando está habilitado */}
        {!disabled && (
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-blue-400/20 to-indigo-400/20 animate-pulse" />
        )}
        
        <Mic className="w-5 h-5 relative z-10" />
        
        {/* Tooltip mejorado */}
        <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 bg-black/90 text-white text-xs px-3 py-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap">
          Grabar mensaje de voz
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-2 h-2 bg-black/90 rotate-45 -translate-y-1" />
        </div>
      </button>
    </div>
  );
} 