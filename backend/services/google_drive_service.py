"""
Google Drive Service
Handles file listing, downloading, and conversion from Google Drive
"""

import os
import tempfile
import io
import mimetypes
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path

# Importaciones condicionales de Google Drive API para compatibilidad con Railway
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload
    from google.oauth2.credentials import Credentials
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
    build = None
    HttpError = Exception
    MediaIoBaseDownload = None
    Credentials = None

from .token_manager import token_manager
try:
    from ..config import settings
except ImportError:
    from ..config import settings


class GoogleDriveService:
    """Service for interacting with Google Drive API"""
    
    # Supported file types and their conversion mappings
    SUPPORTED_MIME_TYPES = {
        # Documents - Solo Google Docs nativos pueden convertirse
        'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': None,  # No conversion needed
        'application/msword': None,  # CORREGIDO: Archivos .doc no se pueden convertir, se descargan directamente
        'application/pdf': None,  # No conversion needed
        'text/plain': None,  # No conversion needed
        
        # Spreadsheets (for potential future support)
        'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': None,
        
        # Presentations (for potential future support)
        'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    }
    
    def __init__(self):
        self.drive_service = None
        self.current_credentials = None
        self.available = GOOGLE_DRIVE_AVAILABLE
        
        if not GOOGLE_DRIVE_AVAILABLE:
            print("⚠️ Google Drive API no disponible - funcionalidad limitada")
    
    def _get_service(self, credentials):
        """Get or create Google Drive service with credentials"""
        if not GOOGLE_DRIVE_AVAILABLE:
            raise Exception("Google Drive API no está disponible. Instale google-api-python-client y dependencias relacionadas.")
            
        if self.drive_service is None or self.current_credentials != credentials:
            self.drive_service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
            self.current_credentials = credentials
        return self.drive_service
    
    def _is_supported_file(self, mime_type: str, name: str) -> bool:
        """Check if file type is supported for import"""
        # Check by MIME type
        if mime_type in self.SUPPORTED_MIME_TYPES:
            return True
        
        # Check by file extension as fallback
        ext = Path(name).suffix.lower()
        supported_extensions = {'.pdf', '.doc', '.docx', '.txt'}
        return ext in supported_extensions
    
    def _get_conversion_mime_type(self, original_mime: str) -> Optional[str]:
        """Get target MIME type for conversion, if needed"""
        return self.SUPPORTED_MIME_TYPES.get(original_mime)
    
    async def list_files(
        self, 
        credentials: Credentials,
        folder_id: Optional[str] = None,
        mime_types: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        List files from Google Drive
        """
        try:
            print(f"📂 GoogleDriveService.list_files called")
            print(f"   folder_id: {folder_id}")
            print(f"   search_query: {search_query}")
            print(f"   page_size: {page_size}")
            
            service = self._get_service(credentials)
            print(f"✅ Got Google Drive service")
            
            # Build query
            query_parts = []
            
            # Folder constraint
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            
            # MIME type constraint
            if mime_types:
                mime_conditions = [f"mimeType='{mime}'" for mime in mime_types]
                query_parts.append(f"({' or '.join(mime_conditions)})")
            else:
                # Default: only show supported file types and folders
                supported_mimes = list(self.SUPPORTED_MIME_TYPES.keys())
                supported_mimes.append('application/vnd.google-apps.folder')
                mime_conditions = [f"mimeType='{mime}'" for mime in supported_mimes]
                query_parts.append(f"({' or '.join(mime_conditions)})")
            
            # Search query
            if search_query:
                query_parts.append(f"name contains '{search_query}'")
            
            # Not trashed
            query_parts.append("trashed=false")
            
            # Combine query
            query = ' and '.join(query_parts)
            
            # Execute request
            print(f"📝 Query: {query}")
            results = service.files().list(
                q=query,
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, createdTime, parents, webViewLink, thumbnailLink)",
                orderBy="folder,name"
            ).execute()
            print(f"✅ Google Drive API call successful")
            
            files = results.get('files', [])
            print(f"✅ Got {len(files)} files from API")
            
            # Process files
            processed_files = []
            folders = []
            documents = []
            
            for file in files:
                file_data = {
                    'id': file['id'],
                    'name': file['name'],
                    'mimeType': file['mimeType'],
                    'size': int(file.get('size', 0)) if file.get('size') else None,
                    'modifiedTime': file.get('modifiedTime'),
                    'createdTime': file.get('createdTime'),
                    'parents': file.get('parents', []),
                    'webViewLink': file.get('webViewLink'),
                    'thumbnailLink': file.get('thumbnailLink'),
                    'isFolder': file['mimeType'] == 'application/vnd.google-apps.folder',
                    'isSupported': self._is_supported_file(file['mimeType'], file['name']),
                    'needsConversion': self._get_conversion_mime_type(file['mimeType']) is not None
                }
                
                if file_data['isFolder']:
                    folders.append(file_data)
                elif file_data['isSupported']:
                    documents.append(file_data)
                
                processed_files.append(file_data)
            
            # Get breadcrumb path if we're in a folder
            breadcrumb = []
            if folder_id:
                breadcrumb = await self._get_folder_breadcrumb(service, folder_id)
            
            return {
                'files': processed_files,
                'folders': folders,
                'documents': documents,
                'total': len(processed_files),
                'nextPageToken': results.get('nextPageToken'),
                'breadcrumb': breadcrumb,
                'query': query
            }
            
        except HttpError as e:
            raise Exception(f"Google Drive API error: {e}")
        except Exception as e:
            raise Exception(f"Error listing files: {e}")
    
    async def _get_folder_breadcrumb(self, service, folder_id: str) -> List[Dict]:
        """Get breadcrumb path for current folder"""
        breadcrumb = []
        current_id = folder_id
        
        try:
            while current_id and current_id != 'root':
                folder = service.files().get(
                    fileId=current_id,
                    fields="id, name, parents"
                ).execute()
                
                breadcrumb.insert(0, {
                    'id': folder['id'],
                    'name': folder['name']
                })
                
                # Get parent
                parents = folder.get('parents', [])
                current_id = parents[0] if parents else None
                
                # Prevent infinite loops
                if len(breadcrumb) > 10:
                    break
                    
        except HttpError:
            # If we can't get breadcrumb, just return what we have
            pass
        
        # Add root at the beginning
        breadcrumb.insert(0, {'id': 'root', 'name': 'Mi unidad'})
        
        return breadcrumb
    
    async def get_file_metadata(self, credentials: Credentials, file_id: str) -> Dict:
        """Get detailed metadata for a specific file"""
        try:
            service = self._get_service(credentials)
            
            file_metadata = service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, modifiedTime, createdTime, parents, webViewLink, description"
            ).execute()
            
            return {
                'id': file_metadata['id'],
                'name': file_metadata['name'],
                'mimeType': file_metadata['mimeType'],
                'size': int(file_metadata.get('size', 0)) if file_metadata.get('size') else None,
                'modifiedTime': file_metadata.get('modifiedTime'),
                'createdTime': file_metadata.get('createdTime'),
                'parents': file_metadata.get('parents', []),
                'webViewLink': file_metadata.get('webViewLink'),
                'description': file_metadata.get('description', ''),
                'isSupported': self._is_supported_file(file_metadata['mimeType'], file_metadata['name']),
                'needsConversion': self._get_conversion_mime_type(file_metadata['mimeType']) is not None
            }
            
        except HttpError as e:
            raise Exception(f"Error getting file metadata: {e}")
    
    async def download_and_convert_file(
        self, 
        credentials: Credentials, 
        file_id: str,
        target_format: str = 'docx'
    ) -> Tuple[str, str, Dict]:
        """
        Download file from Google Drive and convert if needed
        Returns: (file_path, filename, metadata)
        """
        try:
            service = self._get_service(credentials)
            
            # Get file metadata
            file_metadata = await self.get_file_metadata(credentials, file_id)
            original_name = file_metadata['name']
            original_mime = file_metadata['mimeType']
            
            print(f"📁 Downloading: {original_name} ({original_mime})")
            
            # Determine if conversion is needed
            conversion_mime = self._get_conversion_mime_type(original_mime)
            
            # Create temporary file
            if conversion_mime:
                # File needs conversion
                print(f"🔄 Converting {original_mime} → {conversion_mime}")
                
                # Export with conversion
                request = service.files().export_media(
                    fileId=file_id,
                    mimeType=conversion_mime
                )
                
                # Determine output extension
                if target_format == 'docx' or conversion_mime.endswith('wordprocessingml.document'):
                    extension = '.docx'
                    final_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                elif conversion_mime == 'text/plain':
                    extension = '.txt'
                    final_mime = 'text/plain'
                else:
                    extension = '.docx'  # Default
                    final_mime = conversion_mime
                
                # Create filename
                base_name = Path(original_name).stem
                converted_filename = f"{base_name}_converted{extension}"
                
            else:
                # No conversion needed, download directly
                print(f"📥 Downloading directly: {original_mime}")
                
                request = service.files().get_media(fileId=file_id)
                converted_filename = original_name
                final_mime = original_mime
            
            # Download file content
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    print(f"📊 Download progress: {int(status.progress() * 100)}%")
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f"_{converted_filename}",
                prefix="gdrive_"
            )
            
            file_content.seek(0)
            temp_file.write(file_content.getvalue())
            temp_file.close()
            
            metadata = {
                'original_name': original_name,
                'converted_name': converted_filename,
                'original_mime': original_mime,
                'final_mime': final_mime,
                'google_file_id': file_id,
                'was_converted': conversion_mime is not None,
                'download_time': datetime.utcnow().isoformat(),
                'file_size': len(file_content.getvalue())
            }
            
            print(f"✅ Downloaded: {temp_file.name}")
            return temp_file.name, converted_filename, metadata
            
        except HttpError as e:
            raise Exception(f"Google Drive download error: {e}")
        except Exception as e:
            raise Exception(f"Error downloading file: {e}")
    
    def cleanup_temp_file(self, file_path: str):
        """Clean up temporary file"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                print(f"🗑️ Cleaned up temp file: {file_path}")
        except Exception as e:
            print(f"⚠️ Error cleaning up temp file {file_path}: {e}")
    
    async def get_user_info(self, credentials: Credentials) -> Dict:
        """Get Google user information"""
        try:
            service = self._get_service(credentials)
            about = service.about().get(fields='user,storageQuota').execute()
            
            user = about.get('user', {})
            storage = about.get('storageQuota', {})
            
            return {
                'email': user.get('emailAddress'),
                'name': user.get('displayName'),
                'photo_link': user.get('photoLink'),
                'permission_id': user.get('permissionId'),
                'storage_used': int(storage.get('usage', 0)),
                'storage_limit': int(storage.get('limit', 0)) if storage.get('limit') else None
            }
            
        except HttpError as e:
            raise Exception(f"Error getting user info: {e}")
    
    async def create_file(
        self,
        credentials: Credentials,
        file_name: str,
        file_content: bytes,
        parent_folder_id: Optional[str] = None,
        mime_type: str = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ) -> Dict:
        """
        Create a new file in Google Drive
        
        Args:
            credentials: Google OAuth2 credentials
            file_name: Name of the file to create
            file_content: File content as bytes
            parent_folder_id: ID of parent folder (None for root)
            mime_type: MIME type of the file
            
        Returns:
            Dictionary with file metadata
        """
        try:
            if not GOOGLE_DRIVE_AVAILABLE:
                raise Exception("Google Drive API no está disponible")
                
            from googleapiclient.http import MediaIoBaseUpload
            
            service = self._get_service(credentials)
            
            # Prepare file metadata
            file_metadata = {
                'name': file_name,
                'mimeType': mime_type
            }
            
            # Set parent folder if specified (validate first)
            if parent_folder_id:
                # Validate that the folder exists and we have write access
                try:
                    folder_check = service.files().get(
                        fileId=parent_folder_id,
                        fields="id, name, mimeType, capabilities"
                    ).execute()
                    
                    # Verify it's actually a folder
                    if folder_check.get('mimeType') != 'application/vnd.google-apps.folder':
                        raise Exception(f"Specified parent ID {parent_folder_id} is not a folder")
                    
                    file_metadata['parents'] = [parent_folder_id]
                    print(f"✅ Validated parent folder: {folder_check.get('name')}")
                    
                except HttpError as e:
                    if e.resp.status == 404:
                        print(f"⚠️ Parent folder {parent_folder_id} not found, uploading to root instead")
                        # Don't set parents - will upload to root
                    elif e.resp.status == 403:
                        print(f"⚠️ No permission to access folder {parent_folder_id}, uploading to root instead")
                        # Don't set parents - will upload to root
                    else:
                        raise Exception(f"Error validating parent folder: {e}")
                except Exception as e:
                    print(f"⚠️ Error validating parent folder: {e}, uploading to root instead")
            
            # Create media upload
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype=mime_type,
                resumable=True
            )
            
            print(f"📤 Uploading file: {file_name} to Google Drive...")
            
            # Upload file
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, parents, createdTime, mimeType'
            ).execute()
            
            print(f"✅ File uploaded successfully: {file.get('id')}")
            
            return {
                'id': file.get('id'),
                'name': file.get('name'),
                'webViewLink': file.get('webViewLink'),
                'parents': file.get('parents', []),
                'createdTime': file.get('createdTime'),
                'mimeType': file.get('mimeType'),
                'success': True
            }
            
        except HttpError as e:
            print(f"❌ Google Drive upload error: {e}")
            raise Exception(f"Error uploading file to Google Drive: {e}")
        except Exception as e:
            print(f"❌ Upload error: {e}")
            raise Exception(f"Error creating file: {e}")
    
    async def create_folder(
        self,
        credentials: Credentials,
        folder_name: str,
        parent_folder_id: Optional[str] = None
    ) -> Dict:
        """
        Create a new folder in Google Drive
        
        Args:
            credentials: Google OAuth2 credentials
            folder_name: Name of the folder to create
            parent_folder_id: ID of parent folder (None for root)
            
        Returns:
            Dictionary with folder metadata
        """
        try:
            service = self._get_service(credentials)
            
            # Prepare folder metadata
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            # Set parent folder if specified
            if parent_folder_id:
                folder_metadata['parents'] = [parent_folder_id]
            
            print(f"📁 Creating folder: {folder_name} in Google Drive...")
            
            # Create folder
            folder = service.files().create(
                body=folder_metadata,
                fields='id, name, webViewLink, parents, createdTime'
            ).execute()
            
            print(f"✅ Folder created successfully: {folder.get('id')}")
            
            return {
                'id': folder.get('id'),
                'name': folder.get('name'),
                'webViewLink': folder.get('webViewLink'),
                'parents': folder.get('parents', []),
                'createdTime': folder.get('createdTime'),
                'mimeType': 'application/vnd.google-apps.folder',
                'isFolder': True,
                'success': True
            }
            
        except HttpError as e:
            print(f"❌ Google Drive folder creation error: {e}")
            raise Exception(f"Error creating folder in Google Drive: {e}")
        except Exception as e:
            print(f"❌ Folder creation error: {e}")
            raise Exception(f"Error creating folder: {e}")
    
    async def get_folder_contents(
        self,
        credentials: Credentials,
        folder_id: Optional[str] = None,
        folders_only: bool = False,
        search_query: Optional[str] = None
    ) -> List[Dict]:
        """
        Get contents of a folder (used for folder picker)
        
        Args:
            credentials: Google OAuth2 credentials
            folder_id: ID of folder to list (None for root)
            folders_only: If True, only return folders
            search_query: Optional search query to filter folders
            
        Returns:
            List of folder/file metadata
        """
        try:
            service = self._get_service(credentials)
            
            # Build query
            query_parts = []
            
            # Folder constraint
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            
            # Only folders if specified
            if folders_only:
                query_parts.append("mimeType='application/vnd.google-apps.folder'")
            
            # Search query
            if search_query:
                query_parts.append(f"name contains '{search_query}'")
            
            # Not trashed
            query_parts.append("trashed=false")
            
            # Combine query
            query = ' and '.join(query_parts)
            
            print(f"📂 Getting folder contents with query: {query}")
            
            # Execute request with ordering by modifiedTime descending
            results = service.files().list(
                q=query,
                pageSize=100,
                fields="files(id, name, mimeType, parents, modifiedTime, createdTime)",
                orderBy="modifiedTime desc"  # Ordenar por última modificación
            ).execute()
            
            files = results.get('files', [])
            
            # Process files
            processed_files = []
            for file in files:
                processed_files.append({
                    'id': file['id'],
                    'name': file['name'],
                    'mimeType': file['mimeType'],
                    'parents': file.get('parents', []),
                    'modifiedTime': file.get('modifiedTime'),
                    'createdTime': file.get('createdTime'),
                    'isFolder': file['mimeType'] == 'application/vnd.google-apps.folder'
                })
            
            return processed_files
            
        except HttpError as e:
            print(f"❌ Error getting folder contents: {e}")
            raise Exception(f"Error getting folder contents: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
            raise Exception(f"Error getting folder contents: {e}")


# Global instance (condicional para compatibilidad con Railway)
if GOOGLE_DRIVE_AVAILABLE:
    google_drive_service = GoogleDriveService()
else:
    # Crear un servicio mock que arroja errores informativos
    class MockGoogleDriveService:
        def __init__(self):
            self.available = False
            
        def __getattr__(self, name):
            def method_not_available(*args, **kwargs):
                raise Exception("Google Drive API no está disponible. Instale google-api-python-client y dependencias relacionadas.")
            return method_not_available
    
    google_drive_service = MockGoogleDriveService() 