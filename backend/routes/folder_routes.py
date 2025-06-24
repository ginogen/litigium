from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
import uuid
from datetime import datetime
from pydantic import BaseModel, Field

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ..auth.dependencies import get_current_user
from ..models.user import User
from supabase_integration import supabase_admin

router = APIRouter(prefix="/api/folders", tags=["folders"])

# Modelos Pydantic
class CarpetaCreate(BaseModel):
    nombre: str = Field(..., description="Nombre de la carpeta")
    descripcion: Optional[str] = Field(None, description="Descripción opcional")
    color: Optional[str] = Field("#3B82F6", description="Color hex para la carpeta")
    icono: Optional[str] = Field("folder", description="Icono para la carpeta")

class CarpetaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, description="Nuevo nombre")
    descripcion: Optional[str] = Field(None, description="Nueva descripción")
    color: Optional[str] = Field(None, description="Nuevo color")
    icono: Optional[str] = Field(None, description="Nuevo icono")

@router.get("/")
async def obtener_carpetas(current_user: User = Depends(get_current_user)):
    """Obtiene todas las carpetas del abogado."""
    try:
        print(f"📁 Obteniendo carpetas para usuario: {current_user.id}")
        
        # Obtener el perfil del abogado
        abogado_response = supabase_admin.table('abogados')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        
        # Obtener carpetas
        response = supabase_admin.table('carpetas')\
            .select('*')\
            .eq('abogado_id', abogado_id)\
            .order('orden', desc=False)\
            .execute()
        
        print(f"✅ Carpetas encontradas: {len(response.data or [])}")
        
        return {
            "success": True,
            "carpetas": response.data or []
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Error obteniendo carpetas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo carpetas: {str(e)}"
        )

@router.post("/")
async def crear_carpeta(
    carpeta: CarpetaCreate,
    current_user: User = Depends(get_current_user)
):
    """Crea una nueva carpeta."""
    try:
        print(f"📁 Creando carpeta: {carpeta.nombre}")
        
        # Obtener el perfil del abogado
        abogado_response = supabase_admin.table('abogados')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        
        # Verificar que no existe una carpeta con el mismo nombre
        existing_response = supabase_admin.table('carpetas')\
            .select('id')\
            .eq('abogado_id', abogado_id)\
            .eq('nombre', carpeta.nombre)\
            .execute()
        
        if existing_response.data:
            raise HTTPException(
                status_code=400,
                detail="Ya existe una carpeta con ese nombre"
            )
        
        # Crear la carpeta
        nueva_carpeta = {
            "abogado_id": abogado_id,
            "nombre": carpeta.nombre,
            "descripcion": carpeta.descripcion,
            "color": carpeta.color,
            "icono": carpeta.icono,
            "orden": 0
        }
        
        response = supabase_admin.table('carpetas')\
            .insert(nueva_carpeta)\
            .execute()
        
        print(f"✅ Carpeta creada: {carpeta.nombre}")
        
        return {
            "success": True,
            "message": "Carpeta creada exitosamente",
            "carpeta": response.data[0] if response.data else None
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Error creando carpeta: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creando carpeta: {str(e)}"
        )

