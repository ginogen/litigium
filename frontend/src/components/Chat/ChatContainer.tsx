import { useEffect, useRef, useState, useCallback } from 'react';
import { useChat } from '@/contexts/ChatContext';
import { ChatInput } from './ChatInput';
import { MessageList } from './MessageList';
import { TypingIndicator } from './TypingIndicator';
import { ChatLoadingSkeleton } from '@/components/ui/Skeleton';

export function ChatContainer() {
  const { state } = useChat();
  
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [isUserScrolling] = useState<boolean>(false);
  const [previousMessageCount, setPreviousMessageCount] = useState<number>(0);

  // Función para hacer scroll al final
  const scrollToBottom = useCallback((force = false) => {
    if (!messagesContainerRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    const isAtBottom = scrollTop + clientHeight >= scrollHeight - 150;
    
    if (force || isAtBottom || !isUserScrolling) {
      requestAnimationFrame(() => {
        if (messagesContainerRef.current) {
          messagesContainerRef.current.scrollTo({
            top: messagesContainerRef.current.scrollHeight + 100,
            behavior: 'smooth'
          });
        }
      });
    }
  }, [isUserScrolling]);

  // Auto-scroll cuando hay nuevos mensajes
  useEffect(() => {
    if (!messagesContainerRef.current) return;
    
    const currentMessageCount = state.messages.length;
    
    if (currentMessageCount > previousMessageCount) {
      setTimeout(() => {
        scrollToBottom();
      }, 200);
      
      setPreviousMessageCount(currentMessageCount);
    }
  }, [state.messages.length, previousMessageCount, scrollToBottom]);

  return (
    <div className="flex flex-col h-full relative" style={{ backgroundColor: '#212121' }}>
      {/* Messages area */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto"
        style={{ backgroundColor: '#212121' }}
      >
        <div className="pb-32">
          {state.isLoadingMessages ? (
            <ChatLoadingSkeleton />
          ) : (
            <>
              <MessageList messages={state.messages} />
              {state.isTyping && <TypingIndicator type={state.typingType} />}
            </>
          )}
        </div>
      </div>

      {/* Gradient overlay at bottom - más sutil como ChatGPT */}
      <div 
        className="absolute bottom-0 left-0 w-full h-20 pointer-events-none"
        style={{ 
          background: 'linear-gradient(to top, #212121 0%, transparent 100%)' 
        }}
      />

      {/* Input area */}
      <div className="absolute bottom-0 left-0 w-full" style={{ backgroundColor: '#212121' }}>
        <ChatInput />
      </div>
    </div>
  );
} 