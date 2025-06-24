/**
 * Google Drive API Client
 * Handles all Google Drive integration API calls
 */

import { api, apiLong } from './api';

// ================== TYPES ==================

export interface GoogleDriveFile {
  id: string;
  name: string;
  mimeType: string;
  size?: number;
  modifiedTime?: string;
  createdTime?: string;
  parents?: string[];
  webViewLink?: string;
  thumbnailLink?: string;
  isFolder: boolean;
  isSupported: boolean;
  needsConversion: boolean;
}

export interface GoogleDriveBreadcrumb {
  id: string;
  name: string;
}

export interface GoogleDriveFilesResponse {
  success: boolean;
  files: GoogleDriveFile[];
  folders: GoogleDriveFile[];
  documents: GoogleDriveFile[];
  total: number;
  nextPageToken?: string;
  breadcrumb: GoogleDriveBreadcrumb[];
  query?: string;
}

export interface ConnectionStatus {
  connected: boolean;
  google_email?: string;
  google_user_id?: string;
  connected_at?: string;
  last_sync_at?: string;
  expires_at?: string;
  needs_refresh: boolean;
}

export interface ImportResult {
  success: boolean;
  message: string;
  file_name: string;
  file_id: string;
  needs_conversion: boolean;
}

export interface ImportHistoryItem {
  id: string;
  google_file_id: string;
  google_file_name: string;
  google_mime_type: string;
  sync_status: 'pending' | 'imported' | 'error' | 'updated' | 'skipped';
  sync_error_message?: string;
  last_imported_at?: string;
  import_categoria_id?: string;
  import_tipo_demanda?: string;
  created_at: string;
}

export interface ImportFilesRequest {
  files: GoogleDriveFile[];
  categoriaId: string;
  tipoDemanda: string;
}

// ================== API CLIENT ==================

interface GoogleDriveAPIType {
  getConnectionStatus(): Promise<ConnectionStatus>;
  initiateConnection(): Promise<string>;
  completeConnection(authCode: string): Promise<void>;
  disconnect(): Promise<void>;
  listFiles(params?: { folderId?: string; search?: string; pageSize?: number }): Promise<GoogleDriveFilesResponse>;
  getFileMetadata(fileId: string): Promise<{ success: boolean; metadata: GoogleDriveFile }>;
  importFile(params: { fileId: string; categoriaId: string; tipoDemanda: string }): Promise<ImportResult>;
  importMultipleFiles(request: ImportFilesRequest): Promise<ImportResult[]>;
  getImportHistory(limit?: number): Promise<{ success: boolean; history: ImportHistoryItem[]; total: number }>;
  // New save functionality
  saveFile(request: SaveFileRequest): Promise<SaveFileResponse>;
  createFolder(request: CreateFolderRequest): Promise<{ success: boolean; message: string; folder_id: string; folder_name: string }>;
  getFolders(parentId?: string, search?: string): Promise<FolderPickerResponse>;
}