@router.put("/{carpeta_id}")
async def actualizar_carpeta(
    carpeta_id: str,
    datos: CarpetaUpdate,
    current_user: User = Depends(get_current_user)
):
    """Actualiza una carpeta existente."""
    try:
        print(f"📝 Actualizando carpeta: {carpeta_id}")
        
        # Obtener el perfil del abogado
        abogado_response = supabase_admin.table('abogados')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        
        # Verificar que la carpeta existe y pertenece al abogado
        carpeta_response = supabase_admin.table('carpetas')\
            .select('*')\
            .eq('id', carpeta_id)\
            .eq('abogado_id', abogado_id)\
            .single()\
            .execute()
        
        if not carpeta_response.data:
            raise HTTPException(status_code=404, detail="Carpeta no encontrada")
        
        # Si se actualiza el nombre, verificar que no existe otra con el mismo nombre
        if datos.nombre:
            existing_response = supabase_admin.table('carpetas')\
                .select('id')\
                .eq('abogado_id', abogado_id)\
                .eq('nombre', datos.nombre)\
                .neq('id', carpeta_id)\
                .execute()
            
            if existing_response.data:
                raise HTTPException(
                    status_code=400,
                    detail="Ya existe otra carpeta con ese nombre"
                )
        
        # Preparar datos de actualización
        update_data = {
            "updated_at": datetime.now().isoformat()
        }
        
        if datos.nombre is not None:
            update_data["nombre"] = datos.nombre
        if datos.descripcion is not None:
            update_data["descripcion"] = datos.descripcion
        if datos.color is not None:
            update_data["color"] = datos.color
        if datos.icono is not None:
            update_data["icono"] = datos.icono
        
        # Actualizar carpeta
        response = supabase_admin.table('carpetas')\
            .update(update_data)\
            .eq('id', carpeta_id)\
            .execute()
        
        print(f"✅ Carpeta actualizada: {carpeta_id}")
        
        return {
            "success": True,
            "message": "Carpeta actualizada exitosamente",
            "carpeta": response.data[0] if response.data else None
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Error actualizando carpeta: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando carpeta: {str(e)}"
        )

@router.delete("/{carpeta_id}")
async def eliminar_carpeta(
    carpeta_id: str,
    current_user: User = Depends(get_current_user)
):
    """Elimina una carpeta y mueve todas sus sesiones a 'sin carpeta'."""
    try:
        print(f"🗑️ Eliminando carpeta: {carpeta_id}")
        
        # Obtener el perfil del abogado
        abogado_response = supabase_admin.table('abogados')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        
        # Verificar que la carpeta existe y pertenece al abogado
        carpeta_response = supabase_admin.table('carpetas')\
            .select('*')\
            .eq('id', carpeta_id)\
            .eq('abogado_id', abogado_id)\
            .single()\
            .execute()
        
        if not carpeta_response.data:
            raise HTTPException(status_code=404, detail="Carpeta no encontrada")
        
        # Contar sesiones que se moverán
        sesiones_response = supabase_admin.table('chat_sesiones')\
            .select('id')\
            .eq('carpeta_id', carpeta_id)\
            .execute()
        
        sesiones_count = len(sesiones_response.data or [])
        
        # Mover todas las sesiones de esta carpeta a "sin carpeta" (carpeta_id = null)
        if sesiones_count > 0:
            supabase_admin.table('chat_sesiones')\
                .update({'carpeta_id': None})\
                .eq('carpeta_id', carpeta_id)\
                .execute()
        
        # Eliminar la carpeta
        supabase_admin.table('carpetas')\
            .delete()\
            .eq('id', carpeta_id)\
            .execute()
        
        print(f"✅ Carpeta eliminada: {carpeta_id}, {sesiones_count} conversaciones movidas a 'Recientes'")
        
        return {
            "success": True,
            "message": f"Carpeta eliminada exitosamente. {sesiones_count} conversaciones movidas a 'Recientes'."
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Error eliminando carpeta: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando carpeta: {str(e)}"
        )

@router.get("/{carpeta_id}/sesiones")
async def obtener_sesiones_carpeta(
    carpeta_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obtiene todas las sesiones de una carpeta específica."""
    try:
        # Obtener el perfil del abogado
        abogado_response = supabase_admin.table('abogados')\
            .select('*')\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if not abogado_response.data:
            raise HTTPException(status_code=404, detail="Perfil de abogado no encontrado")
        
        abogado_id = abogado_response.data['id']
        
        # Obtener sesiones de la carpeta
        response = supabase_admin.table('chat_sesiones')\
            .select('*')\
            .eq('abogado_id', abogado_id)\
            .eq('carpeta_id', carpeta_id)\
            .order('updated_at', desc=True)\
            .execute()
        
        return {
            "success": True,
            "sesiones": response.data or []
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo sesiones: {str(e)}"
        ) 