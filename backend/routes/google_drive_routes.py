"""
Google Drive API Routes
Handles OAuth2 authentication, file listing, and document import
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Form
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import uuid

from ..auth.dependencies import get_current_user
from ..models.user import User
from ..services.google_drive_service import google_drive_service
from ..services.token_manager import token_manager
from .training_routes import process_document_background
try:
    from ..config import settings
except ImportError:
    from ..config import settings

router = APIRouter(prefix="/api/google-drive", tags=["google-drive"])

# Pydantic models for request/response
class ConnectionRequest(BaseModel):
    authorization_code: str

class ImportFileRequest(BaseModel):
    categoria_id: str
    tipo_demanda: str

class SyncAllRequest(BaseModel):
    categoria_id: Optional[str] = None
    tipo_demanda: Optional[str] = None
    auto_import: bool = False

class ConnectionStatus(BaseModel):
    connected: bool
    google_email: Optional[str] = None
    google_user_id: Optional[str] = None
    connected_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    needs_refresh: bool = False

# ================== DATABASE HELPERS ==================

async def get_user_connection(user_id: str) -> Optional[Dict]:
    """Get user's Google Drive connection from database"""
    try:
        from supabase_integration import supabase_admin
        
        result = supabase_admin.table("google_drive_connections")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("is_active", True)\
            .execute()
        
        if result.data:
            return result.data[0]
        return None
        
    except Exception as e:
        print(f"❌ Error getting user connection: {e}")
        return None

async def save_user_connection(user_id: str, token_data: Dict, user_info: Dict) -> Dict:
    """Save or update user's Google Drive connection"""
    try:
        from supabase_integration import supabase_admin
        
        # Encrypt tokens
        encrypted_tokens = token_manager.encrypt_token_data(token_data)
        
        connection_data = {
            "user_id": user_id,
            "access_token_encrypted": encrypted_tokens["access_token_encrypted"],
            "refresh_token_encrypted": encrypted_tokens["refresh_token_encrypted"],
            "token_expires_at": token_data["expires_at"].isoformat() if token_data.get("expires_at") else None,
            "google_email": user_info["google_email"],
            "google_user_id": user_info["google_user_id"],
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        }
        
        # Upsert connection (update if exists, insert if not)
        result = supabase_admin.table("google_drive_connections")\
            .upsert(connection_data, on_conflict="user_id")\
            .execute()
        
        if result.data:
            print(f"✅ Saved Google Drive connection for user {user_id}")
            return result.data[0]
        else:
            raise Exception("No data returned from upsert")
            
    except Exception as e:
        print(f"❌ Error saving connection: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving connection: {e}")

async def get_user_credentials(user_id: str):
    """Get valid credentials for user"""
    try:
        print(f"🔑 Getting credentials for user {user_id}")
        
        connection = await get_user_connection(user_id)
        if not connection:
            raise HTTPException(status_code=404, detail="Google Drive not connected")
        
        print(f"✅ Found connection for user")
        
        # Decrypt tokens
        decrypted_tokens = token_manager.decrypt_token_data(connection)
        print(f"✅ Decrypted tokens")
        
        # Create credentials with naive datetime (sin timezone) para compatibilidad con Google Auth
        try:
            expires_at = datetime.fromisoformat(connection["token_expires_at"]) if connection.get("token_expires_at") else None
            if expires_at and expires_at.tzinfo is not None:
                # Convertir a UTC naive datetime para compatibilidad con Google Auth
                expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)
            print(f"✅ Parsed expires_at (naive): {expires_at}")
        except (ValueError, TypeError) as e:
            print(f"⚠️ Error parsing expires_at: {e}")
            expires_at = None
            
        credentials = token_manager.create_credentials_from_token_data(decrypted_tokens, expires_at)
        print(f"✅ Created credentials")
        
        # Refresh if needed
        print(f"🔄 Checking if refresh needed...")
        credentials, was_refreshed = token_manager.refresh_credentials(credentials)
        print(f"✅ Refresh check complete, was_refreshed: {was_refreshed}")
        
        # Update database if token was refreshed
        if was_refreshed:
            print(f"🔄 Updating tokens in database...")
            await update_connection_tokens(user_id, credentials)
            print(f"✅ Tokens updated")
        
        return credentials
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_user_credentials: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting credentials: {e}")

