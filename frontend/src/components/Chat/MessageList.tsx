import React, { memo } from 'react';
import { Message } from '../../contexts/ChatContext';
import { useChat } from '../../contexts/ChatContext';
import { useCanvas } from '../../contexts/CanvasContext';
import { cn } from '@/utils';

interface MessageListProps {
  messages: Message[];
}

// Componente MessageBubble mejorado y minimalista
const MessageBubble = memo(({ message }: { message: Message }) => {
  const { selectOption, state: chatState } = useChat();
  const { open: openCanvas, downloadDocument } = useCanvas();
  
  const isUser = message.type === 'user';
  const isError = message.type === 'error';
  const isFirstBotMessage = !isUser && !isError && message.text && message.text.includes('¿En qué tipo de demanda te puedo ayudar hoy?');

  const handleSelectOption = async (option: string) => {
    await selectOption(option);
  };

  const handleCategorySelect = async (categoryName: string) => {
    await selectOption(`Quiero ayuda con ${categoryName}`);
  };

  const handlePreview = () => {
    if (chatState.sessionId) {
      openCanvas('preview');
    }
  };

  const handleDownload = async () => {
    if (chatState.sessionId) {
      await downloadDocument(chatState.sessionId);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6">
      <div className={cn(
        "flex gap-4",
        isUser ? "justify-end" : "justify-start"
      )}>
        {/* Avatar para mensajes de la IA (izquierda) */}
        {!isUser && (
          <div className="flex-shrink-0">
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium",
              isError ? "bg-red-500" : "bg-emerald-500"
            )}>
              {isError ? "!" : "AI"}
            </div>
          </div>
        )}

        {/* Contenedor del mensaje */}
        <div className={cn(
          "rounded-xl px-4 py-3",
          isUser 
            ? "max-w-[70%] bg-gray-600 text-white" 
            : "w-full bg-transparent text-white"
        )}>
          {/* Texto del mensaje */}
          <div className="whitespace-pre-wrap leading-relaxed">
            {message.text || ''}
          </div>

          {/* Options predefinidas del mensaje */}
          {message.options && message.options.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-4">
              {message.options.map((option, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectOption(option)}
                  className="px-3 py-1.5 text-sm border border-gray-500 text-gray-200 rounded-lg hover:bg-gray-600 transition-colors"
                >
                  {option}
                </button>
              ))}
            </div>
          )}

          {/* Opciones de categorías para el primer mensaje del bot - solo si no es el mensaje inicial */}
          {isFirstBotMessage && !message.options && chatState.categories.length > 0 && 
           !message.text.includes('¡Hola doctor!') && (
            <div className="grid gap-3 mt-4 max-w-md">
              {chatState.categories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => handleCategorySelect(category.nombre)}
                  className="p-3 border border-gray-500 rounded-lg hover:bg-gray-600 cursor-pointer transition-all text-left"
                >
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-8 h-8 rounded-md flex items-center justify-center text-sm font-medium"
                      style={{ backgroundColor: `${category.color}20`, color: category.color }}
                    >
                      {category.icon}
                    </div>
                    <div>
                      <h4 className="font-medium text-sm text-white">{category.nombre}</h4>
                      {category.descripcion && (
                        <p className="text-xs text-gray-300 mt-0.5">{category.descripcion}</p>
                      )}
                    </div>
                  </div>
                </button>
              ))}
              <div className="mt-3 p-3 bg-gray-600 rounded-lg">
                <p className="text-xs text-gray-300 text-center">
                  También puedes escribir directamente tu consulta legal
                </p>
              </div>
            </div>
          )}

          {/* Action buttons */}
          {(message.showDownload || message.showPreview) && (
            <div className="flex gap-3 mt-4">
              {message.showPreview && (
                <button 
                  onClick={handlePreview}
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  🔍 Previsualizar
                </button>
              )}
              {message.showDownload && (
                <button 
                  onClick={handleDownload}
                  className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  📄 Descargar
                </button>
              )}
            </div>
          )}
        </div>

        {/* Avatar para mensajes del usuario (derecha) */}
        {isUser && (
          <div className="flex-shrink-0">
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white text-sm font-medium">
              Tú
            </div>
          </div>
        )}
      </div>

      {/* Timestamp sutil */}
      <div className={cn(
        "text-xs text-gray-400 mt-1 px-2",
        isUser ? "text-right" : "text-left ml-12"
      )}>
        {message.timestamp}
      </div>
    </div>
  );
});

MessageBubble.displayName = 'MessageBubble';

// Componente principal MessageList minimalista
export const MessageList = memo(({ messages }: MessageListProps) => {
  const { selectOption, state, initialize } = useChat();

  if (messages.length === 0) {
    return (
      <div 
        className="h-full w-full flex items-center justify-center" 
        style={{ backgroundColor: '#212121' }}
      >
        <div className="text-center max-w-2xl mx-auto p-8">
          <div className="mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mx-auto mb-4 flex items-center justify-center">
              <span className="text-white text-2xl font-bold">⚖️</span>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">
              LITIGIUM
            </h1>
            <p className="text-lg text-gray-300">
              Tu asistente legal inteligente
            </p>
          </div>
          
          <div className="space-y-6">
            {state.isLoadingCategories ? (
              <div className="flex justify-center py-8">
                <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <div className="text-center">
                <div className="p-4 bg-gray-700 rounded-xl">
                  <p className="text-sm text-gray-300 text-center">
                    💡 Escriba su consulta para comenzar
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full overflow-y-auto" style={{ backgroundColor: '#212121' }}>
      <div className="pb-20">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
      </div>
    </div>
  );
});

MessageList.displayName = 'MessageList'; 