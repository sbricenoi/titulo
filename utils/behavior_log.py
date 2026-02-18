"""
Behavior Log - Sistema de bitácora persistente para comportamientos de hurones.

Este módulo gestiona una base de datos SQLite que registra todos los comportamientos
detectados, asociados a cada individuo con timestamp, duración y confianza.

Autor: Sistema de Monitoreo de Hurones
Fecha: 2025-11-09
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger
import json


@dataclass
class BehaviorEntry:
    """
    Entrada de comportamiento en la bitácora.
    
    Attributes:
        id: ID único de la entrada (auto-incrementado)
        individual_id: ID del individuo (hurón o persona)
        entity_type: Tipo de entidad ("ferret" o "person")
        behavior: Nombre del comportamiento
        confidence: Confianza de la detección (0-1)
        timestamp: Timestamp ISO8601
        duration: Duración en segundos (opcional)
        camera_id: ID de la cámara donde se detectó
        metadata: Datos adicionales en formato JSON
    """
    id: Optional[int]
    individual_id: str
    entity_type: str = "ferret"  # "ferret" o "person"
    behavior: str = ""
    confidence: float = 0.0
    timestamp: str = ""
    duration: Optional[float] = None
    camera_id: Optional[int] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario."""
        return {
            "id": self.id,
            "individual_id": self.individual_id,
            "entity_type": self.entity_type,
            "behavior": self.behavior,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "camera_id": self.camera_id,
            "metadata": self.metadata
        }


