"""
Endpoints API para gestión de cámaras (CRUD).

Permite a los usuarios:
- Listar cámaras configuradas
- Agregar nuevas cámaras
- Editar cámaras existentes
- Eliminar cámaras
- Activar/desactivar streams

Autor: Sistema de Monitoreo de Hurones
Fecha: 2026-01-10
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Any
from loguru import logger

from utils.camera_manager import camera_db, CameraConfig
from api.hls_server import hls_server


# ==================== MODELOS PYDANTIC ====================

class CameraCreateRequest(BaseModel):
    """Modelo para crear cámara."""
    name: str = Field(..., min_length=1, max_length=100, description="Nombre descriptivo")
    rtsp_url: str = Field(..., min_length=10, description="URL RTSP completa")
    description: str = Field(default="", max_length=500, description="Descripción opcional")
    location: str = Field(default="", max_length=100, description="Ubicación física")
    is_active: bool = Field(default=True, description="Si debe iniciarse automáticamente")
    
    @validator('rtsp_url')
    def validate_rtsp_url(cls, v):
        """Validar que sea una URL RTSP válida."""
        if not v.startswith('rtsp://'):
            raise ValueError('La URL debe comenzar con rtsp://')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Cámara Sala Principal",
                "rtsp_url": "rtsp://admin:password@192.168.1.10:554/stream1",
                "description": "Cámara principal del área de juego",
                "location": "Sala 1",
                "is_active": True
            }
        }


class CameraUpdateRequest(BaseModel):
    """Modelo para actualizar cámara."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rtsp_url: Optional[str] = Field(None, min_length=10)
    description: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    
    @validator('rtsp_url')
    def validate_rtsp_url(cls, v):
        """Validar que sea una URL RTSP válida."""
        if v and not v.startswith('rtsp://'):
            raise ValueError('La URL debe comenzar con rtsp://')
        return v


class CameraResponse(BaseModel):
    """Modelo de respuesta de cámara."""
    id: int
    name: str
    rtsp_url: str
    description: str
    location: str
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
    
    # Status del stream (si está corriendo)
    stream_status: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Cámara Sala Principal",
                "rtsp_url": "rtsp://admin:***@192.168.1.10:554/stream1",
                "description": "Cámara principal",
                "location": "Sala 1",
                "is_active": True,
                "created_at": "2026-01-10T10:00:00",
                "updated_at": "2026-01-10T10:30:00",
                "stream_status": "running"
            }
        }


class APIResponse(BaseModel):
    """Respuesta estándar de la API."""
    trace_id: str = "camera-api"
    code: int = 200
    message: str = "OK"
    data: Optional[Any] = None


# ==================== ROUTER ====================

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])


# ==================== ENDPOINTS ====================

