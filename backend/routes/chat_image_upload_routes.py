"""
Endpoints para Upload Múltiple de Imágenes en Chat
Sistema especializado para documentos legales con extracción completa.
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
import uuid
import asyncio
from datetime import datetime
import os

# Imports internos
from backend.models.user import User
from supabase_integration import (
    get_current_user, get_current_abogado,
    documento_chat_service, storage_service,
    DocumentoChatCreate, DocumentoChatResponse,
    supabase_admin, ChatService
)
from backend.services.image_document_processor import LegalDocumentProcessor
from backend.routes.chat_routes import obtener_sesion_con_abogado_id

router = APIRouter(prefix="/api/v1/chat", tags=["chat-documents"])

# Configuración
MAX_FILES_PER_REQUEST = 10
ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/upload-images")
async def upload_multiple_images(
    session_id: str = Form(...),
    files: List[UploadFile] = File(...),
    tipos_documento: List[str] = Form(...),  # Lista paralela a files
    current_user: User = Depends(get_current_user)
):
    """
    Upload múltiple de imágenes con procesamiento automático.
    
    Parámetros:
    - session_id: ID de la sesión de chat
    - files: Lista de archivos de imagen
    - tipos_documento: Lista de tipos ['telegrama', 'liquidacion', 'recibo_sueldo', 'carta_documento', 'imagen_general']
    """
    try:
        print(f"🚀 [UPLOAD] Iniciando upload de imágenes")
        print(f"   📁 Archivos recibidos: {len(files)}")
        print(f"   🆔 Session ID: {session_id}")
        print(f"   👤 User ID: {current_user.id}")
        print(f"   📋 Tipos documento: {tipos_documento}")
        
        # Validaciones iniciales
        if len(files) > MAX_FILES_PER_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Máximo {MAX_FILES_PER_REQUEST} archivos por request"
            )
        
        if len(files) != len(tipos_documento):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe especificar un tipo_documento para cada archivo"
            )
        
        print(f"✅ [UPLOAD] Validaciones básicas pasadas")
        
        # Obtener perfil del abogado
        print(f"🔍 [UPLOAD] Buscando perfil de abogado...")
        abogado_response = supabase_admin.table('abogados')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            print(f"❌ [UPLOAD] Perfil de abogado no encontrado para user_id: {current_user.id}")
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        print(f"✅ [UPLOAD] Abogado encontrado: {abogado_id}")
        
        # Validar que la sesión pertenece al abogado
        print(f"🔍 [UPLOAD] Validando sesión...")
        session_response = supabase_admin.table('chat_sesiones')\
            .select('id')\
            .eq('session_id', session_id)\
            .eq('abogado_id', abogado_id)\
            .single()\
            .execute()
        
        if not session_response.data:
            print(f"❌ [UPLOAD] Sesión no encontrada: session_id={session_id}, abogado_id={abogado_id}")
            raise HTTPException(status_code=404, detail="Sesión no encontrada o no autorizada")
        
        print(f"✅ [UPLOAD] Sesión validada: {session_response.data['id']}")
        print(f"🚀 [UPLOAD] Iniciando procesamiento de {len(files)} archivos")
        
        # Procesar archivos en paralelo
        upload_tasks = []
        for i, (file, tipo_doc) in enumerate(zip(files, tipos_documento)):
            print(f"   📄 [UPLOAD] Preparando archivo {i+1}: {file.filename} (tipo: {tipo_doc})")
            task = _process_single_file(file, tipo_doc, session_id, abogado_id, i)
            upload_tasks.append(task)
        
        # Ejecutar uploads concurrentemente (máximo 3 paralelos)
        semaforo = asyncio.Semaphore(3)
        upload_results = []
        
        async def limited_upload(task):
            async with semaforo:
                return await task
        
        limited_tasks = [limited_upload(task) for task in upload_tasks]
        print(f"🔄 [UPLOAD] Ejecutando {len(limited_tasks)} tareas de upload...")
        upload_results = await asyncio.gather(*limited_tasks, return_exceptions=True)
        
        # Separar éxitos de errores
        successful_uploads = []
        failed_uploads = []
        
        for i, result in enumerate(upload_results):
            if isinstance(result, Exception):
                print(f"❌ [UPLOAD] Error en archivo {i+1}: {str(result)}")
                failed_uploads.append({
                    'archivo': files[i].filename,
                    'error': str(result),
                    'indice': i
                })
            else:
                print(f"✅ [UPLOAD] Archivo {i+1} procesado exitosamente: {result['nombre_archivo']}")
                successful_uploads.append(result)
        
        print(f"✅ [UPLOAD] Resumen: {len(successful_uploads)} éxitos, {len(failed_uploads)} errores")
        
        # Si hay archivos exitosos, iniciar procesamiento en background
        if successful_uploads:
            print(f"🧠 [UPLOAD] Iniciando procesamiento en background para {len(successful_uploads)} archivos")
            # Crear tarea de procesamiento en background
            asyncio.create_task(_process_images_background(
                successful_uploads, session_id, abogado_id
            ))
        
        response_data = {
            "success": True,
            "message": f"Upload completado: {len(successful_uploads)} archivos subidos",
            "uploaded_files": successful_uploads,
            "failed_files": failed_uploads,
            "total_uploaded": len(successful_uploads),
            "total_failed": len(failed_uploads),
            "processing_started": len(successful_uploads) > 0
        }
        
        print(f"🎯 [UPLOAD] Respuesta final: {response_data}")
        return response_data
        
    except HTTPException as e:
        print(f"❌ [UPLOAD] HTTPException: {e.detail}")
        raise e
    except Exception as e:
        print(f"❌ [UPLOAD] Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando upload: {str(e)}"
        )

async def _process_single_file(
    file: UploadFile, 
    tipo_documento: str, 
    session_id: str, 
    abogado_id: str, 
    index: int
) -> Dict[str, Any]:
    """Procesa un archivo individual: validación, upload a Storage, registro en DB."""
    
    try:
        print(f"📄 [PROCESS] Iniciando procesamiento de archivo {index+1}: {file.filename}")
        
        # Validar archivo
        print(f"🔍 [PROCESS] Validando tipo de archivo: {file.content_type}")
        if file.content_type not in ALLOWED_MIME_TYPES:
            error_msg = f"Tipo de archivo no permitido: {file.content_type}"
            print(f"❌ [PROCESS] {error_msg}")
            raise ValueError(error_msg)
        
        # Leer archivo
        print(f"📖 [PROCESS] Leyendo archivo...")
        file_bytes = await file.read()
        file_size = len(file_bytes)
        print(f"✅ [PROCESS] Archivo leído: {file_size} bytes")
        
        if file_size > MAX_FILE_SIZE:
            error_msg = f"Archivo muy grande: {file_size} bytes (máximo: {MAX_FILE_SIZE})"
            print(f"❌ [PROCESS] {error_msg}")
            raise ValueError(error_msg)
        
        # Generar path único - IMPORTANTE: usar user_id como primer segmento para las políticas
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"{session_id}_{timestamp}_{index:02d}_{uuid.uuid4().hex[:8]}.{file_extension}"
        
        # Obtener user_id del abogado para el path
        abogado_response = supabase_admin.table('abogados')\
            .select('user_id')\
            .eq('id', abogado_id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise ValueError(f"No se pudo obtener user_id para abogado {abogado_id}")
        
        user_id = abogado_response.data['user_id']
        print(f"👤 [PROCESS] User ID obtenido: {user_id}")
        
        # Path que coincide con las políticas: user_id/chat/abogado_id/session_id/filename
        storage_path = f"{user_id}/chat/{abogado_id}/{session_id}/{unique_filename}"
        
        print(f"📁 [PROCESS] Path generado: {storage_path}")
        
        # Subir a Supabase Storage
        print(f"☁️ [PROCESS] Subiendo a Supabase Storage...")
        try:
            archivo_url = await storage_service.subir_archivo(
                "documentos-chat",
                storage_path,
                file_bytes,
                file.content_type
            )
            print(f"✅ [PROCESS] Archivo subido exitosamente: {archivo_url}")
        except Exception as storage_error:
            print(f"❌ [PROCESS] Error subiendo a Storage: {str(storage_error)}")
            raise storage_error
        
        # Registrar en base de datos
        print(f"💾 [PROCESS] Registrando en base de datos...")
        try:
            documento_data = DocumentoChatCreate(
                session_id=session_id,
                nombre_archivo=file.filename,
                tipo_documento=tipo_documento,
                mime_type=file.content_type,
                tamaño_bytes=file_size
            )
            
            documento_db = await documento_chat_service.crear_documento(
                abogado_id, archivo_url, documento_data
            )
            print(f"✅ [PROCESS] Documento registrado en DB: {documento_db['id']}")
        except Exception as db_error:
            print(f"❌ [PROCESS] Error registrando en DB: {str(db_error)}")
            raise db_error
        
        result = {
            "id": documento_db["id"],
            "nombre_archivo": file.filename,
            "tipo_documento": tipo_documento,
            "archivo_url": archivo_url,
            "tamaño_bytes": file_size,
            "upload_index": index,
            "procesamiento_pendiente": True
        }
        
        print(f"🎯 [PROCESS] Procesamiento completado exitosamente para: {file.filename}")
        return result
        
    except Exception as e:
        print(f"❌ [PROCESS] Error procesando archivo {file.filename}: {str(e)}")
        raise e

async def _enviar_resultados_procesamiento_al_chat(
    session_id: str, 
    abogado_id: str, 
    resultados: List[Dict]
):
    """Envía los resultados del procesamiento de imágenes al chat de forma más inteligente."""
    try:
        # Contar resultados exitosos
        resultados_exitosos = [r for r in resultados if r.get('procesado_exitosamente')]
        resultados_fallidos = [r for r in resultados if not r.get('procesado_exitosamente')]
        
        if not resultados_exitosos:
            # Si no hay resultados exitosos, enviar mensaje de error
            mensaje_resultados = "❌ **No se pudo procesar ninguna imagen correctamente.**\n\n"
            mensaje_resultados += "💡 **Sugerencias:**\n"
            mensaje_resultados += "• Verifica que las imágenes sean claras y legibles\n"
            mensaje_resultados += "• Asegúrate de que contengan texto relevante\n"
            mensaje_resultados += "• Intenta con imágenes de mejor calidad\n"
        else:
            # Crear mensaje más conversacional y útil
            mensaje_resultados = f"✅ **Procesamiento completado:** {len(resultados_exitosos)} imagen(es) analizada(s)\n\n"
            
            # Extraer información más relevante de todos los documentos
            todas_personas = []
            todas_empresas = []
            todas_fechas = []
            todos_montos = []
            
            for resultado in resultados_exitosos:
                datos_estructurados = resultado.get('datos_estructurados', {})
                
                # Recolectar personas
                if 'datos_personales' in datos_estructurados:
                    personas = datos_estructurados['datos_personales'].get('nombres_personas', [])
                    todas_personas.extend(personas)
                
                # Recolectar empresas
                if 'datos_empresas' in datos_estructurados:
                    empresas = datos_estructurados['datos_empresas'].get('nombres_empresas', [])
                    todas_empresas.extend(empresas)
                
                # Recolectar fechas
                if 'fechas_encontradas' in datos_estructurados:
                    fechas = datos_estructurados['fechas_encontradas']
                    todas_fechas.extend(fechas)
                
                # Recolectar montos
                if 'montos_encontrados' in datos_estructurados:
                    montos = datos_estructurados['montos_encontrados']
                    todos_montos.extend(montos)
            
            # Mostrar información más relevante de forma resumida
            if todas_personas:
                personas_unicas = list(set(todas_personas))[:3]  # Máximo 3 personas únicas
                mensaje_resultados += f"👥 **Personas identificadas:** {', '.join(personas_unicas)}\n"
            
            if todas_empresas:
                empresas_unicas = list(set(todas_empresas))[:2]  # Máximo 2 empresas únicas
                mensaje_resultados += f"🏢 **Empresas mencionadas:** {', '.join(empresas_unicas)}\n"
            
            if todas_fechas:
                fechas_unicas = list(set(todas_fechas))[:3]  # Máximo 3 fechas únicas
                mensaje_resultados += f"📅 **Fechas importantes:** {', '.join(fechas_unicas)}\n"
            
            if todos_montos:
                montos_unicos = list(set(todos_montos))[:2]  # Máximo 2 montos únicos
                mensaje_resultados += f"💰 **Montos relevantes:** {', '.join(montos_unicos)}\n"
            
            # Mensaje conversacional para continuar
            mensaje_resultados += f"\n💬 **¿Qué te gustaría hacer ahora?**\n"
            mensaje_resultados += f"• Puedes confirmar si esta información es correcta\n"
            mensaje_resultados += f"• Agregar más detalles sobre el caso\n"
            mensaje_resultados += f"• Subir más documentos si es necesario\n"
            mensaje_resultados += f"• Proceder a generar la demanda si tienes toda la información\n"
        
        # Si hay errores, mencionarlos brevemente
        if resultados_fallidos:
            mensaje_resultados += f"\n⚠️ **Nota:** {len(resultados_fallidos)} imagen(es) no se pudieron procesar correctamente."
        
        # Obtener el id interno de la sesión (UUID de la tabla chat_sesiones)
        sesion_db = await obtener_sesion_con_abogado_id(session_id, abogado_id)
        sesion_db_id = sesion_db['id']
        await ChatService.guardar_mensaje(
            sesion_id=sesion_db_id,
            tipo="bot",
            mensaje=mensaje_resultados,
            metadata={"tipo": "resultados_procesamiento_imagen"}
        )
        
        print(f"✅ Mensaje inteligente con resultados enviado al chat: {session_id}")
        
    except Exception as e:
        print(f"❌ Error enviando resultados al chat: {str(e)}")

async def _process_images_background(
    uploaded_files: List[Dict], 
    session_id: str, 
    abogado_id: str
):
    """Procesa las imágenes en background usando GPT-4 Vision y envía un mensaje final inteligente."""
    try:
        print(f"🧠 Iniciando procesamiento en background de {len(uploaded_files)} imágenes")
        
        # Obtener el id interno de la sesión (UUID de la tabla chat_sesiones)
        sesion_db = await obtener_sesion_con_abogado_id(session_id, abogado_id)
        sesion_db_id = sesion_db['id']
        
        # Inicializar procesador
        processor = LegalDocumentProcessor()
        
        # Procesar cada imagen individualmente
        resultados_individuales = []
        for idx, uploaded_file in enumerate(uploaded_files):
            nombre_archivo = uploaded_file["nombre_archivo"]
            tipo_documento = uploaded_file["tipo_documento"]
            documento_id = uploaded_file["id"]
            archivo_url = uploaded_file["archivo_url"]
            
            try:
                # Solo enviar un mensaje de inicio si hay múltiples imágenes
                if len(uploaded_files) > 1:
                    await ChatService.guardar_mensaje(
                        sesion_db_id=sesion_db_id,
                        tipo="bot",
                        mensaje=f"📄 Procesando imagen {idx+1} de {len(uploaded_files)}: **{nombre_archivo}**...",
                        metadata={"tipo": "avance_procesamiento_imagen", "nombre_archivo": nombre_archivo, "indice": idx}
                    )
                
                # Descargar imagen
                imagen_bytes = await _descargar_imagen_desde_storage(archivo_url)
                if not imagen_bytes:
                    await documento_chat_service.actualizar_procesamiento(
                        documento_id,
                        "",
                        {},
                        {"error": True, "error_message": "No se pudo descargar la imagen"},
                        "No se pudo descargar la imagen"
                    )
                    await ChatService.guardar_mensaje(
                        sesion_id=sesion_db_id,
                        tipo="bot",
                        mensaje=f"❌ Error al descargar la imagen {idx+1}: **{nombre_archivo}**",
                        metadata={"tipo": "error_procesamiento_imagen", "nombre_archivo": nombre_archivo, "indice": idx}
                    )
                    resultados_individuales.append({
                        "procesado_exitosamente": False,
                        "nombre_archivo": nombre_archivo,
                        "error": "No se pudo descargar la imagen"
                    })
                    continue
                
                # Procesar imagen con GPT-4 Vision
                resultado = await processor.procesar_imagenes_multiples([
                    (imagen_bytes, nombre_archivo, tipo_documento)
                ], session_id, abogado_id)
                resultado_ind = resultado['resultados_individuales'][0]
                
                # Actualizar registro en DB
                await documento_chat_service.actualizar_procesamiento(
                    documento_id,
                    resultado_ind.get('texto_extraido', ''),
                    resultado_ind.get('datos_estructurados', {}),
                    resultado_ind.get('metadatos_procesamiento', {}),
                    None
                )
                resultado_ind['procesado_exitosamente'] = True
                resultado_ind['nombre_archivo'] = nombre_archivo
                resultados_individuales.append(resultado_ind)
                print(f"✅ Procesamiento completado: {nombre_archivo}")
            except Exception as e:
                print(f"❌ Error procesando imagen {nombre_archivo}: {str(e)}")
                await documento_chat_service.actualizar_procesamiento(
                    documento_id,
                    "",
                    {},
                    {"error": True, "error_message": str(e)},
                    str(e)
                )
                await ChatService.guardar_mensaje(
                    sesion_id=sesion_db_id,
                    tipo="bot",
                    mensaje=f"❌ Error procesando la imagen {idx+1}: **{nombre_archivo}** - {str(e)}",
                    metadata={"tipo": "error_procesamiento_imagen", "nombre_archivo": nombre_archivo, "indice": idx}
                )
                resultados_individuales.append({
                    "procesado_exitosamente": False,
                    "nombre_archivo": nombre_archivo,
                    "error": str(e)
                })
        
        # Al finalizar, enviar el mensaje resumen inteligente
        if resultados_individuales:
            await _enviar_resultados_procesamiento_al_chat(
                session_id, abogado_id, resultados_individuales
            )
    except Exception as e:
        print(f"❌ Error en procesamiento background: {str(e)}")
        for uploaded_file in uploaded_files:
            try:
                await documento_chat_service.actualizar_procesamiento(
                    uploaded_file["id"],
                    "",
                    {},
                    {"error": True, "error_message": str(e)},
                    str(e)
                )
            except Exception as update_error:
                print(f"❌ Error actualizando estado de error: {update_error}")

async def _descargar_imagen_desde_storage(archivo_url: str) -> bytes:
    """Descarga una imagen desde Supabase Storage usando la API."""
    try:
        print(f"📥 [DOWNLOAD] Descargando desde: {archivo_url}")
        
        # Extraer el path del archivo de la URL
        # URL: https://odemisttpuwsgfezotnm.supabase.co/storage/v1/object/public/documentos-chat/path/to/file.jpg
        path_parts = archivo_url.split('/storage/v1/object/public/documentos-chat/')
        if len(path_parts) < 2:
            print(f"❌ [DOWNLOAD] URL malformada: {archivo_url}")
            return None
        
        file_path = path_parts[1]
        # Remover parámetros de query si existen
        if '?' in file_path:
            file_path = file_path.split('?')[0]
        
        print(f"📁 [DOWNLOAD] Path extraído: {file_path}")
        
        # Usar supabase_admin para descargar el archivo
        response = supabase_admin.storage.from_('documentos-chat').download(file_path)
        
        if response is None:
            print(f"❌ [DOWNLOAD] Respuesta nula de Supabase")
            return None
        
        # Verificar si hay error en la respuesta
        if hasattr(response, 'error') and response.error:
            print(f"❌ [DOWNLOAD] Error de Supabase: {response.error}")
            return None
        
        # La respuesta debería ser bytes
        if isinstance(response, bytes):
            content_length = len(response)
            print(f"✅ [DOWNLOAD] Descarga exitosa: {content_length} bytes")
            return response
        else:
            print(f"❌ [DOWNLOAD] Tipo de respuesta inesperado: {type(response)}")
            return None
            
    except Exception as e:
        print(f"❌ [DOWNLOAD] Error descargando imagen desde {archivo_url}: {str(e)}")
        return None

@router.get("/documents/{session_id}")
async def get_chat_documents(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtiene todos los documentos de una sesión de chat."""
    try:
        # Obtener abogado_id
        abogado_response = supabase_admin.table('abogados')\
            .select('id')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        
        # Obtener documentos
        documentos = await documento_chat_service.obtener_documentos_sesion(session_id, abogado_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "documentos": documentos,
            "total": len(documentos)
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo documentos: {str(e)}"
        )

