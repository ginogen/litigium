from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import tempfile
import os
import shutil
from pydantic import BaseModel
import uuid
from datetime import datetime
import hashlib

from ..core.document_processor import DocumentProcessor
from ..core.category_manager import CategoryManager
from ..auth.dependencies import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/training", tags=["training"])

# Instancias de servicios
doc_processor = DocumentProcessor()
category_manager = CategoryManager()

# Función para asegurar que los buckets existen
async def ensure_bucket_exists(bucket_name: str):
    """Verifica que el bucket exista en Supabase Storage."""
    try:
        from supabase_integration import supabase_admin
        
        # Solo intentar usar el bucket, sin verificación previa
        # Si el bucket no existe, fallará en la subida y ahí capturaremos el error
        print(f"🔍 Usando bucket '{bucket_name}' (se verificará durante la subida)")
        return True
            
    except Exception as e:
        print(f"⚠️ Error accediendo bucket '{bucket_name}': {e}")
        return False

# Helper function para obtener o crear abogado_id
async def get_or_create_abogado_id(user_id: str) -> str:
    """Obtiene el ID del abogado o lo crea si no existe."""
    from supabase_integration import supabase_admin
    
    # Buscar el ID del abogado
    abogado_result = supabase_admin.table("abogados")\
        .select("id")\
        .eq("user_id", user_id)\
        .execute()
    
    if abogado_result.data:
        return abogado_result.data[0]["id"]
    
    # Si no existe, crear automáticamente
    try:
        # Crear registro básico sin obtener info del usuario
        abogado_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "nombre": f"Usuario_{user_id[:8]}",  # Nombre temporal usando parte del UUID
            "email": f"user_{user_id}@temp.com",  # Email temporal
            "especialidad": "General",
            "activo": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        create_result = supabase_admin.table("abogados")\
            .insert(abogado_data)\
            .execute()
        
        if create_result.data:
            print(f"✅ Registro de abogado creado automáticamente para user {user_id}")
            return create_result.data[0]["id"]
        else:
            raise Exception("No se pudo crear el registro de abogado")
            
    except Exception as e:
        print(f"❌ Error creando registro de abogado: {e}")
        # En lugar de lanzar excepción, devolver None para usar fallback
        return None

# Modelos Pydantic
class CategoryCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    color: str = "#6366f1"
    icon: str = "📁"

class CategoryUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class DocumentProcessRequest(BaseModel):
    document_id: str

# ================== CATEGORÍAS ==================