@router.get("", response_model=APIResponse)
async def list_cameras(only_active: bool = False):
    """
    Listar todas las cámaras configuradas.
    
    Args:
        only_active: Si True, solo devuelve cámaras activas
        
    Returns:
        Lista de cámaras con su configuración y estado de stream
    """
    try:
        cameras = camera_db.get_all_cameras(only_active=only_active)
        
        # Agregar estado del stream HLS
        cameras_with_status = []
        for cam in cameras:
            camera_dict = cam.to_dict()
            
            # Ocultar credenciales en la respuesta
            if '@' in camera_dict['rtsp_url']:
                parts = camera_dict['rtsp_url'].split('@')
                credentials = parts[0].split('//')[1]
                camera_dict['rtsp_url'] = f"rtsp://***@{parts[1]}"
            
            # Verificar estado del stream (si HLS server está inicializado)
            if hls_server and cam.id is not None:
                if hls_server.is_stream_running(cam.id):
                    camera_dict['stream_status'] = 'running'
                else:
                    camera_dict['stream_status'] = 'stopped'
            else:
                camera_dict['stream_status'] = 'unknown'
            
            cameras_with_status.append(camera_dict)
        
        logger.info(f"📹 Listadas {len(cameras_with_status)} cámaras")
        
        return APIResponse(
            trace_id="list-cameras",
            code=200,
            message=f"{len(cameras_with_status)} cámara(s) encontrada(s)",
            data=cameras_with_status
        )
        
    except Exception as e:
        logger.error(f"❌ Error listando cámaras: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.get("/{camera_id}", response_model=APIResponse)
async def get_camera(camera_id: int):
    """
    Obtener configuración de una cámara específica.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        Configuración de la cámara
    """
    try:
        camera = camera_db.get_camera(camera_id)
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara {camera_id} no encontrada"
            )
        
        camera_dict = camera.to_dict()
        
        # Ocultar credenciales
        if '@' in camera_dict['rtsp_url']:
            parts = camera_dict['rtsp_url'].split('@')
            camera_dict['rtsp_url'] = f"rtsp://***@{parts[1]}"
        
        # Estado del stream
        if hls_server:
            if hls_server.is_stream_running(camera_id):
                camera_dict['stream_status'] = 'running'
            else:
                camera_dict['stream_status'] = 'stopped'
        else:
            camera_dict['stream_status'] = 'unknown'
        
        return APIResponse(
            trace_id=f"get-camera-{camera_id}",
            code=200,
            message="Cámara encontrada",
            data=camera_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.post("", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(camera: CameraCreateRequest):
    """
    Agregar nueva cámara al sistema.
    
    Args:
        camera: Datos de la nueva cámara
        
    Returns:
        ID de la cámara creada y su configuración
    """
    try:
        logger.info(f"➕ Creando cámara: {camera.name}")
        
        camera_id = camera_db.add_camera(
            name=camera.name,
            rtsp_url=camera.rtsp_url,
            description=camera.description,
            location=camera.location,
            is_active=camera.is_active
        )
        
        if not camera_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo crear la cámara (posible URL duplicada)"
            )
        
        # Iniciar stream HLS si está activa
        if camera.is_active and hls_server:
            logger.info(f"🎬 Iniciando stream HLS para nueva cámara {camera_id}")
            await hls_server.start_camera_stream(camera_id, camera.rtsp_url)
        
        # Obtener cámara creada
        created_camera = camera_db.get_camera(camera_id)
        camera_dict = created_camera.to_dict() if created_camera else {}
        
        # Ocultar credenciales
        if camera_dict and '@' in camera_dict.get('rtsp_url', ''):
            parts = camera_dict['rtsp_url'].split('@')
            camera_dict['rtsp_url'] = f"rtsp://***@{parts[1]}"
        
        logger.info(f"✅ Cámara {camera_id} creada exitosamente")
        
        return APIResponse(
            trace_id=f"create-camera-{camera_id}",
            code=201,
            message=f"Cámara '{camera.name}' creada exitosamente",
            data=camera_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando cámara: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.put("/{camera_id}", response_model=APIResponse)
async def update_camera(camera_id: int, camera: CameraUpdateRequest):
    """
    Actualizar configuración de una cámara existente.
    
    Args:
        camera_id: ID de la cámara
        camera: Datos a actualizar (solo campos presentes)
        
    Returns:
        Configuración actualizada de la cámara
    """
    try:
        # Verificar que existe
        existing = camera_db.get_camera(camera_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara {camera_id} no encontrada"
            )
        
        logger.info(f"✏️  Actualizando cámara {camera_id}")
        
        # Si cambió URL o estado, reiniciar stream
        restart_stream = False
        if camera.rtsp_url and camera.rtsp_url != existing.rtsp_url:
            restart_stream = True
        if camera.is_active is not None and camera.is_active != existing.is_active:
            restart_stream = True
        
        # Actualizar en BD
        success = camera_db.update_camera(
            camera_id=camera_id,
            name=camera.name,
            rtsp_url=camera.rtsp_url,
            description=camera.description,
            location=camera.location,
            is_active=camera.is_active
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo actualizar la cámara"
            )
        
        # Reiniciar stream si es necesario
        if restart_stream and hls_server:
            logger.info(f"🔄 Reiniciando stream HLS para cámara {camera_id}")
            await hls_server.stop_camera_stream(camera_id)
            
            updated_camera = camera_db.get_camera(camera_id)
            if updated_camera and updated_camera.is_active:
                await hls_server.start_camera_stream(camera_id, updated_camera.rtsp_url)
        
        # Obtener cámara actualizada
        updated_camera = camera_db.get_camera(camera_id)
        camera_dict = updated_camera.to_dict() if updated_camera else {}
        
        # Ocultar credenciales
        if camera_dict and '@' in camera_dict.get('rtsp_url', ''):
            parts = camera_dict['rtsp_url'].split('@')
            camera_dict['rtsp_url'] = f"rtsp://***@{parts[1]}"
        
        logger.info(f"✅ Cámara {camera_id} actualizada exitosamente")
        
        return APIResponse(
            trace_id=f"update-camera-{camera_id}",
            code=200,
            message=f"Cámara {camera_id} actualizada exitosamente",
            data=camera_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.delete("/{camera_id}", response_model=APIResponse)
async def delete_camera(camera_id: int, hard_delete: bool = False):
    """
    Eliminar una cámara.
    
    Args:
        camera_id: ID de la cámara
        hard_delete: Si True, elimina permanentemente. Si False, solo desactiva.
        
    Returns:
        Confirmación de eliminación
    """
    try:
        # Verificar que existe
        existing = camera_db.get_camera(camera_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara {camera_id} no encontrada"
            )
        
        logger.warning(f"🗑️  Eliminando cámara {camera_id} (hard={hard_delete})")
        
        # Detener stream si está corriendo
        if hls_server and hls_server.is_stream_running(camera_id):
            logger.info(f"🛑 Deteniendo stream HLS de cámara {camera_id}")
            await hls_server.stop_camera_stream(camera_id)
        
        # Eliminar de BD
        if hard_delete:
            success = camera_db.hard_delete_camera(camera_id)
            message = "eliminada permanentemente"
        else:
            success = camera_db.delete_camera(camera_id)
            message = "desactivada"
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo eliminar la cámara"
            )
        
        logger.info(f"✅ Cámara {camera_id} {message}")
        
        return APIResponse(
            trace_id=f"delete-camera-{camera_id}",
            code=200,
            message=f"Cámara {camera_id} {message} exitosamente",
            data={"camera_id": camera_id, "hard_delete": hard_delete}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error eliminando cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.post("/{camera_id}/start", response_model=APIResponse)
async def start_camera_stream(camera_id: int):
    """
    Iniciar stream HLS para una cámara.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        Confirmación de inicio de stream
    """
    try:
        camera = camera_db.get_camera(camera_id)
        
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cámara {camera_id} no encontrada"
            )
        
        if not camera.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cámara {camera_id} está desactivada"
            )
        
        if not hls_server:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Servidor HLS no disponible"
            )
        
        logger.info(f"▶️  Iniciando stream para cámara {camera_id}")
        
        success = await hls_server.start_camera_stream(camera_id, camera.rtsp_url)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo iniciar el stream"
            )
        
        return APIResponse(
            trace_id=f"start-stream-{camera_id}",
            code=200,
            message=f"Stream iniciado para cámara {camera_id}",
            data={"camera_id": camera_id, "status": "running"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error iniciando stream de cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.post("/{camera_id}/stop", response_model=APIResponse)
async def stop_camera_stream(camera_id: int):
    """
    Detener stream HLS de una cámara.
    
    Args:
        camera_id: ID de la cámara
        
    Returns:
        Confirmación de detención de stream
    """
    try:
        if not hls_server:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Servidor HLS no disponible"
            )
        
        logger.info(f"⏸️  Deteniendo stream para cámara {camera_id}")
        
        await hls_server.stop_camera_stream(camera_id)
        
        return APIResponse(
            trace_id=f"stop-stream-{camera_id}",
            code=200,
            message=f"Stream detenido para cámara {camera_id}",
            data={"camera_id": camera_id, "status": "stopped"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deteniendo stream de cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )
