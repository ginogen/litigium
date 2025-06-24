import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

class CategoryManager:
    """Gestor de categorías de demandas personalizadas por usuario."""
    
    def __init__(self):
        # No necesitamos el cliente normal, usaremos el admin
        from supabase_integration import supabase_admin
        self.supabase = supabase_admin
    
    def create_category(
        self, 
        user_id: str, 
        nombre: str, 
        descripcion: str = None, 
        color: str = "#6366f1",
        icon: str = "📁"
    ) -> Dict[str, Any]:
        """Crea una nueva categoría para el usuario."""
        try:
            category_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "nombre": nombre.strip(),
                "descripcion": descripcion.strip() if descripcion else None,
                "color": color,
                "icon": icon,
                "activo": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Usar cliente admin para bypasear RLS
            result = self.supabase.table("categorias_demandas").insert(category_data).execute()
            
            if result.data:
                return {
                    "success": True,
                    "category": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": "No se pudo crear la categoría"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creando categoría: {str(e)}"
            }
    
    def get_user_categories(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene todas las categorías activas del usuario."""
        try:
            result = self.supabase.table("categorias_demandas")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("activo", True)\
                .order("nombre")\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            raise Exception(f"Error obteniendo categorías: {str(e)}")
    
    def update_category(
        self, 
        category_id: str, 
        user_id: str, 
        nombre: str = None, 
        descripcion: str = None,
        color: str = None,
        icon: str = None
    ) -> Dict[str, Any]:
        """Actualiza una categoría existente."""
        try:
            update_data = {
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if nombre is not None:
                update_data["nombre"] = nombre.strip()
            if descripcion is not None:
                update_data["descripcion"] = descripcion.strip() if descripcion else None
            if color is not None:
                update_data["color"] = color
            if icon is not None:
                update_data["icon"] = icon
            
            result = self.supabase.table("categorias_demandas")\
                .update(update_data)\
                .eq("id", category_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if result.data:
                return {
                    "success": True,
                    "category": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": "Categoría no encontrada o sin permisos"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error actualizando categoría: {str(e)}"
            }
    
    def delete_category(self, category_id: str, user_id: str) -> Dict[str, Any]:
        """Marca una categoría como inactiva (soft delete)."""
        try:
            # Verificar si la categoría tiene documentos asociados
            docs_result = self.supabase.table("documentos_entrenamiento")\
                .select("id")\
                .eq("categoria_id", category_id)\
                .execute()
            
            if docs_result.data:
                return {
                    "success": False,
                    "error": f"No se puede eliminar la categoría porque tiene {len(docs_result.data)} documentos asociados"
                }
            
            # Marcar como inactiva
            result = self.supabase.table("categorias_demandas")\
                .update({
                    "activo": False,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("id", category_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if result.data:
                return {
                    "success": True,
                    "message": "Categoría eliminada correctamente"
                }
            else:
                return {
                    "success": False,
                    "error": "Categoría no encontrada o sin permisos"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error eliminando categoría: {str(e)}"
            }
    
    def get_category_statistics(self, user_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas de documentos por categoría para el usuario."""
        try:
            # Buscar el ID del abogado basado en el user_id
            abogado_result = self.supabase.table("abogados")\
                .select("id")\
                .eq("user_id", user_id)\
                .execute()
            
            if not abogado_result.data or len(abogado_result.data) == 0:
                print(f"⚠️ No se encontró abogado para user_id: {user_id}")
                # Devolver estructura vacía pero válida
                return {
                    "categories": [],
                    "total_categories": 0,
                    "total_documents": 0
                }
            
            abogado_id = abogado_result.data[0]["id"]
            print(f"🔍 Estadísticas - Usuario {user_id} -> Abogado {abogado_id}")
            
            # Obtener categorías del usuario
            categories = self.get_user_categories(user_id)
            
            # Obtener conteo de documentos por categoría
            stats = []
            total_documents = 0
            
            for category in categories:
                docs_result = self.supabase.table("documentos_entrenamiento")\
                    .select("id, estado_procesamiento")\
                    .eq("abogado_id", abogado_id)\
                    .eq("categoria_id", category["id"])\
                    .execute()
                
                docs_count = len(docs_result.data) if docs_result.data else 0
                processed_count = len([d for d in (docs_result.data or []) if d.get("estado_procesamiento") == "completado"])
                
                print(f"   📊 Categoría {category['nombre']}: {docs_count} docs, {processed_count} procesados")
                
                stats.append({
                    "categoria_id": category["id"],
                    "nombre": category["nombre"],
                    "color": category["color"],
                    "icon": category["icon"],
                    "total_documentos": docs_count,
                    "documentos_procesados": processed_count,
                    "documentos_pendientes": docs_count - processed_count
                })
                
                total_documents += docs_count
            
            return {
                "categories": stats,
                "total_categories": len(categories),
                "total_documents": total_documents
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas: {str(e)}")
            raise Exception(f"Error obteniendo estadísticas: {str(e)}")
    
    def get_category_by_id(self, category_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una categoría específica por ID."""
        try:
            result = self.supabase.table("categorias_demandas")\
                .select("*")\
                .eq("id", category_id)\
                .eq("user_id", user_id)\
                .eq("activo", True)\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            raise Exception(f"Error obteniendo categoría: {str(e)}")
    
    def create_default_categories_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Crea categorías por defecto para un nuevo usuario."""
        default_categories = [
            {
                "nombre": "Derecho Laboral",
                "descripcion": "Demandas relacionadas con conflictos laborales",
                "color": "#3b82f6",
                "icon": "⚖️"
            },
            {
                "nombre": "Derecho Civil",
                "descripcion": "Demandas civiles generales",
                "color": "#8b5cf6",
                "icon": "📋"
            },
            {
                "nombre": "Derecho Penal",
                "descripcion": "Demandas y casos penales",
                "color": "#ef4444",
                "icon": "🔒"
            },
            {
                "nombre": "Derecho Comercial",
                "descripcion": "Demandas comerciales y empresariales",
                "color": "#10b981",
                "icon": "💼"
            },
            {
                "nombre": "Derecho de Familia",
                "descripcion": "Demandas familiares y de menores",
                "color": "#f59e0b",
                "icon": "👨‍👩‍👧‍👦"
            }
        ]
        
        created_categories = []
        
        for category_data in default_categories:
            result = self.create_category(
                user_id=user_id,
                nombre=category_data["nombre"],
                descripcion=category_data["descripcion"],
                color=category_data["color"],
                icon=category_data["icon"]
            )
            
            if result["success"]:
                created_categories.append(result["category"])
        
        return created_categories
    
    def search_categories(self, user_id: str, search_term: str) -> List[Dict[str, Any]]:
        """Busca categorías por nombre o descripción."""
        try:
            search_term = search_term.lower().strip()
            
            result = self.supabase.table("categorias_demandas")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("activo", True)\
                .execute()
            
            if not result.data:
                return []
            
            # Filtrar en Python ya que Supabase no soporta ILIKE en todos los casos
            filtered_categories = []
            for category in result.data:
                if (search_term in category["nombre"].lower() or 
                    (category["descripcion"] and search_term in category["descripcion"].lower())):
                    filtered_categories.append(category)
            
            return filtered_categories
            
        except Exception as e:
            raise Exception(f"Error buscando categorías: {str(e)}")
    
    def user_has_trained_categories(self, user_id: str) -> Dict[str, Any]:
        """Verifica si el usuario tiene categorías con documentos entrenados."""
        try:
            # Obtener categorías del usuario
            categorias = self.get_user_categories(user_id)
            
            if not categorias:
                return {
                    "has_categories": False,
                    "has_documents": False,
                    "ready_for_chat": False,
                    "total_categories": 0,
                    "categories_with_docs": 0,
                    "message": "No tienes categorías creadas. Ve a 'Entrenar' → 'Gestionar Categorías'",
                    "categories": []
                }
            
            # Verificar documentos procesados por categoría (ya usa el abogado_id correcto)
            stats = self.get_category_statistics(user_id)
            categorias_con_documentos = []
            
            for categoria in categorias:
                categoria_stats = next((s for s in stats['categories'] if s['categoria_id'] == categoria['id']), None)
                
                if categoria_stats and categoria_stats['documentos_procesados'] > 0:
                    categorias_con_documentos.append({
                        'id': categoria['id'],
                        'nombre': categoria['nombre'],
                        'documentos_procesados': categoria_stats['documentos_procesados'],
                        'documentos_pendientes': categoria_stats.get('documentos_pendientes', 0)
                    })
            
            ready_for_chat = len(categorias_con_documentos) > 0
            
            print(f"🎯 Verificación de categorías entrenadas:")
            print(f"   Total categorías: {len(categorias)}")
            print(f"   Categorías con documentos: {len(categorias_con_documentos)}")
            print(f"   Listo para chat: {ready_for_chat}")
            
            return {
                "has_categories": True,
                "has_documents": ready_for_chat,
                "ready_for_chat": ready_for_chat,
                "total_categories": len(categorias),
                "categories_with_docs": len(categorias_con_documentos),
                "message": f"✅ Listo con {len(categorias_con_documentos)} categorías entrenadas" if ready_for_chat else f"⚠️ Tienes {len(categorias)} categorías sin documentos procesados",
                "categories": categorias_con_documentos
            }
            
        except Exception as e:
            print(f"❌ Error verificando categorías entrenadas: {str(e)}")
            return {
                "has_categories": False,
                "has_documents": False,
                "ready_for_chat": False,
                "total_categories": 0,
                "categories_with_docs": 0,
                "message": f"Error verificando categorías: {str(e)}",
                "categories": [],
                "error": str(e)
            } 