@router.get("/documents/{session_id}/summary")
async def get_chat_documents_summary(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtiene resumen consolidado de documentos de una sesión."""
    try:
        # Validar sesión pertenece al usuario
        abogado_response = supabase_admin.table('abogados')\
            .select('id')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        
        session_response = supabase_admin.table('chat_sesiones')\
            .select('id')\
            .eq('session_id', session_id)\
            .eq('abogado_id', abogado_id)\
            .single()\
            .execute()
        
        if not session_response.data:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        
        # Obtener resumen usando función SQL
        resumen = await documento_chat_service.obtener_resumen_sesion(session_id)
        
        # Obtener consolidado usando función SQL
        consolidado = await documento_chat_service.obtener_consolidado_sesion(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "resumen": resumen,
            "consolidado": consolidado
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo resumen: {str(e)}"
        )

@router.delete("/documents/{documento_id}")
async def delete_chat_document(
    documento_id: str,
    current_user: User = Depends(get_current_user)
):
    """Elimina un documento del chat."""
    try:
        # Obtener abogado_id
        abogado_response = supabase_admin.table('abogados')\
            .select('id')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        
        # Verificar que el documento pertenece al abogado
        doc_response = supabase_admin.table('documentos_chat')\
            .select('archivo_url')\
            .eq('id', documento_id)\
            .eq('abogado_id', abogado_id)\
            .single()\
            .execute()
        
        if not doc_response.data:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        archivo_url = doc_response.data['archivo_url']
        
        # Eliminar de base de datos
        delete_response = supabase_admin.table('documentos_chat')\
            .delete()\
            .eq('id', documento_id)\
            .eq('abogado_id', abogado_id)\
            .execute()
        
        # Intentar eliminar archivo de Storage (no crítico si falla)
        try:
            if archivo_url:
                # Extraer path del archivo de la URL
                path_parts = archivo_url.split('/storage/v1/object/public/documentos-chat/')
                if len(path_parts) > 1:
                    file_path = path_parts[1]
                    await storage_service.eliminar_archivo("documentos-chat", file_path)
        except Exception as storage_error:
            print(f"⚠️ Error eliminando archivo de storage: {storage_error}")
        
        return {
            "success": True,
            "message": "Documento eliminado exitosamente",
            "documento_id": documento_id
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando documento: {str(e)}"
        ) 