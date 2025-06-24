import React, { useState, memo } from 'react';
import { ParagraphData } from '@/lib/api';
import { cn } from '@/lib/utils';

interface ParagraphItemProps {
  paragraph: ParagraphData;
}

// Obtener el ícono según el tipo de párrafo
function getTypeIcon(type: string): string {
  switch (type.toLowerCase()) {
    case 'hechos':
      return '📋';
    case 'derecho':
      return '⚖️';
    case 'petitorio':
      return '🎯';
    case 'prueba':
      return '📁';
    case 'conclusión':
    case 'conclusion':
      return '🏁';
    default:
      return '📄';
  }
}

// Obtener clase CSS para el tipo
function getTypeClass(type: string): string {
  switch (type.toLowerCase()) {
    case 'hechos':
      return 'type-hechos';
    case 'derecho':
      return 'type-derecho';
    case 'petitorio':
      return 'type-petitorio';
    case 'prueba':
      return 'type-prueba';
    default:
      return 'type-default';
  }
}

// Truncar contenido si es muy largo
function truncateContent(content: string, maxLength: number = 150): string {
  if (content.length <= maxLength) return content;
  return content.substring(0, maxLength).trim() + '...';
}

export const ParagraphItem = memo(({ paragraph }: ParagraphItemProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const needsTruncation = paragraph.contenido.length > 150;

  const toggleExpanded = () => {
    if (needsTruncation) {
      setIsExpanded(!isExpanded);
    }
  };

  return (
    <div className={cn(
      "bg-card/50 border border-border rounded-lg overflow-hidden transition-all duration-200",
      "hover:bg-card/80 hover:border-border/80 hover:-translate-y-0.5 hover:shadow-sm",
      paragraph.modificado && "border-purple-500/50 bg-purple-500/5"
    )}>
      {/* Header del párrafo */}
      <div className="flex items-center justify-between p-3 pb-2 border-b border-border/50">
        <div className="flex items-center gap-2">
          <span className={cn(
            "px-2 py-1 rounded-md text-xs font-mono font-semibold",
            "bg-background/80 text-foreground/80"
          )}>
            §{paragraph.numero}
          </span>
          
          {paragraph.modificado && (
            <div className="flex items-center text-xs text-purple-400 animate-pulse">
              <span>✨</span>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-1.5">
          <span className="text-sm">{getTypeIcon(paragraph.tipo)}</span>
          <span className={cn(
            "text-xs font-medium uppercase tracking-wide",
            getTypeClass(paragraph.tipo) === 'type-hechos' && "text-blue-400",
            getTypeClass(paragraph.tipo) === 'type-derecho' && "text-purple-400",
            getTypeClass(paragraph.tipo) === 'type-petitorio' && "text-green-400",
                            getTypeClass(paragraph.tipo) === 'type-prueba' && "text-primary",
            getTypeClass(paragraph.tipo) === 'type-default' && "text-muted-foreground"
          )}>
            {paragraph.tipo}
          </span>
        </div>
      </div>
      
      {/* Contenido del párrafo */}
      <div className="p-3 pt-2">
        <p className="text-sm text-foreground leading-relaxed break-words">
          {isExpanded ? paragraph.contenido : truncateContent(paragraph.contenido)}
        </p>
        
        {needsTruncation && (
          <button
            onClick={toggleExpanded}
            className={cn(
              "mt-2 text-xs text-blue-400 hover:text-blue-300",
              "transition-colors cursor-pointer hover:underline"
            )}
          >
            {isExpanded ? 'Ver menos...' : 'Ver más...'}
          </button>
        )}
      </div>
      
      {/* Footer con metadata (si existe) */}
      {paragraph.fecha_modificacion && (
        <div className="px-3 pb-2 border-t border-border/30 bg-background/20">
          <span className="text-xs text-muted-foreground italic">
            Editado: {new Date(paragraph.fecha_modificacion).toLocaleString('es-ES', {
              hour: '2-digit',
              minute: '2-digit',
              day: '2-digit',
              month: '2-digit'
            })}
          </span>
        </div>
      )}
    </div>
  );
});

ParagraphItem.displayName = 'ParagraphItem'; 