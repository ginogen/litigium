import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Utilidades adicionales del sistema legal
export function formatDate(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function formatTime(timestamp: string | Date): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diffInSeconds < 60) {
    return 'hace ' + diffInSeconds + 's';
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return 'hace ' + minutes + 'm';
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return 'hace ' + hours + 'h';
  } else {
    return date.toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}

export function truncateText(text: string, maxLength: number = 150): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim() + '...';
}

export function getFileIcon(fileName: string): string {
  const extension = fileName.split('.').pop()?.toLowerCase();
  switch (extension) {
    case 'pdf': return '📄';
    case 'doc':
    case 'docx': return '📝';
    case 'txt': return '📃';
    default: return '📋';
  }
}

export function getOperationIcon(operation: string): string {
  switch (operation.toLowerCase()) {
    case 'reemplazar':
    case 'replace':
      return '🔄';
    case 'agregar':
    case 'add':
      return '➕';
    case 'eliminar':
    case 'delete':
      return '🗑️';
    case 'insertar':
    case 'insert':
      return '📝';
    case 'modificar':
    case 'modify':
      return '✏️';
    default:
      return '⚡';
  }
} 