async def update_connection_tokens(user_id: str, credentials):
    """Update connection with refreshed tokens"""
    try:
        from supabase_integration import supabase_admin
        
        # Encrypt new tokens
        token_data = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token
        }
        encrypted_tokens = token_manager.encrypt_token_data(token_data)
        
        # Update database
        update_data = {
            "access_token_encrypted": encrypted_tokens["access_token_encrypted"],
            "token_expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        supabase_admin.table("google_drive_connections")\
            .update(update_data)\
            .eq("user_id", user_id)\
            .execute()
        
        print(f"✅ Updated refreshed tokens for user {user_id}")
        
    except Exception as e:
        print(f"⚠️ Error updating refreshed tokens: {e}")

# ================== ROUTES ==================

@router.get("/auth-url")
async def get_google_auth_url():
    """Generate OAuth2 authorization URL for Google Drive"""
    try:
        # Validate Google Drive configuration
        if not settings.validate_google_drive():
            raise HTTPException(
                status_code=500, 
                detail="Google Drive integration not configured. Please contact administrator."
            )
        
        # Use a temporary ID for public auth URL generation
        temp_user_id = "public_auth"
        auth_url = token_manager.get_authorization_url(temp_user_id)
        
        return {
            "success": True,
            "auth_url": auth_url,
            "message": "Please authorize the application to access your Google Drive"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating auth URL: {e}")

@router.post("/connect")
async def connect_google_drive(
    request: ConnectionRequest,
    current_user: User = Depends(get_current_user)
):
    """Complete OAuth2 flow and store connection"""
    try:
        # Exchange authorization code for tokens
        token_data = token_manager.exchange_code_for_tokens(
            request.authorization_code, 
            current_user.id
        )
        
        # Save connection to database
        connection = await save_user_connection(current_user.id, token_data, token_data)
        
        return {
            "success": True,
            "message": "Google Drive connected successfully",
            "connection": {
                "google_email": token_data["google_email"],
                "connected_at": connection["connected_at"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error connecting Google Drive: {e}")

@router.get("/status")
async def get_connection_status(current_user: User = Depends(get_current_user)):
    """Get Google Drive connection status"""
    try:
        print(f"🔍 Checking Google Drive status for user {current_user.id}")
        connection = await get_user_connection(current_user.id)
        
        if not connection:
            print(f"❌ No Google Drive connection found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Google Drive not connected")
        
        print(f"✅ Found Google Drive connection for user {current_user.id}")
        
        # Safe parsing of dates with timezone handling
        def parse_datetime_with_tz(date_str):
            if not date_str:
                return None
            try:
                dt = datetime.fromisoformat(date_str)
                # Si la fecha no tiene timezone, asumir UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except (ValueError, TypeError):
                return None
        
        expires_at = parse_datetime_with_tz(connection.get("token_expires_at"))
        connected_at = parse_datetime_with_tz(connection.get("connected_at"))  
        last_sync_at = parse_datetime_with_tz(connection.get("last_sync_at"))
        
        # Check if token needs refresh (convertir a naive para comparación)
        now_utc = datetime.now(timezone.utc)
        
        # Para la comparación, convertir ambos a naive UTC si es necesario
        if expires_at and expires_at.tzinfo is not None:
            expires_at_naive = expires_at.astimezone(timezone.utc).replace(tzinfo=None)
            now_utc_naive = now_utc.replace(tzinfo=None)
            needs_refresh = expires_at_naive <= now_utc_naive + timedelta(minutes=5)
        elif expires_at and expires_at.tzinfo is None:
            # Si expires_at ya es naive, comparar con naive now
            now_utc_naive = now_utc.replace(tzinfo=None)
            needs_refresh = expires_at <= now_utc_naive + timedelta(minutes=5)
        else:
            needs_refresh = True  # Si no hay fecha de expiración, necesita refresh
        
        status_response = ConnectionStatus(
            connected=True,
            google_email=connection.get("google_email", ""),
            google_user_id=connection.get("google_user_id", ""),
            connected_at=connected_at,
            last_sync_at=last_sync_at,
            expires_at=expires_at,
            needs_refresh=needs_refresh or False
        )
        
        print(f"✅ Returning connection status: connected=True, email={status_response.google_email}")
        return status_response
        
    except HTTPException:
        # Re-raise HTTP exceptions (como 404)
        raise
    except Exception as e:
        print(f"❌ Error in get_connection_status for user {current_user.id}: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error checking status: {e}")

@router.delete("/disconnect")
async def disconnect_google_drive(current_user: User = Depends(get_current_user)):
    """Disconnect Google Drive"""
    try:
        from supabase_integration import supabase_admin
        
        # Mark connection as inactive
        supabase_admin.table("google_drive_connections")\
            .update({"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()})\
            .eq("user_id", current_user.id)\
            .execute()
        
        return {
            "success": True,
            "message": "Google Drive disconnected successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disconnecting: {e}")

@router.get("/files")
async def list_google_drive_files(
    current_user: User = Depends(get_current_user),
    folder_id: Optional[str] = Query(None, description="Folder ID to list (root if not specified)"),
    search: Optional[str] = Query(None, description="Search query"),
    page_size: int = Query(50, ge=1, le=1000)
):
    """List files from user's Google Drive"""
    try:
        print(f"📂 Listing Google Drive files for user {current_user.id}")
        
        credentials = await get_user_credentials(current_user.id)
        print(f"✅ Got credentials for user")
        
        files_data = await google_drive_service.list_files(
            credentials=credentials,
            folder_id=folder_id,
            search_query=search,
            page_size=page_size
        )
        print(f"✅ Got {len(files_data.get('files', []))} files from Google Drive")
        
        return {
            "success": True,
            **files_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in list_google_drive_files: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error listing files: {e}")

@router.get("/files/{file_id}/metadata")
async def get_file_metadata(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get metadata for a specific file"""
    try:
        credentials = await get_user_credentials(current_user.id)
        
        metadata = await google_drive_service.get_file_metadata(credentials, file_id)
        
        return {
            "success": True,
            "metadata": metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metadata: {e}")

@router.post("/import/{file_id}")
async def import_file_from_google_drive(
    file_id: str,
    request: ImportFileRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Import a specific file from Google Drive for training"""
    try:
        credentials = await get_user_credentials(current_user.id)
        
        # Get file metadata first
        metadata = await google_drive_service.get_file_metadata(credentials, file_id)
        
        if not metadata["isSupported"]:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {metadata['mimeType']} is not supported"
            )
        
        # Start background import
        background_tasks.add_task(
            import_google_drive_file_background,
            user_id=current_user.id,
            file_id=file_id,
            categoria_id=request.categoria_id,
            tipo_demanda=request.tipo_demanda,
            credentials=credentials
        )
        
        return {
            "success": True,
            "message": f"Import started for '{metadata['name']}'",
            "file_name": metadata["name"],
            "file_id": file_id,
            "needs_conversion": metadata["needsConversion"]
        }
        
    except HTTPException as he:
        # Mejorar mensajes de error HTTP específicos
        if he.status_code == 400:
            error_detail = str(he.detail)
            if "not supported" in error_detail:
                return {
                    "success": False,
                    "message": f"Formato no compatible: {error_detail}",
                    "file_name": metadata.get("name", "Archivo desconocido") if 'metadata' in locals() else "Archivo desconocido",
                    "file_id": file_id,
                    "needs_conversion": False
                }
        raise he
    except Exception as e:
        error_msg = str(e)
        
        # Categorizar errores comunes y proporcionar mensajes más útiles
        if "Export only supports Docs Editors files" in error_msg:
            return {
                "success": False,
                "message": "Este archivo .doc no se puede convertir automáticamente. Descárgalo manualmente, conviértelo a .docx y súbelo directamente.",
                "file_name": metadata.get("name", "Archivo .doc") if 'metadata' in locals() else "Archivo .doc",
                "file_id": file_id,
                "needs_conversion": True
            }
        elif "403" in error_msg or "permission" in error_msg.lower():
            return {
                "success": False,
                "message": "Sin permisos para acceder al archivo. Verifica que tengas acceso de lectura.",
                "file_name": metadata.get("name", "Archivo restringido") if 'metadata' in locals() else "Archivo restringido",
                "file_id": file_id,
                "needs_conversion": False
            }
        elif "404" in error_msg or "not found" in error_msg.lower():
            return {
                "success": False,
                "message": "Archivo no encontrado. Puede haber sido movido o eliminado de Google Drive.",
                "file_name": metadata.get("name", "Archivo no encontrado") if 'metadata' in locals() else "Archivo no encontrado",
                "file_id": file_id,
                "needs_conversion": False
            }
        elif "quotaExceeded" in error_msg:
            return {
                "success": False,
                "message": "Cuota de Google Drive excedida. Intenta nuevamente más tarde.",
                "file_name": metadata.get("name", "Archivo") if 'metadata' in locals() else "Archivo",
                "file_id": file_id,
                "needs_conversion": False
            }
        else:
            return {
                "success": False,
                "message": f"Error de importación: {error_msg}",
                "file_name": metadata.get("name", "Archivo desconocido") if 'metadata' in locals() else "Archivo desconocido",
                "file_id": file_id,
                "needs_conversion": False
            }

# ================== BACKGROUND TASKS ==================

async def import_google_drive_file_background(
    user_id: str,
    file_id: str,
    categoria_id: str,
    tipo_demanda: str,
    credentials
):
    """Background task to import file from Google Drive"""
    temp_file_path = None
    
    try:
        print(f"🚀 Starting Google Drive import for user {user_id}, file {file_id}")
        
        # Download and convert file
        temp_file_path, filename, download_metadata = await google_drive_service.download_and_convert_file(
            credentials=credentials,
            file_id=file_id,
            target_format='docx'
        )
        
        print(f"📁 Downloaded: {filename} to {temp_file_path}")
        
        # Save Google Drive document record
        await save_google_drive_document_record(
            user_id=user_id,
            file_id=file_id,
            filename=filename,
            categoria_id=categoria_id,
            tipo_demanda=tipo_demanda,
            download_metadata=download_metadata
        )
        
        # Process using existing document processing pipeline
        await process_document_background(
            user_id=user_id,
            file_path=temp_file_path,
            filename=filename,
            categoria_id=categoria_id,
            tipo_demanda=tipo_demanda,
            mime_type=download_metadata["final_mime"]
        )
        
        print(f"✅ Google Drive import completed for {filename}")
        
    except Exception as e:
        print(f"❌ Error in Google Drive import: {e}")
        
        # Update record with error status
        try:
            await update_google_drive_document_status(
                user_id=user_id,
                file_id=file_id,
                status='error',
                error_message=str(e)
            )
        except:
            pass  # Don't fail the whole process if we can't update status
        
    finally:
        # Clean up temporary file
        if temp_file_path:
            google_drive_service.cleanup_temp_file(temp_file_path)

async def save_google_drive_document_record(
    user_id: str,
    file_id: str,
    filename: str,
    categoria_id: str,
    tipo_demanda: str,
    download_metadata: Dict
):
    """Save Google Drive document record to database"""
    try:
        from supabase_integration import supabase_admin
        
        # Get connection ID
        connection = await get_user_connection(user_id)
        if not connection:
            raise Exception("Google Drive connection not found")
        
        # Get file metadata from download_metadata
        record_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "connection_id": connection["id"],
            "google_file_id": file_id,
            "google_file_name": download_metadata["original_name"],
            "google_mime_type": download_metadata["original_mime"],
            "google_file_size": download_metadata.get("file_size"),
            "sync_status": "imported",
            "last_imported_at": datetime.utcnow().isoformat(),
            "import_categoria_id": categoria_id,
            "import_tipo_demanda": tipo_demanda
        }
        
        # Upsert record
        supabase_admin.table("google_drive_documents")\
            .upsert(record_data, on_conflict="user_id,google_file_id")\
            .execute()
        
        print(f"✅ Saved Google Drive document record for {filename}")
        
    except Exception as e:
        print(f"⚠️ Error saving Google Drive document record: {e}")

async def update_google_drive_document_status(
    user_id: str,
    file_id: str,
    status: str,
    error_message: str = None
):
    """Update Google Drive document status"""
    try:
        from supabase_integration import supabase_admin
        
        update_data = {
            "sync_status": status,
            "last_sync_attempt_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if error_message:
            update_data["sync_error_message"] = error_message
        
        supabase_admin.table("google_drive_documents")\
            .update(update_data)\
            .eq("user_id", user_id)\
            .eq("google_file_id", file_id)\
            .execute()
        
    except Exception as e:
        print(f"⚠️ Error updating document status: {e}")

@router.get("/import-history")
async def get_import_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200)
):
    """Get import history for user"""
    try:
        from supabase_integration import supabase_admin
        
        result = supabase_admin.table("google_drive_documents")\
            .select("*")\
            .eq("user_id", current_user.id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return {
            "success": True,
            "history": result.data or [],
            "total": len(result.data or [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting import history: {e}")

# ================== NEW ENDPOINTS FOR SAVING FILES ==================

class SaveFileRequest(BaseModel):
    file_name: str
    file_content: str  # Base64 encoded content
    folder_id: Optional[str] = None
    mime_type: str = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

class CreateFolderRequest(BaseModel):
    folder_name: str
    parent_folder_id: Optional[str] = None

@router.post("/save-file")
async def save_file_to_google_drive(
    request: SaveFileRequest,
    current_user: User = Depends(get_current_user)
):
    """Save a file to Google Drive"""
    try:
        import base64
        
        # Get user credentials
        credentials = await get_user_credentials(current_user.id)
        
        # Decode file content
        try:
            file_content = base64.b64decode(request.file_content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 content: {e}")
        
        # Upload file to Google Drive
        result = await google_drive_service.create_file(
            credentials=credentials,
            file_name=request.file_name,
            file_content=file_content,
            parent_folder_id=request.folder_id,
            mime_type=request.mime_type
        )
        
        return {
            "success": True,
            "message": f"Archivo '{request.file_name}' guardado en Google Drive exitosamente",
            "file_id": result["id"],
            "file_name": result["name"],
            "web_view_link": result.get("webViewLink"),
            "created_time": result.get("createdTime")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error saving file to Google Drive: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {e}")

@router.post("/create-folder")
async def create_folder_in_google_drive(
    request: CreateFolderRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new folder in Google Drive"""
    try:
        # Get user credentials
        credentials = await get_user_credentials(current_user.id)
        
        # Create folder in Google Drive
        result = await google_drive_service.create_folder(
            credentials=credentials,
            folder_name=request.folder_name,
            parent_folder_id=request.parent_folder_id
        )
        
        return {
            "success": True,
            "message": f"Carpeta '{request.folder_name}' creada exitosamente",
            "folder_id": result["id"],
            "folder_name": result["name"],
            "web_view_link": result.get("webViewLink"),
            "created_time": result.get("createdTime")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating folder in Google Drive: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating folder: {e}")

@router.get("/folders")
async def get_folders(
    current_user: User = Depends(get_current_user),
    parent_id: Optional[str] = Query(None, description="Parent folder ID (root if not specified)"),
    search: Optional[str] = Query(None, description="Search query for folder names")
):
    """Get list of folders for folder picker"""
    try:
        # Get user credentials
        credentials = await get_user_credentials(current_user.id)
        
        # Get folders from Google Drive
        folders = await google_drive_service.get_folder_contents(
            credentials=credentials,
            folder_id=parent_id,
            folders_only=True,
            search_query=search
        )
        
        # Get breadcrumb for navigation
        breadcrumb = []
        if parent_id:
            breadcrumb = await google_drive_service._get_folder_breadcrumb(
                google_drive_service._get_service(credentials), 
                parent_id
            )
        else:
            breadcrumb = [{'id': 'root', 'name': 'Mi unidad'}]
        
        return {
            "success": True,
            "folders": folders,
            "breadcrumb": breadcrumb,
            "total": len(folders)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting folders: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting folders: {e}") 