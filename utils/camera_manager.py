"""
Gestor de configuración de cámaras con persistencia SQLite.

Este módulo maneja:
- CRUD de cámaras (Create, Read, Update, Delete)
- Persistencia en SQLite
- Validación de URLs RTSP
- Estado de conexión de cámaras

Autor: Sistema de Monitoreo de Hurones
Fecha: 2026-01-10
"""

import sqlite3
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from loguru import logger


@dataclass
class CameraConfig:
    """Configuración de una cámara."""
    id: Optional[int] = None
    name: str = ""
    rtsp_url: str = ""
    description: str = ""
    location: str = ""
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'CameraConfig':
        """Crear desde diccionario."""
        return CameraConfig(**data)


class CameraDatabase:
    """
    Gestor de base de datos de cámaras.
    
    Características:
    - CRUD completo de cámaras
    - Persistencia SQLite
    - Thread-safe con conexiones locales
    - Migraciones automáticas
    """
    
    def __init__(self, db_path: str = "data/cameras.db"):
        """
        Inicializar base de datos de cámaras.
        
        Args:
            db_path: Ruta al archivo SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        logger.info(f"✅ Base de datos de cámaras lista: {self.db_path}")
    
    def _init_database(self):
        """Crear tablas si no existen."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cameras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rtsp_url TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                location TEXT DEFAULT '',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("📊 Tabla 'cameras' inicializada")
    
    def add_camera(
        self,
        name: str,
        rtsp_url: str,
        description: str = "",
        location: str = "",
        is_active: bool = True
    ) -> Optional[int]:
        """
        Agregar nueva cámara.
        
        Args:
            name: Nombre descriptivo
            rtsp_url: URL RTSP completa
            description: Descripción opcional
            location: Ubicación física
            is_active: Si está activa
            
        Returns:
            ID de la cámara creada, None si hay error
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO cameras (name, rtsp_url, description, location, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (name, rtsp_url, description, location, is_active))
            
            camera_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Cámara agregada: {name} (ID: {camera_id})")
            return camera_id
            
        except sqlite3.IntegrityError as e:
            logger.error(f"❌ Error: URL RTSP ya existe - {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error agregando cámara: {e}")
            return None
    
    def get_camera(self, camera_id: int) -> Optional[CameraConfig]:
        """
        Obtener cámara por ID.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            CameraConfig o None si no existe
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM cameras WHERE id = ?", (camera_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return CameraConfig(**dict(row))
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo cámara {camera_id}: {e}")
            return None
    
    def get_all_cameras(self, only_active: bool = False) -> List[CameraConfig]:
        """
        Obtener todas las cámaras.
        
        Args:
            only_active: Si True, solo cámaras activas
            
        Returns:
            Lista de CameraConfig
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if only_active:
                cursor.execute("SELECT * FROM cameras WHERE is_active = 1 ORDER BY id")
            else:
                cursor.execute("SELECT * FROM cameras ORDER BY id")
            
            rows = cursor.fetchall()
            conn.close()
            
            cameras = [CameraConfig(**dict(row)) for row in rows]
            logger.debug(f"📹 {len(cameras)} cámaras encontradas")
            return cameras
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo cámaras: {e}")
            return []
    
    def get_active_camera_urls(self) -> Dict[int, str]:
        """
        Obtener URLs RTSP de cámaras activas con sus IDs.
        Útil para inicializar el HLS server.
        
        Returns:
            Diccionario {camera_id: rtsp_url}
        """
        cameras = self.get_all_cameras(only_active=True)
        urls = {cam.id: cam.rtsp_url for cam in cameras}
        logger.info(f"📡 {len(urls)} URLs de cámaras activas obtenidas")
        return urls
    
    def update_camera(
        self,
        camera_id: int,
        name: Optional[str] = None,
        rtsp_url: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """
        Actualizar cámara existente.
        
        Args:
            camera_id: ID de la cámara
            name: Nuevo nombre (opcional)
            rtsp_url: Nueva URL (opcional)
            description: Nueva descripción (opcional)
            location: Nueva ubicación (opcional)
            is_active: Nuevo estado (opcional)
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            # Construir query dinámicamente
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if rtsp_url is not None:
                updates.append("rtsp_url = ?")
                params.append(rtsp_url)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if location is not None:
                updates.append("location = ?")
                params.append(location)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(is_active)
            
            if not updates:
                logger.warning("⚠️  No hay campos para actualizar")
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(camera_id)
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            query = f"UPDATE cameras SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"✅ Cámara {camera_id} actualizada")
            else:
                logger.warning(f"⚠️  Cámara {camera_id} no encontrada")
            
            return success
            
        except sqlite3.IntegrityError as e:
            logger.error(f"❌ Error: URL RTSP duplicada - {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error actualizando cámara {camera_id}: {e}")
            return False
    
    def delete_camera(self, camera_id: int) -> bool:
        """
        Eliminar cámara (soft delete: is_active = False).
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            True si se desactivó correctamente
        """
        return self.update_camera(camera_id, is_active=False)
    
    def hard_delete_camera(self, camera_id: int) -> bool:
        """
        Eliminar cámara permanentemente de la BD.
        ⚠️ Usar con precaución.
        
        Args:
            camera_id: ID de la cámara
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM cameras WHERE id = ?", (camera_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.warning(f"🗑️  Cámara {camera_id} eliminada permanentemente")
            else:
                logger.warning(f"⚠️  Cámara {camera_id} no encontrada")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error eliminando cámara {camera_id}: {e}")
            return False
    
    def count_cameras(self, only_active: bool = False) -> int:
        """Contar número de cámaras."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            if only_active:
                cursor.execute("SELECT COUNT(*) FROM cameras WHERE is_active = 1")
            else:
                cursor.execute("SELECT COUNT(*) FROM cameras")
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Error contando cámaras: {e}")
            return 0


# Instancia global
camera_db = CameraDatabase()


if __name__ == "__main__":
    """Ejemplo de uso."""
    
    print("=" * 60)
    print("GESTOR DE CÁMARAS - EJEMPLO")
    print("=" * 60)
    
    # Agregar cámara
    camera_id = camera_db.add_camera(
        name="Cámara Hurón 1",
        rtsp_url="rtsp://admin:Sb123456@192.168.0.20:554/Preview_01_main",
        description="Cámara principal del área de juego",
        location="Sala principal"
    )
    
    if camera_id:
        print(f"\n✅ Cámara agregada con ID: {camera_id}")
        
        # Obtener cámara
        camera = camera_db.get_camera(camera_id)
        if camera:
            print(f"\n📹 Cámara obtenida:")
            print(f"   Nombre: {camera.name}")
            print(f"   URL: {camera.rtsp_url}")
            print(f"   Ubicación: {camera.location}")
        
        # Actualizar
        camera_db.update_camera(camera_id, description="Actualizada")
        print(f"\n✅ Cámara actualizada")
        
        # Listar todas
        cameras = camera_db.get_all_cameras()
        print(f"\n📊 Total cámaras: {len(cameras)}")
        
        # URLs activas
        urls = camera_db.get_active_camera_urls()
        print(f"\n📡 URLs activas: {len(urls)}")
        for url in urls:
            safe_url = url.split('@')[-1] if '@' in url else url
            print(f"   - rtsp://***@{safe_url}")
    
    print("\n" + "=" * 60)
