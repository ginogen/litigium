import React from 'react';

interface TypingIndicatorProps {
  message?: string;
  type?: 'writing' | 'generating' | 'editing';
}

export function TypingIndicator({ 
  message, 
  type = 'writing' 
}: TypingIndicatorProps) {
  // Mensajes por defecto según el tipo de operación
  const defaultMessages = {
    writing: 'Escribiendo...',
    generating: 'Estoy generando tu demanda, un momento por favor...',
    editing: 'Estoy aplicando los cambios solicitados...'
  };
  
  const displayMessage = message || defaultMessages[type];
  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6">
      <div className="flex gap-4 justify-start">
        {/* Avatar para mensajes de la IA (izquierda) */}
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center text-white text-sm font-medium">
            AI
          </div>
        </div>

        {/* Contenedor del indicador */}
        <div className="max-w-[70%] rounded-xl px-4 py-3 bg-transparent">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
        </div>
      </div>

      {/* Mensaje de estado */}
      <div className="text-xs text-gray-400 mt-1 px-2 text-left ml-12">
        {displayMessage}
      </div>
    </div>
  );
}

 