export const googleDriveAPI: GoogleDriveAPIType = {
  /**
   * Get current connection status
   */
  async getConnectionStatus(): Promise<ConnectionStatus> {
    try {
      const response = await api.get<ConnectionStatus>('/api/google-drive/status');
      return response.data;
    } catch (error: any) {
      console.error('Error getting connection status:', error);
      
      // Si es 404, significa que no hay conexión - devolver estado desconectado
      if (error.response?.status === 404) {
        return {
          connected: false,
          needs_refresh: false
        };
      }
      
      // Para otros errores, también asumir desconectado para evitar estados incorrectos
      if (error.response?.status >= 400) {
        console.warn('API error, assuming disconnected state:', error.response.status);
        return {
          connected: false,
          needs_refresh: false
        };
      }
      
      throw error;
    }
  },

  /**
   * Initiate Google Drive connection (get OAuth URL)
   */
  async initiateConnection(): Promise<string> {
    try {
      const response = await api.get<{ success: boolean; auth_url: string; message: string }>('/api/google-drive/auth-url');
      
      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to get authorization URL');
      }
      
      return response.data.auth_url;
    } catch (error) {
      console.error('Error initiating connection:', error);
      throw error;
    }
  },

  /**
   * Complete connection with authorization code
   */
  async completeConnection(authCode: string): Promise<void> {
    try {
      const response = await api.post('/api/google-drive/connect', {
        authorization_code: authCode
      });
      
      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to connect Google Drive');
      }
    } catch (error) {
      console.error('Error completing connection:', error);
      throw error;
    }
  },

  /**
   * Disconnect Google Drive
   */
  async disconnect(): Promise<void> {
    try {
      const response = await api.delete('/api/google-drive/disconnect');
      
      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to disconnect Google Drive');
      }
    } catch (error) {
      console.error('Error disconnecting:', error);
      throw error;
    }
  },

  /**
   * List files from Google Drive
   */
  async listFiles(params: {
    folderId?: string;
    search?: string;
    pageSize?: number;
  } = {}): Promise<GoogleDriveFilesResponse> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.folderId) {
        queryParams.append('folder_id', params.folderId);
      }
      if (params.search) {
        queryParams.append('search', params.search);
      }
      if (params.pageSize) {
        queryParams.append('page_size', params.pageSize.toString());
      }
      
      const response = await api.get<GoogleDriveFilesResponse>(`/api/google-drive/files?${queryParams}`);
      return response.data;
    } catch (error) {
      console.error('Error listing files:', error);
      throw error;
    }
  },

  /**
   * Get metadata for a specific file
   */
  async getFileMetadata(fileId: string): Promise<{ success: boolean; metadata: GoogleDriveFile }> {
    try {
      const response = await api.get<{ success: boolean; metadata: GoogleDriveFile }>(`/api/google-drive/files/${fileId}/metadata`);
      return response.data;
    } catch (error) {
      console.error('Error getting file metadata:', error);
      throw error;
    }
  },

  /**
   * Import a single file from Google Drive
   */
  async importFile(params: {
    fileId: string;
    categoriaId: string;
    tipoDemanda: string;
  }): Promise<ImportResult> {
    try {
      const response = await apiLong.post<ImportResult>(`/api/google-drive/import/${params.fileId}`, {
        categoria_id: params.categoriaId,
        tipo_demanda: params.tipoDemanda
      });
      
      return response.data;
    } catch (error) {
      console.error('Error importing file:', error);
      throw error;
    }
  },

  /**
   * Import multiple files from Google Drive
   */
  async importMultipleFiles(request: ImportFilesRequest): Promise<ImportResult[]> {
    try {
      const promises = request.files.map(file => 
        this.importFile({
          fileId: file.id,
          categoriaId: request.categoriaId,
          tipoDemanda: request.tipoDemanda
        }).catch(error => ({
          success: false,
          message: error.response?.data?.detail || error.message || 'Error importing file',
          file_name: file.name,
          file_id: file.id,
          needs_conversion: file.needsConversion
        }))
      );
      
      const results = await Promise.all(promises);
      
      // Log para debugging de conteo
      const actualSuccessful = results.filter(r => r.success);
      const actualFailed = results.filter(r => !r.success);
      console.log(`📊 Import results: ${actualSuccessful.length} successful, ${actualFailed.length} failed`);
      
      // Log detallado de errores
      actualFailed.forEach(failed => {
        console.error(`❌ Failed import: ${failed.file_name} - ${failed.message}`);
      });
      
      return results;
      
    } catch (error) {
      console.error('Error importing multiple files:', error);
      throw error;
    }
  },

  /**
   * Get import history
   */
  async getImportHistory(limit: number = 50): Promise<{ success: boolean; history: ImportHistoryItem[]; total: number }> {
    try {
      const response = await api.get<{ success: boolean; history: ImportHistoryItem[]; total: number }>(`/api/google-drive/import-history?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Error getting import history:', error);
      throw error;
    }
  },

  /**
   * Save a file to Google Drive
   */
  async saveFile(request: SaveFileRequest): Promise<SaveFileResponse> {
    try {
      const response = await api.post<SaveFileResponse>('/api/google-drive/save-file', request);
      return response.data;
    } catch (error) {
      console.error('Error saving file to Google Drive:', error);
      throw error;
    }
  },

  /**
   * Create a new folder in Google Drive
   */
  async createFolder(request: CreateFolderRequest): Promise<{ success: boolean; message: string; folder_id: string; folder_name: string }> {
    try {
      const response = await api.post('/api/google-drive/create-folder', request);
      return response.data;
    } catch (error) {
      console.error('Error creating folder in Google Drive:', error);
      throw error;
    }
  },

  /**
   * Get folders for folder picker
   */
  async getFolders(parentId?: string, search?: string): Promise<FolderPickerResponse> {
    try {
      const params: Record<string, string> = {};
      if (parentId) params.parent_id = parentId;
      if (search) params.search = search;
      
      const response = await api.get<FolderPickerResponse>('/api/google-drive/folders', { params });
      return response.data;
    } catch (error) {
      console.error('Error getting folders:', error);
      throw error;
    }
  }
};

// ================== UTILITY FUNCTIONS ==================

/**
 * Format file size to human readable format
 */
export function formatFileSize(bytes?: number): string {
  if (!bytes) return 'N/A';
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Format date to local string
 */
export function formatDate(dateString?: string): string {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Get file type icon based on MIME type
 */
export function getFileTypeIcon(mimeType: string): string {
  if (mimeType === 'application/vnd.google-apps.folder') {
    return '📁';
  } else if (mimeType.includes('document') || mimeType.includes('word')) {
    return '📄';
  } else if (mimeType.includes('pdf')) {
    return '📕';
  } else if (mimeType.includes('text')) {
    return '📄';
  } else if (mimeType.includes('spreadsheet') || mimeType.includes('excel')) {
    return '📊';
  } else if (mimeType.includes('presentation') || mimeType.includes('powerpoint')) {
    return '📊';
  } else if (mimeType.includes('image')) {
    return '🖼️';
  } else {
    return '📄';
  }
}

/**
 * Check if file type is supported for import
 */
export function isFileSupported(file: GoogleDriveFile): boolean {
  return file.isSupported;
}

/**
 * Get status color for import status
 */
export function getStatusColor(status: string): string {
  switch (status) {
    case 'imported':
      return 'text-green-600';
    case 'pending':
      return 'text-yellow-600';
    case 'error':
      return 'text-red-600';
    case 'skipped':
      return 'text-gray-600';
    default:
      return 'text-gray-600';
  }
}

/**
 * Get status text in Spanish
 */
export function getStatusText(status: string): string {
  switch (status) {
    case 'imported':
      return 'Importado';
    case 'pending':
      return 'Pendiente';
    case 'error':
      return 'Error';
    case 'skipped':
      return 'Omitido';
    default:
      return 'Desconocido';
  }
}

// ================== NEW SAVE FUNCTIONALITY ==================

export interface SaveFileRequest {
  file_name: string;
  file_content: string; // Base64 encoded
  folder_id?: string;
  mime_type?: string;
}

export interface CreateFolderRequest {
  folder_name: string;
  parent_folder_id?: string;
}

export interface SaveFileResponse {
  success: boolean;
  message: string;
  file_id: string;
  file_name: string;
  web_view_link?: string;
  created_time?: string;
}

export interface FolderPickerResponse {
  success: boolean;
  folders: GoogleDriveFile[];
  breadcrumb: GoogleDriveBreadcrumb[];
  total: number;
}

/**
 * Helper function to convert file to base64
 */
export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // Remove data URL prefix to get just the base64 content
      const base64 = result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

/**
 * Helper function to convert text content to base64
 */
export function textToBase64(text: string): string {
  return btoa(unescape(encodeURIComponent(text)));
} 