class BehaviorLog:
    """
    Gestor de bitácora de comportamientos.
    
    Mantiene una base de datos SQLite con todos los comportamientos detectados,
    permitiendo consultas por individuo, comportamiento, rango temporal, etc.
    
    Ejemplo:
        >>> log = BehaviorLog("data/behavior_log.db")
        >>> log.add_behavior("F0", "eating", 0.95)
        >>> entries = log.get_by_individual("F0", limit=10)
        >>> stats = log.get_statistics("F0")
    """
    
    def __init__(self, db_path: str = "data/behavior_log.db"):
        """
        Inicializar bitácora de comportamientos.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = Path(db_path)
        
        # Crear directorio si no existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar base de datos
        self._init_database()
        
        logger.info(f"BehaviorLog inicializado: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtener conexión a la base de datos."""
        conn = sqlite3.Connection(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
        return conn
    
    def _init_database(self):
        """Inicializar esquema de base de datos."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Tabla principal de comportamientos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS behaviors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                individual_id TEXT NOT NULL,
                entity_type TEXT NOT NULL DEFAULT 'ferret',
                behavior TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp TEXT NOT NULL,
                duration REAL,
                camera_id INTEGER,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Índices para mejorar rendimiento de consultas
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_individual 
            ON behaviors(individual_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_behavior 
            ON behaviors(behavior)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON behaviors(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_individual_timestamp 
            ON behaviors(individual_id, timestamp)
        """)
        
        conn.commit()
        conn.close()
        
        logger.debug("Esquema de base de datos inicializado")
    
    def add_behavior(
        self,
        individual_id: str,
        behavior: str,
        confidence: float,
        timestamp: Optional[str] = None,
        duration: Optional[float] = None,
        camera_id: Optional[int] = None,
        metadata: Optional[Dict] = None,
        entity_type: str = "ferret"
    ) -> int:
        """
        Agregar comportamiento a la bitácora.
        
        Args:
            individual_id: ID del individuo (hurón o persona)
            behavior: Nombre del comportamiento
            confidence: Confianza de la detección (0-1)
            timestamp: Timestamp ISO8601 (None = ahora)
            duration: Duración en segundos
            camera_id: ID de la cámara
            metadata: Datos adicionales
            entity_type: Tipo de entidad ("ferret" o "person")
            
        Returns:
            ID de la entrada creada
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Serializar metadata a JSON si existe
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT INTO behaviors 
            (individual_id, entity_type, behavior, confidence, timestamp, duration, camera_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (individual_id, entity_type, behavior, confidence, timestamp, duration, camera_id, metadata_json))
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.debug(
            f"Comportamiento registrado: {individual_id} - {behavior} "
            f"(conf={confidence:.2f}, id={entry_id})"
        )
        
        return entry_id
    
    def get_by_individual(
        self,
        individual_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: str = "timestamp DESC"
    ) -> List[BehaviorEntry]:
        """
        Obtener comportamientos de un individuo.
        
        Args:
            individual_id: ID del hurón
            limit: Número máximo de resultados
            offset: Offset para paginación
            order_by: Ordenamiento (ej: "timestamp DESC")
            
        Returns:
            Lista de entradas de comportamiento
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = f"""
            SELECT * FROM behaviors 
            WHERE individual_id = ?
            ORDER BY {order_by}
        """
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        cursor.execute(query, (individual_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_entry(row) for row in rows]
    
    def get_by_behavior(
        self,
        behavior: str,
        individual_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[BehaviorEntry]:
        """
        Obtener registros de un comportamiento específico.
        
        Args:
            behavior: Nombre del comportamiento
            individual_id: Filtrar por individuo (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Lista de entradas
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if individual_id:
            query = """
                SELECT * FROM behaviors 
                WHERE behavior = ? AND individual_id = ?
                ORDER BY timestamp DESC
            """
            params = (behavior, individual_id)
        else:
            query = """
                SELECT * FROM behaviors 
                WHERE behavior = ?
                ORDER BY timestamp DESC
            """
            params = (behavior,)
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_entry(row) for row in rows]
    
    def get_by_time_range(
        self,
        start_time: str,
        end_time: str,
        individual_id: Optional[str] = None
    ) -> List[BehaviorEntry]:
        """
        Obtener comportamientos en un rango de tiempo.
        
        Args:
            start_time: Timestamp inicio (ISO8601)
            end_time: Timestamp fin (ISO8601)
            individual_id: Filtrar por individuo (opcional)
            
        Returns:
            Lista de entradas
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if individual_id:
            query = """
                SELECT * FROM behaviors 
                WHERE timestamp BETWEEN ? AND ? AND individual_id = ?
                ORDER BY timestamp ASC
            """
            params = (start_time, end_time, individual_id)
        else:
            query = """
                SELECT * FROM behaviors 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            """
            params = (start_time, end_time)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_entry(row) for row in rows]
    
    def get_recent(
        self,
        minutes: int = 60,
        individual_id: Optional[str] = None
    ) -> List[BehaviorEntry]:
        """
        Obtener comportamientos recientes.
        
        Args:
            minutes: Minutos hacia atrás desde ahora
            individual_id: Filtrar por individuo (opcional)
            
        Returns:
            Lista de entradas
        """
        start_time = (datetime.now() - timedelta(minutes=minutes)).isoformat()
        end_time = datetime.now().isoformat()
        
        return self.get_by_time_range(start_time, end_time, individual_id)
    
    def get_statistics(
        self,
        individual_id: str,
        time_range_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Obtener estadísticas de comportamiento de un individuo.
        
        Args:
            individual_id: ID del hurón
            time_range_hours: Horas hacia atrás (None = todo el tiempo)
            
        Returns:
            Dict con estadísticas por comportamiento
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Query base
        query = """
            SELECT 
                behavior,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence,
                AVG(COALESCE(duration, 0)) as avg_duration
            FROM behaviors
            WHERE individual_id = ?
        """
        
        params = [individual_id]
        
        # Filtrar por tiempo si se especifica
        if time_range_hours:
            start_time = (datetime.now() - timedelta(hours=time_range_hours)).isoformat()
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        query += " GROUP BY behavior"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Obtener total de registros
        cursor.execute(
            "SELECT COUNT(*) FROM behaviors WHERE individual_id = ?",
            (individual_id,)
        )
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Construir diccionario de estadísticas
        stats = {
            "individual_id": individual_id,
            "total_behaviors": total_count,
            "time_range_hours": time_range_hours,
            "behaviors": {}
        }
        
        for row in rows:
            behavior = row["behavior"]
            stats["behaviors"][behavior] = {
                "count": row["count"],
                "percentage": (row["count"] / total_count * 100) if total_count > 0 else 0,
                "avg_confidence": row["avg_confidence"],
                "avg_duration": row["avg_duration"]
            }
        
        return stats
    
    def get_all_individuals(self) -> List[str]:
        """
        Obtener lista de todos los individuos registrados.
        
        Returns:
            Lista de IDs de individuos
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT individual_id 
            FROM behaviors 
            ORDER BY individual_id
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row["individual_id"] for row in rows]
    
    def get_last_behavior(
        self,
        individual_id: str
    ) -> Optional[BehaviorEntry]:
        """
        Obtener último comportamiento registrado de un individuo.
        
        Args:
            individual_id: ID del hurón
            
        Returns:
            Última entrada o None
        """
        entries = self.get_by_individual(individual_id, limit=1)
        return entries[0] if entries else None
    
    def delete_old_entries(self, days: int = 90) -> int:
        """
        Eliminar entradas antiguas (mantenimiento).
        
        Args:
            days: Días de antigüedad para eliminar
            
        Returns:
            Número de entradas eliminadas
        """
        cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM behaviors 
            WHERE timestamp < ?
        """, (cutoff_time,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Eliminadas {deleted_count} entradas antiguas (>{days} días)")
        
        return deleted_count
    
    def get_count(self, individual_id: Optional[str] = None) -> int:
        """
        Obtener conteo total de registros.
        
        Args:
            individual_id: Filtrar por individuo (opcional)
            
        Returns:
            Número de registros
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if individual_id:
            cursor.execute(
                "SELECT COUNT(*) FROM behaviors WHERE individual_id = ?",
                (individual_id,)
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM behaviors")
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def _row_to_entry(self, row: sqlite3.Row) -> BehaviorEntry:
        """Convertir fila de BD a BehaviorEntry."""
        metadata = json.loads(row["metadata"]) if row["metadata"] else None
        
        # Manejar retrocompatibilidad con bases de datos antiguas sin entity_type
        try:
            entity_type = row["entity_type"]
        except (KeyError, IndexError):
            entity_type = "ferret"  # Default para registros antiguos
        
        return BehaviorEntry(
            id=row["id"],
            individual_id=row["individual_id"],
            entity_type=entity_type,
            behavior=row["behavior"],
            confidence=row["confidence"],
            timestamp=row["timestamp"],
            duration=row["duration"],
            camera_id=row["camera_id"],
            metadata=metadata
        )
    
    def export_to_json(
        self,
        output_file: str,
        individual_id: Optional[str] = None
    ):
        """
        Exportar bitácora a archivo JSON.
        
        Args:
            output_file: Ruta del archivo de salida
            individual_id: Filtrar por individuo (opcional)
        """
        if individual_id:
            entries = self.get_by_individual(individual_id)
        else:
            # Obtener todas las entradas
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM behaviors ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            conn.close()
            entries = [self._row_to_entry(row) for row in rows]
        
        # Convertir a diccionarios
        data = [entry.to_dict() for entry in entries]
        
        # Guardar a JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Bitácora exportada a {output_file} ({len(data)} entradas)")


# ==================== EJEMPLO DE USO ====================
if __name__ == "__main__":
    """Ejemplo de uso de BehaviorLog."""
    
    from loguru import logger
    import time
    
    # Configurar logging
    logger.add("behavior_log_test.log", rotation="10 MB")
    
    # Crear bitácora
    log = BehaviorLog("test_behavior_log.db")
    
    logger.info("Agregando comportamientos de prueba...")
    
    # Simular comportamientos de 2 hurones
    individuals = ["F0", "F1"]
    behaviors = ["eating", "sleeping", "running", "walking", "idle"]
    
    import random
    
    for _ in range(50):
        individual = random.choice(individuals)
        behavior = random.choice(behaviors)
        confidence = random.uniform(0.6, 0.99)
        duration = random.uniform(5.0, 30.0)
        camera_id = random.randint(0, 1)
        
        log.add_behavior(
            individual_id=individual,
            behavior=behavior,
            confidence=confidence,
            duration=duration,
            camera_id=camera_id
        )
    
    logger.info("\nConsultando bitácora...")
    
    # Últimos 10 comportamientos de F0
    logger.info("\nÚltimos comportamientos de F0:")
    entries = log.get_by_individual("F0", limit=10)
    for entry in entries:
        logger.info(f"  {entry.behavior} - conf={entry.confidence:.2f} - {entry.timestamp}")
    
    # Estadísticas de F0
    logger.info("\nEstadísticas de F0:")
    stats = log.get_statistics("F0")
    logger.info(f"  Total registros: {stats['total_behaviors']}")
    for behavior, data in stats['behaviors'].items():
        logger.info(
            f"  {behavior}: {data['count']} veces ({data['percentage']:.1f}%), "
            f"conf promedio={data['avg_confidence']:.2f}"
        )
    
    # Todos los individuos
    logger.info("\nIndividuos registrados:")
    individuals = log.get_all_individuals()
    for ind in individuals:
        count = log.get_count(ind)
        logger.info(f"  {ind}: {count} registros")
    
    # Exportar a JSON
    log.export_to_json("bitacora_export.json", individual_id="F0")
    logger.info("\nBitácora exportada a bitacora_export.json")
    
    logger.info("\nTest completado")

