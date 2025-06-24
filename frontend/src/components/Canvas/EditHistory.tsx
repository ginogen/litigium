import React, { memo } from 'react';
import { EditHistoryItem } from '@/lib/api';
import { cn, formatTime, getOperationIcon } from '@/lib/utils';

interface EditHistoryProps {
  history: EditHistoryItem[];
}

// Obtener clase CSS según el tipo de operación
function getOperationClass(operation: string): string {
  switch (operation.toLowerCase()) {
    case 'reemplazar':
    case 'replace':
      return 'op-replace';
    case 'agregar':
    case 'add':
      return 'op-add';
    case 'eliminar':
    case 'delete':
      return 'op-delete';
    case 'insertar':
    case 'insert':
      return 'op-insert';
    case 'modificar':
    case 'modify':
      return 'op-modify';
    default:
      return 'op-default';
  }
}

// Truncar comando si es muy largo
function truncateCommand(command: string, maxLength: number = 60): string {
  if (command.length <= maxLength) return command;
  return command.substring(0, maxLength).trim() + '...';
}

const HistoryItem = memo(({ entry }: { entry: EditHistoryItem }) => {
  return (
    <div className={cn(
      "bg-card/30 border border-border rounded-lg overflow-hidden transition-all duration-200",
      "hover:bg-card/50 hover:border-border/80 mb-2"
    )}>
      {/* Header del item */}
      <div className="flex items-center justify-between p-3 border-b border-border/50">
        <div className="flex items-center gap-2">
          <span className="text-sm">{getOperationIcon(entry.operacion)}</span>
          <span className={cn(
            "text-sm font-medium capitalize",
            getOperationClass(entry.operacion) === 'op-replace' && "text-blue-400",
            getOperationClass(entry.operacion) === 'op-add' && "text-green-400", 
            getOperationClass(entry.operacion) === 'op-delete' && "text-red-400",
            getOperationClass(entry.operacion) === 'op-insert' && "text-purple-400",
                            getOperationClass(entry.operacion) === 'op-modify' && "text-primary",
            getOperationClass(entry.operacion) === 'op-default' && "text-muted-foreground"
          )}>
            {entry.operacion}
          </span>
          {entry.parrafo_numero && (
            <span className="px-1.5 py-0.5 bg-background/50 text-xs rounded text-muted-foreground font-mono">
              §{entry.parrafo_numero}
            </span>
          )}
        </div>
        <div className="text-xs text-muted-foreground italic">
          {formatTime(entry.timestamp)}
        </div>
      </div>
      
      {/* Comando ejecutado */}
      <div className="p-3">
        <p 
          className={cn(
            "text-sm text-foreground/80 font-mono bg-background/30 p-2 rounded",
            "border-l-2 border-border/50 leading-relaxed"
          )}
          title={entry.comando}
        >
          {truncateCommand(entry.comando)}
        </p>
      </div>
      
      {/* Resultado (si existe) */}
      {entry.resultado && (
        <div className="px-3 pb-3 border-t border-border/30">
          <div className={cn(
            "inline-block text-xs font-medium px-2 py-1 rounded mt-2",
            entry.exito
              ? "bg-green-500/15 text-green-400"
              : "bg-red-500/15 text-red-400"
          )}>
            {entry.exito ? '✅ Exitoso' : '❌ Error'}
          </div>
          {entry.mensaje && (
            <div className="text-xs text-muted-foreground mt-1 italic">
              {entry.mensaje}
            </div>
          )}
        </div>
      )}
    </div>
  );
});

HistoryItem.displayName = 'HistoryItem';

export const EditHistory = memo(({ history }: EditHistoryProps) => {
  return (
    <div className="flex flex-col h-full bg-card/20">
      {/* Header */}
      <div className="p-4 border-b border-border flex items-center justify-between">
        <h3 className="text-lg font-semibold text-foreground">📝 Historial</h3>
        <div className="px-2 py-1 bg-background/50 text-xs rounded text-muted-foreground">
          {history.length} ediciones
        </div>
      </div>
      
      {/* Lista de historial */}
      <div className="flex-1 overflow-y-auto p-2">
        {history.length > 0 ? (
          <div className="space-y-1">
            {history.map((entry) => (
              <HistoryItem key={entry.id} entry={entry} />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center py-16">
            <div className="text-6xl mb-4 opacity-70">📋</div>
            <h4 className="text-lg font-medium text-foreground mb-2">Sin ediciones</h4>
            <p className="text-sm text-muted-foreground">
              Los comandos ejecutados aparecerán aquí
            </p>
          </div>
        )}
      </div>
    </div>
  );
});

EditHistory.displayName = 'EditHistory'; 