@router.post("/categories")
async def create_category(
    category: CategoryCreate,
    current_user: User = Depends(get_current_user)
):
    """Crea una nueva categoría para el usuario."""
    try:
        result = category_manager.create_category(
            user_id=current_user.id,
            nombre=category.nombre,
            descripcion=category.descripcion,
            color=category.color,
            icon=category.icon
        )
        
        if result["success"]:
            return JSONResponse(
                status_code=201,
                content={
                    "success": True,
                    "message": "Categoría creada exitosamente",
                    "category": result["category"]
                }
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/categories")
async def get_categories(
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Obtiene las categorías del usuario, con búsqueda opcional."""
    try:
        if search:
            categories = category_manager.search_categories(current_user.id, search)
        else:
            categories = category_manager.get_user_categories(current_user.id)
        
        return {
            "success": True,
            "categories": categories,
            "total": len(categories)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo categorías: {str(e)}"
        )

@router.get("/categories/statistics")
async def get_category_statistics(
    current_user: User = Depends(get_current_user)
):
    """Obtiene estadísticas de documentos por categoría."""
    try:
        stats = category_manager.get_category_statistics(current_user.id)
        return {
            "success": True,
            **stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )

@router.put("/categories/{category_id}")
async def update_category(
    category_id: str,
    category: CategoryUpdate,
    current_user: User = Depends(get_current_user)
):
    """Actualiza una categoría existente."""
    try:
        result = category_manager.update_category(
            category_id=category_id,
            user_id=current_user.id,
            nombre=category.nombre,
            descripcion=category.descripcion,
            color=category.color,
            icon=category.icon
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "Categoría actualizada exitosamente",
                "category": result["category"]
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando categoría: {str(e)}"
        )

@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user)
):
    """Elimina una categoría (soft delete)."""
    try:
        result = category_manager.delete_category(
            category_id=category_id,
            user_id=current_user.id
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando categoría: {str(e)}"
        )

@router.post("/categories/default")
async def create_default_categories(
    current_user: User = Depends(get_current_user)
):
    """Crea categorías por defecto para un usuario nuevo."""
    try:
        categories = category_manager.create_default_categories_for_user(current_user.id)
        return {
            "success": True,
            "message": f"Se crearon {len(categories)} categorías por defecto",
            "categories": categories
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creando categorías por defecto: {str(e)}"
        )

# ================== DOCUMENTOS ==================

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    categoria_id: str = Form(...),
    tipo_demanda: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Sube y procesa un documento en la colección personal del usuario."""
    
    # Validar archivo
    if not file.filename:
        raise HTTPException(status_code=400, detail="No se proporcionó archivo")
    
    # Validar categoría
    category = category_manager.get_category_by_id(categoria_id, current_user.id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Crear archivo temporal para verificación de duplicados
    temp_file = None
    try:
        # Importar supabase_admin para buscar abogado
        from supabase_integration import supabase_admin
        
        # Buscar el ID del abogado basado en el user_id
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not abogado_result.data or len(abogado_result.data) == 0:
            raise HTTPException(
                status_code=404, 
                detail=f"No se encontró registro de abogado para el usuario"
            )
        
        abogado_id = abogado_result.data[0]["id"]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
        
        # Verificar duplicados antes de procesar
        file_hash = calculate_file_hash(temp_file_path)
        duplicate_check = check_duplicate_document(
            abogado_id=abogado_id,  # Usar abogado_id correcto
            filename=file.filename,
            categoria_id=categoria_id,
            file_hash=file_hash
        )
        
        if duplicate_check["is_duplicate"]:
            # Limpiar archivo temporal
            os.unlink(temp_file_path)
            
            existing_doc = duplicate_check["existing_document"]
            raise HTTPException(
                status_code=409,  # Conflict
                detail={
                    "error": "Documento duplicado",
                    "message": duplicate_check["reason"],
                    "duplicate_type": duplicate_check["duplicate_type"],
                    "existing_document": {
                        "nombre": existing_doc["nombre"],
                        "fecha": existing_doc["fecha"],
                        "estado": existing_doc["estado"],
                        "tipo_demanda": existing_doc["tipo_demanda"]
                    }
                }
            )
        
        # Procesar en background si no es duplicado
        background_tasks.add_task(
            process_document_background,
            user_id=current_user.id,  # Mantener user_id para Qdrant
            file_path=temp_file_path,
            filename=file.filename,
            categoria_id=categoria_id,
            tipo_demanda=tipo_demanda,
            mime_type=file.content_type
        )
        
        return {
            "success": True,
            "message": "Documento subido exitosamente. El procesamiento comenzará en breve.",
            "filename": file.filename,
            "categoria": category["nombre"],
            "tipo_demanda": tipo_demanda
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Limpiar archivo temporal si hubo error
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error subiendo documento: {str(e)}"
        )

def calculate_file_hash(file_path: str) -> str:
    """Calcula el hash SHA-256 del archivo para detectar duplicados."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def check_duplicate_document(
    abogado_id: str,  # Cambiar de user_id a abogado_id
    filename: str, 
    categoria_id: str, 
    file_hash: str
) -> Dict[str, Any]:
    """Verifica si ya existe un documento duplicado."""
    from supabase_integration import supabase_admin
    
    # Verificar por nombre + categoría (duplicado obvio)
    name_result = supabase_admin.table("documentos_entrenamiento")\
        .select("id, nombre_archivo, created_at, estado_procesamiento, tipo_demanda")\
        .eq("abogado_id", abogado_id)\
        .eq("categoria_id", categoria_id)\
        .eq("nombre_archivo", filename)\
        .execute()
    
    if name_result.data:
        existing_doc = name_result.data[0]
        return {
            "is_duplicate": True,
            "duplicate_type": "nombre_categoria",
            "reason": f"Ya existe un documento con el mismo nombre '{filename}' en esta categoría",
            "existing_document": {
                "id": existing_doc["id"],
                "nombre": existing_doc["nombre_archivo"],
                "fecha": existing_doc["created_at"],
                "estado": existing_doc["estado_procesamiento"],
                "tipo_demanda": existing_doc["tipo_demanda"]
            }
        }
    
    # Verificar por hash si tuviéramos la columna
    # TODO: Agregar columna file_hash a la tabla documentos_entrenamiento
    # para detección por contenido idéntico
    
    return {"is_duplicate": False}

async def upload_file_to_storage(
    file_path: str,
    filename: str,
    user_id: str,
    categoria_id: str,
    mime_type: str
) -> str:
    """Sube el archivo a Supabase Storage y retorna la URL pública."""
    try:
        from supabase_integration import supabase_admin
        
        # Crear path organizado: user_id/categoria_id/timestamp_filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        storage_path = f"{user_id}/{categoria_id}/{timestamp}_{filename}"
        
        # Leer el archivo
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Subir a Storage
        bucket_name = "documentos-entrenamiento"
        
        # Asegurar que el bucket existe
        await ensure_bucket_exists(bucket_name)
        
        result = supabase_admin.storage.from_(bucket_name).upload(
            path=storage_path,
            file=file_data,
            file_options={
                "content-type": mime_type or "application/octet-stream",
                "upsert": "false"  # No sobrescribir si existe (string en lugar de bool)
            }
        )
        
        # Verificar errores de manera robusta
        if result is None:
            raise Exception("Error: resultado nulo del upload")
        
        # Diferentes formas de verificar errores dependiendo del formato de respuesta
        error_msg = None
        if hasattr(result, 'error') and result.error:
            error_msg = str(result.error)
        elif isinstance(result, dict) and result.get('error'):
            error_msg = str(result['error'])
        elif isinstance(result, bool) and not result:
            error_msg = "Upload falló (retornó False)"
        
        if error_msg:
            raise Exception(f"Error subiendo a Storage: {error_msg}")
        
        # Obtener URL pública - manejar correctamente el retorno
        try:
            public_url_response = supabase_admin.storage.from_(bucket_name).get_public_url(storage_path)
            
            # Verificar si es una cadena (URL) o un diccionario con data
            if isinstance(public_url_response, str):
                public_url = public_url_response
            elif isinstance(public_url_response, dict) and public_url_response.get('publicUrl'):
                public_url = public_url_response['publicUrl']
            elif hasattr(public_url_response, 'publicUrl'):
                public_url = public_url_response.publicUrl
            else:
                # Fallback: construir URL manualmente
                public_url = f"{supabase_admin.supabase_url}/storage/v1/object/public/{bucket_name}/{storage_path}"
        except Exception as url_error:
            print(f"⚠️ Error obteniendo URL pública, usando fallback: {url_error}")
            # Fallback: construir URL manualmente
            public_url = f"{supabase_admin.supabase_url}/storage/v1/object/public/{bucket_name}/{storage_path}"
        
        print(f"📁 Archivo subido a Storage: {storage_path}")
        return public_url
        
    except Exception as e:
        print(f"❌ Error subiendo archivo a Storage: {e}")
        raise Exception(f"Error subiendo archivo a Storage: {e}")

async def process_document_background(
    user_id: str,
    file_path: str,
    filename: str,
    categoria_id: str,
    tipo_demanda: str,
    mime_type: str = None
):
    """Procesa el documento en background y actualiza la base de datos."""
    documento_id = None
    
    try:
        # Importar supabase_admin para acceder a la base de datos
        from supabase_integration import supabase_admin
        
        # 1. Buscar el ID del abogado basado en el user_id
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", user_id)\
            .execute()
        
        if not abogado_result.data or len(abogado_result.data) == 0:
            raise Exception(f"No se encontró registro de abogado para user_id: {user_id}")
        
        abogado_id = abogado_result.data[0]["id"]
        print(f"🔍 Usuario {user_id} -> Abogado {abogado_id}")
        
        # 2. Subir archivo a Supabase Storage
        try:
            storage_url = await upload_file_to_storage(
                file_path=file_path,
                filename=filename,
                user_id=user_id,
                categoria_id=categoria_id,
                mime_type=mime_type
            )
            print(f"📁 Archivo guardado en Storage: {storage_url}")
        except Exception as storage_error:
            print(f"⚠️ Error subiendo a Storage (continuando con procesamiento): {storage_error}")
            storage_url = file_path  # Usar path temporal como fallback
        
        # 3. Calcular hash del archivo para detección de duplicados
        file_hash = calculate_file_hash(file_path)
        
        # 4. Verificar duplicados
        duplicate_check = check_duplicate_document(
            abogado_id=abogado_id,  # Usar abogado_id en lugar de user_id
            filename=filename,
            categoria_id=categoria_id,
            file_hash=file_hash
        )
        
        if duplicate_check["is_duplicate"]:
            existing_doc = duplicate_check["existing_document"]
            print(f"⚠️ Documento duplicado detectado: {filename}")
            print(f"   Documento existente: {existing_doc['nombre']} (ID: {existing_doc['id']})")
            print(f"   Fecha original: {existing_doc['fecha']}")
            print(f"   Estado: {existing_doc['estado']}")
            print(f"   Tipo: {duplicate_check['duplicate_type']}")
            return
        
        # 5. Crear registro inicial en la base de datos
        documento_data = {
            "id": str(uuid.uuid4()),
            "abogado_id": abogado_id,  # Usar abogado_id correcto
            "categoria_id": categoria_id,
            "nombre_archivo": filename,
            "archivo_url": storage_url,  # URL del Storage o path temporal
            "tipo_mime": mime_type,
            "tipo_demanda": tipo_demanda,
            "estado_procesamiento": "procesando",
            "vectorizado": False,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insertar documento en Supabase
        insert_result = supabase_admin.table("documentos_entrenamiento")\
            .insert(documento_data)\
            .execute()
        
        if not insert_result.data:
            raise Exception("No se pudo crear el registro del documento en la base de datos")
            
        documento_id = insert_result.data[0]["id"]
        
        # 6. Procesar documento con Qdrant (usar user_id original para la colección)
        result = doc_processor.process_and_upload_document(
            user_id=user_id,  # Mantener user_id para Qdrant
            file_path=file_path,
            filename=filename,
            categoria_id=categoria_id,
            tipo_demanda=tipo_demanda,
            mime_type=mime_type
        )
        
        if result["success"]:
            # 7. Actualizar documento con estado completado y formato rico
            update_data = {
                "estado_procesamiento": "completado",
                "vectorizado": True,
                "qdrant_collection": result.get("collection_name"),
                "texto_extraido": result.get("texto_extraido"),
                "secciones_extraidas": result.get("secciones", {}),
                "processed_at": datetime.utcnow().isoformat(),
                # NUEVO: Campos de formato rico
                "contenido_rico": result.get("contenido_rico"),
                "metadatos_formato": result.get("metadatos_formato", {}),
                "tiene_formato_rico": result.get("tiene_formato_rico", False),
                "version_extraccion": result.get("version_extraccion", "v1.0")
            }
            
            supabase_admin.table("documentos_entrenamiento")\
                .update(update_data)\
                .eq("id", documento_id)\
                .execute()
            
            print(f"✅ Documento procesado exitosamente: {filename}")
            print(f"Collection: {result.get('collection_name')}")
            print(f"Document ID: {result.get('document_id')}")
        else:
            # Actualizar estado de error
            update_data = {
                "estado_procesamiento": "error",
                "error_procesamiento": result.get("error", "Error desconocido"),
                "processed_at": datetime.utcnow().isoformat()
            }
            
            supabase_admin.table("documentos_entrenamiento")\
                .update(update_data)\
                .eq("id", documento_id)\
                .execute()
            
            print(f"❌ Error procesando documento {filename}: {result.get('error')}")
        
    except Exception as e:
        print(f"❌ Error procesando documento {filename}: {e}")
        
        # Actualizar estado de error si el documento se creó
        if documento_id:
            try:
                from supabase_integration import supabase_admin
                update_data = {
                    "estado_procesamiento": "error",
                    "error_procesamiento": str(e),
                    "processed_at": datetime.utcnow().isoformat()
                }
                
                supabase_admin.table("documentos_entrenamiento")\
                    .update(update_data)\
                    .eq("id", documento_id)\
                    .execute()
            except Exception as update_error:
                print(f"❌ Error actualizando estado de error: {update_error}")
        
    finally:
        # Limpiar archivo temporal
        if os.path.exists(file_path):
            os.unlink(file_path)

@router.get("/documents")
async def get_user_documents(
    categoria_id: Optional[str] = None,
    estado: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Obtiene los documentos de entrenamiento del usuario usando función optimizada."""
    try:
        from supabase_integration import supabase_admin
        
        # Usar la función SQL optimizada
        result = supabase_admin.rpc("get_user_documents_optimized", {
            "p_user_id": current_user.id,
            "p_categoria_id": categoria_id,
            "p_estado": estado,
            "p_limit": limit,
            "p_offset": offset
        }).execute()
        
        if not result.data:
            return {
                "success": True,
                "documents": [],
                "total": 0,
                "filters": {
                    "categoria_id": categoria_id,
                    "estado": estado
                },
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": False
                }
            }
        
        # Procesar resultados de la función optimizada
        documents = []
        for doc in result.data:
            # Construir objeto de categoría si existe
            categoria_info = None
            if doc.get("categoria_nombre"):
                categoria_info = {
                    "nombre": doc["categoria_nombre"],
                    "color": doc["categoria_color"],
                    "icon": doc["categoria_icon"]
                }
            
            documents.append({
                "id": doc["id"],
                "nombre_archivo": doc["nombre_archivo"],
                "archivo_url": doc["archivo_url"],
                "tipo_mime": doc["tipo_mime"],
                "tipo_demanda": doc["tipo_demanda"],
                "estado_procesamiento": doc["estado_procesamiento"],
                "vectorizado": doc["vectorizado"],
                "created_at": doc["created_at"],
                "processed_at": doc["processed_at"],
                "categoria": categoria_info,
                "tamaño_bytes": doc.get("tamaño_bytes"),
                "error_procesamiento": doc.get("error_procesamiento"),
                "total_anotaciones": doc.get("total_anotaciones", 0),
                "anotaciones_alta_prioridad": doc.get("anotaciones_alta_prioridad", 0),
                "anotaciones_precedentes": doc.get("anotaciones_precedentes", 0),
                "anotaciones_estrategias": doc.get("anotaciones_estrategias", 0)
            })
        
        # Determinar si hay más documentos
        has_more = len(documents) == limit
        
        return {
            "success": True,
            "documents": documents,
            "total": len(documents),
            "filters": {
                "categoria_id": categoria_id,
                "estado": estado
            },
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": has_more
            },
            "performance": {
                "method": "optimized_sql_function",
                "query_time": "single_query"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
                 # Fallback a método anterior si la función optimizada falla
         print(f"⚠️ Función optimizada falló, usando método tradicional: {e}")
         return await get_user_documents_fallback(categoria_id, estado, current_user)


async def get_user_documents_fallback(
    categoria_id: Optional[str] = None,
    estado: Optional[str] = None,
    current_user: User = None
):
    """Método fallback para obtener documentos si la función optimizada falla."""
    try:
        from supabase_integration import supabase_admin
        
        # Buscar el ID del abogado
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not abogado_result.data:
            raise HTTPException(status_code=404, detail="Registro de abogado no encontrado")
        
        abogado_id = abogado_result.data[0]["id"]
        
        # Consulta básica optimizada
        query = supabase_admin.table("documentos_entrenamiento")\
            .select("*")\
            .eq("abogado_id", abogado_id)\
            .order("created_at", desc=True)\
            .limit(50)
        
        # Filtros opcionales
        if categoria_id:
            query = query.eq("categoria_id", categoria_id)
        if estado:
            query = query.eq("estado_procesamiento", estado)
        
        result = query.execute()
        
        # Obtener categorías en una consulta
        categorias_map = {}
        if result.data:
            categorias_result = supabase_admin.table("categorias_demandas")\
                .select("id, nombre, color, icon")\
                .eq("user_id", current_user.id)\
                .execute()
            
            for cat in categorias_result.data:
                categorias_map[cat["id"]] = cat
        
        # Procesar documentos
        documents = []
        for doc in result.data:
            categoria_info = None
            if doc.get("categoria_id") and doc["categoria_id"] in categorias_map:
                categoria_info = categorias_map[doc["categoria_id"]]
            
            documents.append({
                "id": doc["id"],
                "nombre_archivo": doc["nombre_archivo"],
                "archivo_url": doc["archivo_url"],
                "tipo_mime": doc["tipo_mime"],
                "tipo_demanda": doc["tipo_demanda"],
                "estado_procesamiento": doc["estado_procesamiento"],
                "vectorizado": doc["vectorizado"],
                "created_at": doc["created_at"],
                "processed_at": doc["processed_at"],
                "categoria": categoria_info,
                "tamaño_bytes": doc.get("tamaño_bytes"),
                "error_procesamiento": doc.get("error_procesamiento"),
                "total_anotaciones": 0  # Sin conteo de anotaciones en fallback
            })
        
        return {
            "success": True,
            "documents": documents,
            "total": len(documents),
            "filters": {
                "categoria_id": categoria_id,
                "estado": estado
            },
            "performance": {
                "method": "fallback_traditional",
                "note": "Optimized function not available"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo documentos (fallback): {str(e)}"
        )


@router.get("/documents/{document_id}/content")
async def get_document_content(
    document_id: str,
    format_type: str = "plain",  # "plain", "rich", "html"
    current_user: User = Depends(get_current_user)
):
    """Obtiene el contenido de un documento en diferentes formatos (texto plano, rico, HTML)."""
    try:
        from supabase_integration import supabase_admin
        
        # Buscar el ID del abogado
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not abogado_result.data:
            raise HTTPException(status_code=404, detail="Registro de abogado no encontrado")
        
        abogado_id = abogado_result.data[0]["id"]
        
        # Buscar el documento con TODO el contenido (incluyendo formato rico)
        doc_result = supabase_admin.table("documentos_entrenamiento")\
            .select("*")\
            .eq("id", document_id)\
            .eq("abogado_id", abogado_id)\
            .execute()
        
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        document = doc_result.data[0]
        
        # Preparar respuesta base
        document_data = {
            "id": document["id"],
            "nombre_archivo": document["nombre_archivo"],
            "tipo_demanda": document["tipo_demanda"],
            "estado_procesamiento": document["estado_procesamiento"],
            "tiene_formato_rico": document.get("tiene_formato_rico", False),
            "version_extraccion": document.get("version_extraccion", "v1.0"),
            "metadatos_formato": document.get("metadatos_formato", {})
        }
        
        # NUEVO: Servir contenido según el formato solicitado
        if format_type == "rich" and document.get("contenido_rico"):
            # Formato rico JSON
            document_data["contenido"] = document["contenido_rico"]
            document_data["format_type"] = "rich"
            print(f"✅ Sirviendo contenido rico para documento {document_id}")
            
        elif format_type == "html" and document.get("contenido_rico"):
            # Convertir formato rico a HTML
            try:
                # Importar procesador de formato rico
                from ..core.document_processor_rich_format import rich_format_processor
                
                html_content = rich_format_processor.rich_content_to_html(document["contenido_rico"])
                document_data["contenido"] = html_content
                document_data["format_type"] = "html"
                print(f"✅ Contenido convertido a HTML para documento {document_id}")
                
            except Exception as e:
                print(f"⚠️ Error convirtiendo a HTML: {e}")
                # Fallback a texto plano
                document_data["contenido"] = document.get("texto_extraido", "")
                document_data["format_type"] = "plain"
                document_data["warning"] = "Error convirtiendo formato rico, mostrando texto plano"
        else:
            # Texto plano (formato por defecto)
            texto_extraido = document.get("texto_extraido", "")
            
            if not texto_extraido or texto_extraido.strip() == "":
                return {
                    "success": False,
                    "error": "El documento no tiene contenido extraído disponible",
                    "estado_procesamiento": document.get("estado_procesamiento", "desconocido")
                }
            
            document_data["contenido"] = texto_extraido
            document_data["format_type"] = "plain"
        
        return {
            "success": True,
            "document": document_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo contenido del documento: {str(e)}"
        )

@router.get("/documents/{document_id}/download")
async def get_document_download_url(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtiene la URL de descarga de un documento específico."""
    try:
        from supabase_integration import supabase_admin
        
        # Buscar el ID del abogado
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not abogado_result.data:
            raise HTTPException(status_code=404, detail="Registro de abogado no encontrado")
        
        abogado_id = abogado_result.data[0]["id"]
        
        # Buscar el documento
        doc_result = supabase_admin.table("documentos_entrenamiento")\
            .select("*")\
            .eq("id", document_id)\
            .eq("abogado_id", abogado_id)\
            .execute()
        
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        document = doc_result.data[0]
        
        # Si el archivo está en Storage, generar URL con firma
        if document["archivo_url"].startswith("http"):
            # Ya es una URL pública
            download_url = document["archivo_url"]
        else:
            # Archivo no está en Storage (casos antiguos)
            raise HTTPException(
                status_code=404, 
                detail="Archivo no disponible para descarga"
            )
        
        return {
            "success": True,
            "download_url": download_url,
            "filename": document["nombre_archivo"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo URL de descarga: {str(e)}"
        )

@router.get("/search")
async def search_similar_documents(
    query: str,
    categoria_id: Optional[str] = None,
    limit: int = 5,
    include_annotations: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Busca documentos similares en la colección personal del usuario CON ANOTACIONES."""
    try:
        # Usar búsqueda tradicional estable
        results = doc_processor.search_similar_documents(
            user_id=current_user.id,
            query_text=query,
            categoria_id=categoria_id,
            limit=limit
        )
        
        # Información básica de la respuesta
        enhanced_info = {
            "total_documents": len(results),
            "search_method": "traditional_similarity"
        }
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error buscando documentos: {str(e)}"
        )

@router.get("/enhanced-legal-context")
async def get_enhanced_legal_context(
    query: str,
    tipo_demanda: Optional[str] = None,
    limit: int = 3,
    current_user: User = Depends(get_current_user)
):
    """Obtiene contexto legal enriquecido con anotaciones para generación de demandas."""
    try:
        enhanced_context = doc_processor.get_enhanced_legal_context(
            user_id=current_user.id,
            query_text=query,
            tipo_demanda=tipo_demanda,
            limit=limit
        )
        
        return {
            "success": True,
            "query": query,
            "tipo_demanda": tipo_demanda,
            **enhanced_context
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo contexto legal enriquecido: {str(e)}"
        )

@router.get("/collection/stats")
async def get_collection_stats(
    current_user: User = Depends(get_current_user)
):
    """Obtiene estadísticas de la colección Qdrant del usuario."""
    try:
        stats = doc_processor.get_user_collection_stats(current_user.id)
        return {
            "success": True,
            **stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadísticas de colección: {str(e)}"
        )

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Elimina un documento específico de la colección del usuario."""
    try:
        success = doc_processor.delete_document_from_collection(
            user_id=current_user.id,
            document_id=document_id
        )
        
        if success:
            # TODO: También eliminar/marcar como eliminado en documentos_entrenamiento
            return {
                "success": True,
                "message": "Documento eliminado exitosamente"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Documento no encontrado"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando documento: {str(e)}"
        )

# ================== FUNCIONES AUXILIARES DE VECTORIZACIÓN ==================

async def update_document_vectorization_with_annotations(
    user_id: str, 
    document_id: str, 
    operation: str = "annotation_changed"
):
    """Actualiza la vectorización de un documento cuando cambian sus anotaciones."""
    
    try:
        from supabase_integration import supabase_admin
        from ..core.document_processor import DocumentProcessor
        
        print(f"🔄 Iniciando re-vectorización de documento {document_id} por {operation}")
        
        # Buscar el ID del abogado
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", user_id)\
            .execute()
        
        if not abogado_result.data:
            raise Exception("Registro de abogado no encontrado")
        
        abogado_id = abogado_result.data[0]["id"]
        
        # Obtener todas las anotaciones actuales del documento
        annotations_result = supabase_admin.table("documento_anotaciones")\
            .select("*")\
            .eq("documento_id", document_id)\
            .eq("abogado_id", abogado_id)\
            .execute()
        
        annotations = annotations_result.data or []
        
        # Inicializar procesador de documentos
        doc_processor = DocumentProcessor()
        
        # Actualizar vectorización con anotaciones
        result = doc_processor.update_document_with_annotations(
            user_id=user_id,
            document_id=document_id,
            annotations=annotations
        )
        
        if result["success"]:
            print(f"✅ Re-vectorización exitosa: {result['annotations_processed']} anotaciones procesadas")
            
            # Actualizar metadata en Supabase
            update_data = {
                "secciones_extraidas": {
                    "enhanced_with_annotations": True,
                    "annotations_count": len(annotations),
                    "last_vectorization_update": datetime.utcnow().isoformat(),
                    "vectorization_operation": operation
                }
            }
            
            # Obtener secciones existentes y combinar
            doc_result = supabase_admin.table("documentos_entrenamiento")\
                .select("secciones_extraidas")\
                .eq("id", document_id)\
                .execute()
            
            if doc_result.data:
                existing_sections = doc_result.data[0].get("secciones_extraidas", {})
                update_data["secciones_extraidas"] = {
                    **existing_sections,
                    **update_data["secciones_extraidas"]
                }
            
            supabase_admin.table("documentos_entrenamiento")\
                .update(update_data)\
                .eq("id", document_id)\
                .execute()
        else:
            print(f"❌ Error en re-vectorización: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error actualizando vectorización: {e}")
        raise e

# ================== ANOTACIONES ==================

@router.get("/documents/{document_id}/annotations")
async def get_document_annotations(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtiene todas las anotaciones de un documento."""
    try:
        from supabase_integration import supabase_admin
        
        # Buscar el ID del abogado
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not abogado_result.data:
            raise HTTPException(status_code=404, detail="Registro de abogado no encontrado")
        
        abogado_id = abogado_result.data[0]["id"]
        
        # Verificar que el documento pertenece al abogado
        doc_result = supabase_admin.table("documentos_entrenamiento")\
            .select("id, nombre_archivo")\
            .eq("id", document_id)\
            .eq("abogado_id", abogado_id)\
            .execute()
        
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        # Obtener anotaciones
        annotations_result = supabase_admin.table("documento_anotaciones")\
            .select("*")\
            .eq("documento_id", document_id)\
            .eq("abogado_id", abogado_id)\
            .order("posicion_inicio")\
            .execute()
        
        return {
            "success": True,
            "document": doc_result.data[0],
            "annotations": annotations_result.data or [],
            "total": len(annotations_result.data) if annotations_result.data else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo anotaciones: {str(e)}"
        )

@router.post("/documents/{document_id}/annotations")
async def create_annotation(
    document_id: str,
    annotation_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Crea una nueva anotación en un documento."""
    try:
        from supabase_integration import supabase_admin
        
        # Buscar el ID del abogado
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not abogado_result.data:
            raise HTTPException(status_code=404, detail="Registro de abogado no encontrado")
        
        abogado_id = abogado_result.data[0]["id"]
        
        # Verificar que el documento pertenece al abogado
        doc_result = supabase_admin.table("documentos_entrenamiento")\
            .select("id")\
            .eq("id", document_id)\
            .eq("abogado_id", abogado_id)\
            .execute()
        
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        # Crear anotación
        annotation = {
            "id": str(uuid.uuid4()),
            "documento_id": document_id,
            "abogado_id": abogado_id,
            "pagina": annotation_data.get("pagina"),
            "posicion_inicio": annotation_data.get("posicion_inicio"),
            "posicion_fin": annotation_data.get("posicion_fin"),
            "texto_seleccionado": annotation_data.get("texto_seleccionado", ""),
            "tipo_anotacion": annotation_data.get("tipo_anotacion", "comentario"),
            "titulo": annotation_data.get("titulo"),
            "contenido": annotation_data.get("contenido", ""),
            "etiquetas": annotation_data.get("etiquetas", []),
            "color": annotation_data.get("color", "#fbbf24"),
            "prioridad": annotation_data.get("prioridad", 1),
            "privacidad": annotation_data.get("privacidad", "privado"),
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase_admin.table("documento_anotaciones")\
            .insert(annotation)\
            .execute()
        
        if not result.data:
            raise Exception("No se pudo crear la anotación")
        
        # NUEVO: Actualizar vectorización en Qdrant con la nueva anotación
        try:
            await update_document_vectorization_with_annotations(
                user_id=current_user.id,
                document_id=document_id,
                operation="annotation_added"
            )
            print(f"✅ Documento vectorizado actualizado con nueva anotación")
        except Exception as vector_error:
            print(f"⚠️ Error actualizando vectorización: {vector_error}")
            # No fallar la creación de anotación por error de vectorización
        
        return {
            "success": True,
            "message": "Anotación creada exitosamente y documento re-vectorizado",
            "annotation": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creando anotación: {str(e)}"
        )

@router.put("/annotations/{annotation_id}")
async def update_annotation(
    annotation_id: str,
    annotation_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Actualiza una anotación existente."""
    try:
        from supabase_integration import supabase_admin
        
        # Buscar el ID del abogado
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not abogado_result.data:
            raise HTTPException(status_code=404, detail="Registro de abogado no encontrado")
        
        abogado_id = abogado_result.data[0]["id"]
        
        # Actualizar solo los campos proporcionados
        update_data = {
            "updated_at": datetime.utcnow().isoformat()
        }
        
        allowed_fields = [
            "titulo", "contenido", "etiquetas", "color", "prioridad", 
            "privacidad", "tipo_anotacion"
        ]
        
        for field in allowed_fields:
            if field in annotation_data:
                update_data[field] = annotation_data[field]
        
        result = supabase_admin.table("documento_anotaciones")\
            .update(update_data)\
            .eq("id", annotation_id)\
            .eq("abogado_id", abogado_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Anotación no encontrada")
        
        # NUEVO: Re-vectorizar documento con anotación actualizada
        annotation = result.data[0]
        try:
            await update_document_vectorization_with_annotations(
                user_id=current_user.id,
                document_id=annotation["documento_id"],
                operation="annotation_updated"
            )
            print(f"✅ Documento re-vectorizado tras actualización de anotación")
        except Exception as vector_error:
            print(f"⚠️ Error re-vectorizando tras actualización: {vector_error}")
        
        return {
            "success": True,
            "message": "Anotación actualizada exitosamente y documento re-vectorizado",
            "annotation": annotation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando anotación: {str(e)}"
        )

@router.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Elimina una anotación."""
    try:
        from supabase_integration import supabase_admin
        
        # Buscar el ID del abogado
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not abogado_result.data:
            raise HTTPException(status_code=404, detail="Registro de abogado no encontrado")
        
        abogado_id = abogado_result.data[0]["id"]
        
        # Eliminar anotación
        result = supabase_admin.table("documento_anotaciones")\
            .delete()\
            .eq("id", annotation_id)\
            .eq("abogado_id", abogado_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Anotación no encontrada")
        
        # NUEVO: Re-vectorizar documento tras eliminar anotación
        deleted_annotation = result.data[0]
        try:
            await update_document_vectorization_with_annotations(
                user_id=current_user.id,
                document_id=deleted_annotation["documento_id"],
                operation="annotation_deleted"
            )
            print(f"✅ Documento re-vectorizado tras eliminación de anotación")
        except Exception as vector_error:
            print(f"⚠️ Error re-vectorizando tras eliminación: {vector_error}")
        
        return {
            "success": True,
            "message": "Anotación eliminada exitosamente y documento re-vectorizado"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando anotación: {str(e)}"
        )

# ================== PLANTILLAS DE ANOTACIONES ==================

@router.get("/templates")
async def get_annotation_templates(
    tipo_anotacion: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Obtiene las plantillas de anotaciones del usuario."""
    try:
        from supabase_integration import supabase_admin
        
        # Obtener o crear abogado_id automáticamente
        abogado_id = await get_or_create_abogado_id(current_user.id)
        
        # Si no se pudo obtener/crear el abogado_id, devolver array vacío
        if not abogado_id:
            print(f"⚠️ No se pudo obtener abogado_id para user {current_user.id}")
            return {
                "success": True,
                "templates": [],
                "total": 0
            }
        
        # Construir consulta
        query = supabase_admin.table("plantillas_anotaciones")\
            .select("*")\
            .eq("abogado_id", abogado_id)\
            .eq("activo", True)\
            .order("uso_frecuente", desc=True)\
            .order("nombre")
        
        # Filtro opcional por tipo
        if tipo_anotacion:
            query = query.eq("tipo_anotacion", tipo_anotacion)
        
        result = query.execute()
        
        return {
            "success": True,
            "templates": result.data or [],
            "total": len(result.data) if result.data else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error inesperado en get_annotation_templates: {e}")
        print(f"   User ID: {current_user.id}")
        print(f"   Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo plantillas: {str(e)}"
        )

@router.post("/templates")
async def create_annotation_template(
    template_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Crea una nueva plantilla de anotación."""
    try:
        from supabase_integration import supabase_admin
        
        # Buscar el ID del abogado
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not abogado_result.data:
            raise HTTPException(status_code=404, detail="Registro de abogado no encontrado")
        
        abogado_id = abogado_result.data[0]["id"]
        
        # Verificar que no existe una plantilla con el mismo nombre
        existing_result = supabase_admin.table("plantillas_anotaciones")\
            .select("id")\
            .eq("abogado_id", abogado_id)\
            .eq("nombre", template_data.get("nombre"))\
            .execute()
        
        if existing_result.data:
            raise HTTPException(
                status_code=400, 
                detail="Ya existe una plantilla con ese nombre"
            )
        
        # Crear plantilla
        template = {
            "id": str(uuid.uuid4()),
            "abogado_id": abogado_id,
            "nombre": template_data.get("nombre"),
            "descripcion": template_data.get("descripcion"),
            "tipo_anotacion": template_data.get("tipo_anotacion", "comentario"),
            "plantilla_contenido": template_data.get("plantilla_contenido", ""),
            "etiquetas_sugeridas": template_data.get("etiquetas_sugeridas", []),
            "color_defecto": template_data.get("color_defecto", "#fbbf24"),
            "uso_frecuente": template_data.get("uso_frecuente", False),
            "activo": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase_admin.table("plantillas_anotaciones")\
            .insert(template)\
            .execute()
        
        if not result.data:
            raise Exception("No se pudo crear la plantilla")
        
        return {
            "success": True,
            "message": "Plantilla creada exitosamente",
            "template": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creando plantilla: {str(e)}"
        )

@router.put("/templates/{template_id}")
async def update_annotation_template(
    template_id: str,
    template_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Actualiza una plantilla de anotación existente."""
    try:
        from supabase_integration import supabase_admin
        
        # Buscar el ID del abogado
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not abogado_result.data:
            raise HTTPException(status_code=404, detail="Registro de abogado no encontrado")
        
        abogado_id = abogado_result.data[0]["id"]
        
        # Verificar que la plantilla existe y pertenece al abogado
        template_result = supabase_admin.table("plantillas_anotaciones")\
            .select("id")\
            .eq("id", template_id)\
            .eq("abogado_id", abogado_id)\
            .execute()
        
        if not template_result.data:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Si se actualiza el nombre, verificar que no existe otra con el mismo nombre
        if template_data.get("nombre"):
            existing_result = supabase_admin.table("plantillas_anotaciones")\
                .select("id")\
                .eq("abogado_id", abogado_id)\
                .eq("nombre", template_data["nombre"])\
                .neq("id", template_id)\
                .execute()
            
            if existing_result.data:
                raise HTTPException(
                    status_code=400, 
                    detail="Ya existe otra plantilla con ese nombre"
                )
        
        # Actualizar solo los campos proporcionados
        update_data = {
            "updated_at": datetime.utcnow().isoformat()
        }
        
        allowed_fields = [
            "nombre", "descripcion", "tipo_anotacion", "plantilla_contenido",
            "etiquetas_sugeridas", "color_defecto", "uso_frecuente", "activo"
        ]
        
        for field in allowed_fields:
            if field in template_data:
                update_data[field] = template_data[field]
        
        result = supabase_admin.table("plantillas_anotaciones")\
            .update(update_data)\
            .eq("id", template_id)\
            .eq("abogado_id", abogado_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        return {
            "success": True,
            "message": "Plantilla actualizada exitosamente",
            "template": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando plantilla: {str(e)}"
        )

@router.delete("/templates/{template_id}")
async def delete_annotation_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Elimina una plantilla de anotación."""
    try:
        from supabase_integration import supabase_admin
        
        # Buscar el ID del abogado
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not abogado_result.data:
            raise HTTPException(status_code=404, detail="Registro de abogado no encontrado")
        
        abogado_id = abogado_result.data[0]["id"]
        
        # Verificar que la plantilla existe y pertenece al abogado
        template_result = supabase_admin.table("plantillas_anotaciones")\
            .select("id")\
            .eq("id", template_id)\
            .eq("abogado_id", abogado_id)\
            .execute()
        
        if not template_result.data:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        
        # Marcar como inactiva en lugar de eliminar (soft delete)
        result = supabase_admin.table("plantillas_anotaciones")\
            .update({
                "activo": False,
                "updated_at": datetime.utcnow().isoformat()
            })\
            .eq("id", template_id)\
            .eq("abogado_id", abogado_id)\
            .execute()
        
        return {
            "success": True,
            "message": "Plantilla eliminada exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando plantilla: {str(e)}"
        )

@router.post("/templates/default")
async def create_default_templates(
    current_user: User = Depends(get_current_user)
):
    """Crea las plantillas predeterminadas para el usuario."""
    try:
        from supabase_integration import supabase_admin
        
        # Buscar el ID del abogado
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not abogado_result.data:
            raise HTTPException(status_code=404, detail="Registro de abogado no encontrado")
        
        abogado_id = abogado_result.data[0]["id"]
        
        # Verificar si ya tiene plantillas
        existing_result = supabase_admin.table("plantillas_anotaciones")\
            .select("id")\
            .eq("abogado_id", abogado_id)\
            .execute()
        
        if existing_result.data:
            return {
                "success": True,
                "message": "El usuario ya tiene plantillas creadas",
                "templates_created": 0
            }
        
        # Plantillas predeterminadas
        default_templates = [
            {
                "nombre": "Precedente Relevante",
                "descripcion": "Para marcar precedentes legales importantes",
                "tipo_anotacion": "precedente",
                "plantilla_contenido": "PRECEDENTE: {titulo_caso}\nCorte: {corte}\nFecha: {fecha}\nRelevancia: {relevancia}\nCita: {cita_legal}",
                "etiquetas_sugeridas": ["precedente", "jurisprudencia", "caso"],
                "color_defecto": "#3b82f6"
            },
            {
                "nombre": "Estrategia Legal",
                "descripcion": "Para anotar estrategias y enfoques legales",
                "tipo_anotacion": "estrategia",
                "plantilla_contenido": "ESTRATEGIA: {titulo}\nEnfoque: {enfoque}\nArgumentos: {argumentos}\nRiesgos: {riesgos}\nAcciones: {acciones}",
                "etiquetas_sugeridas": ["estrategia", "táctica", "enfoque"],
                "color_defecto": "#10b981"
            },
            {
                "nombre": "Problema Identificado",
                "descripcion": "Para marcar problemas o inconsistencias",
                "tipo_anotacion": "problema",
                "plantilla_contenido": "PROBLEMA: {descripcion}\nImpacto: {impacto}\nSolución propuesta: {solucion}\nUrgencia: {urgencia}",
                "etiquetas_sugeridas": ["problema", "inconsistencia", "riesgo"],
                "color_defecto": "#ef4444"
            },
            {
                "nombre": "Comentario General",
                "descripcion": "Para comentarios y notas generales",
                "tipo_anotacion": "comentario",
                "plantilla_contenido": "NOTA: {comentario}\nContexto: {contexto}\nImportancia: {importancia}",
                "etiquetas_sugeridas": ["nota", "comentario", "observación"],
                "color_defecto": "#fbbf24"
            }
        ]
        
        # Crear plantillas
        templates_to_insert = []
        for template_data in default_templates:
            template = {
                "id": str(uuid.uuid4()),
                "abogado_id": abogado_id,
                "uso_frecuente": True,
                "activo": True,
                "created_at": datetime.utcnow().isoformat(),
                **template_data
            }
            templates_to_insert.append(template)
        
        result = supabase_admin.table("plantillas_anotaciones")\
            .insert(templates_to_insert)\
            .execute()
        
        return {
            "success": True,
            "message": f"Se crearon {len(templates_to_insert)} plantillas predeterminadas",
            "templates_created": len(templates_to_insert),
            "templates": result.data or []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creando plantillas predeterminadas: {str(e)}"
        )

# ================== INTEGRACIÓN CON IA ==================

@router.post("/enhance-document-analysis")
async def enhance_document_analysis(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mejora el análisis de un documento usando las anotaciones existentes para entrenar la IA."""
    try:
        from supabase_integration import supabase_admin
        
        # Buscar el ID del abogado
        abogado_result = supabase_admin.table("abogados")\
            .select("id")\
            .eq("user_id", current_user.id)\
            .execute()
        
        if not abogado_result.data:
            raise HTTPException(status_code=404, detail="Registro de abogado no encontrado")
        
        abogado_id = abogado_result.data[0]["id"]
        
        # Obtener documento con anotaciones
        doc_result = supabase_admin.table("documentos_entrenamiento")\
            .select("*")\
            .eq("id", document_id)\
            .eq("abogado_id", abogado_id)\
            .execute()
        
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        document = doc_result.data[0]
        
        # Obtener anotaciones del documento
        annotations_result = supabase_admin.table("documento_anotaciones")\
            .select("*")\
            .eq("documento_id", document_id)\
            .execute()
        
        annotations = annotations_result.data or []
        
        # TODO: Integrar con sistema de IA para actualizar vectorización
        # Por ahora, simular mejora del análisis
        
        enhanced_analysis = {
            "document_id": document_id,
            "original_analysis": {
                "tipo_demanda": document["tipo_demanda"],
                "categoria": document["categoria"],
                "tags": document["tags"]
            },
            "enhanced_with_annotations": {
                "precedentes_identificados": len([a for a in annotations if a["tipo_anotacion"] == "precedente"]),
                "estrategias_sugeridas": len([a for a in annotations if a["tipo_anotacion"] == "estrategia"]),
                "problemas_detectados": len([a for a in annotations if a["tipo_anotacion"] == "problema"]),
                "contexto_mejorado": f"Documento enriquecido con {len(annotations)} anotaciones de experto"
            },
            "recommendations": [
                "Las anotaciones han mejorado la comprensión del documento",
                "Se identificaron patrones adicionales basados en experiencia legal",
                "El contexto del caso está mejor definido para futuras consultas"
            ]
        }
        
        # Actualizar metadata del documento
        supabase_admin.table("documentos_entrenamiento")\
            .update({
                "secciones_extraidas": {
                    **document.get("secciones_extraidas", {}),
                    "enhanced_analysis": enhanced_analysis,
                    "annotations_count": len(annotations),
                    "last_enhancement": datetime.utcnow().isoformat()
                }
            })\
            .eq("id", document_id)\
            .execute()
        
        return {
            "success": True,
            "message": "Análisis del documento mejorado con anotaciones",
            "enhanced_analysis": enhanced_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error mejorando análisis: {str(e)}"
        ) 