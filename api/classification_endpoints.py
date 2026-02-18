"""
API Endpoints para clasificación de frames.

Permite al usuario ver y clasificar frames extraídos de los videos
para entrenar el modelo de IA.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import json
import sqlite3

router = APIRouter(prefix="/api/classification", tags=["classification"])

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
FRAMES_DIR = DATA_DIR / "frames_for_classification"
RESULTS_DIR = DATA_DIR / "analysis_results"
DB_PATH = DATA_DIR / "classifications.db"


# ==================== MODELS ====================

class Detection(BaseModel):
    """Detección en un frame."""
    bbox: List[float]
    confidence: float
    class_name: str
    entity_type: str


class FrameInfo(BaseModel):
    """Información de un frame."""
    id: str
    filename: str
    video_name: str
    frame_number: int
    timestamp: float
    detections: List[Detection]
    image_path: str
    classified: bool = False
    classification: Optional[str] = None
    classification_date: Optional[str] = None


class Classification(BaseModel):
    """Clasificación de un frame por el usuario."""
    frame_id: str
    behavior: str  # "playing", "resting", "exploring", "eating", "unknown"
    notes: Optional[str] = None


# ==================== DATABASE ====================

def init_db():
    """Inicializar base de datos de clasificaciones."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frame_classifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frame_id TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            video_name TEXT NOT NULL,
            frame_number INTEGER NOT NULL,
            timestamp REAL NOT NULL,
            behavior TEXT NOT NULL,
            notes TEXT,
            classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


# Inicializar DB al cargar módulo
init_db()


# ==================== ENDPOINTS ====================

@router.get("/frames", response_model=List[FrameInfo])
async def get_frames(
    limit: int = 50,
    skip: int = 0,
    classified: Optional[bool] = None,
    video_name: Optional[str] = None,
    has_animals: Optional[bool] = None
):
    """
    Listar frames disponibles para clasificación.
    
    Args:
        limit: Número máximo de frames a retornar
        skip: Número de frames a saltar (paginación)
        classified: Filtrar por estado de clasificación
        video_name: Filtrar por nombre de video
        has_animals: Filtrar solo frames con detecciones de animales (ferret, cat, dog)
    
    Returns:
        Lista de frames con sus detecciones
    """
    try:
        frames = []
        
        # Listar archivos de análisis
        analysis_files = sorted(RESULTS_DIR.glob("*_analysis.json"))
        
        if not analysis_files:
            return []
        
        # Cargar clasificaciones existentes
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT frame_id, behavior, classified_at FROM frame_classifications")
        classifications = {row[0]: {"behavior": row[1], "date": row[2]} for row in cursor.fetchall()}
        conn.close()
        
        # Procesar cada archivo de análisis
        for analysis_file in analysis_files:
            with open(analysis_file, 'r') as f:
                data = json.load(f)
            
            video_name_parsed = data.get("video_name", "")
            
            # Filtrar por video si se especifica
            if video_name and video_name not in video_name_parsed:
                continue
            
            # Procesar frames guardados
            for frame_info in data.get("frames_saved", []):
                frame_id = f"{video_name_parsed}_{frame_info['frame']}"
                
                # Verificar si está clasificado
                is_classified = frame_id in classifications
                
                # Filtrar por estado de clasificación
                if classified is not None:
                    if classified and not is_classified:
                        continue
                    if not classified and is_classified:
                        continue
                
                # Obtener detecciones del frame
                frame_detections = []
                for det_frame in data.get("detections_per_frame", []):
                    if det_frame["frame"] == frame_info["frame"]:
                        frame_detections = [
                            Detection(**det) for det in det_frame["detections"]
                        ]
                        break
                
                # Filtrar por detecciones de animales si se especifica
                if has_animals is not None:
                    has_animal_detection = any(
                        det.entity_type in ["ferret", "cat", "dog"] 
                        for det in frame_detections
                    )
                    
                    if has_animals and not has_animal_detection:
                        continue
                    if not has_animals and has_animal_detection:
                        continue
                
                # Crear FrameInfo
                frame_obj = FrameInfo(
                    id=frame_id,
                    filename=frame_info["filename"],
                    video_name=video_name_parsed,
                    frame_number=frame_info["frame"],
                    timestamp=frame_info["timestamp"],
                    detections=frame_detections,
                    image_path=f"/api/classification/frames/{frame_info['filename']}",
                    classified=is_classified
                )
                
                if is_classified:
                    frame_obj.classification = classifications[frame_id]["behavior"]
                    frame_obj.classification_date = classifications[frame_id]["date"]
                
                frames.append(frame_obj)
        
        # Paginación
        frames = frames[skip:skip + limit]
        
        return frames
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/frames/{filename}")
async def get_frame_image(filename: str):
    """
    Obtener imagen de un frame.
    
    Args:
        filename: Nombre del archivo de imagen
    
    Returns:
        Archivo de imagen
    """
    from fastapi.responses import FileResponse
    
    frame_path = FRAMES_DIR / filename
    
    if not frame_path.exists():
        raise HTTPException(status_code=404, detail="Frame no encontrado")
    
    return FileResponse(frame_path, media_type="image/jpeg")


@router.post("/classify")
async def classify_frame(classification: Classification):
    """
    Clasificar un frame.
    
    Args:
        classification: Datos de clasificación
    
    Returns:
        Confirmación de clasificación guardada
    """
    try:
        # Validar behavior
        valid_behaviors = ["playing", "resting", "exploring", "eating", "drinking", "unknown", "no_ferret"]
        
        if classification.behavior not in valid_behaviors:
            raise HTTPException(
                status_code=400,
                detail=f"Behavior inválido. Debe ser uno de: {valid_behaviors}"
            )
        
        # Parsear frame_id para obtener info
        parts = classification.frame_id.rsplit('_', 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="frame_id inválido")
        
        video_name = parts[0]
        frame_number = int(parts[1])
        
        # Buscar frame en análisis
        filename = None
        timestamp = 0.0
        
        for analysis_file in RESULTS_DIR.glob("*_analysis.json"):
            with open(analysis_file, 'r') as f:
                data = json.load(f)
            
            if data.get("video_name") == video_name:
                for frame_info in data.get("frames_saved", []):
                    if frame_info["frame"] == frame_number:
                        filename = frame_info["filename"]
                        timestamp = frame_info["timestamp"]
                        break
                break
        
        if not filename:
            raise HTTPException(status_code=404, detail="Frame no encontrado en análisis")
        
        # Guardar clasificación en BD
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO frame_classifications
            (frame_id, filename, video_name, frame_number, timestamp, behavior, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            classification.frame_id,
            filename,
            video_name,
            frame_number,
            timestamp,
            classification.behavior,
            classification.notes
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "frame_id": classification.frame_id,
            "behavior": classification.behavior,
            "message": "Clasificación guardada correctamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_classification_stats():
    """Obtener estadísticas de clasificación."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total clasificaciones
        cursor.execute("SELECT COUNT(*) FROM frame_classifications")
        total_classified = cursor.fetchone()[0]
        
        # Por behavior
        cursor.execute("""
            SELECT behavior, COUNT(*) as count
            FROM frame_classifications
            GROUP BY behavior
            ORDER BY count DESC
        """)
        by_behavior = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Total frames disponibles
        total_frames = 0
        for analysis_file in RESULTS_DIR.glob("*_analysis.json"):
            with open(analysis_file, 'r') as f:
                data = json.load(f)
                total_frames += len(data.get("frames_saved", []))
        
        conn.close()
        
        return {
            "total_frames_available": total_frames,
            "total_classified": total_classified,
            "unclassified": total_frames - total_classified,
            "progress_percent": (total_classified / total_frames * 100) if total_frames > 0 else 0,
            "by_behavior": by_behavior
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/classify/{frame_id}")
async def delete_classification(frame_id: str):
    """Eliminar clasificación de un frame."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM frame_classifications WHERE frame_id = ?", (frame_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Clasificación no encontrada")
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Clasificación eliminada"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def trigger_analysis():
    """
    Ejecutar análisis de videos a demanda.
    
    Ejecuta el script de análisis automático para procesar videos nuevos
    sin esperar al cron job.
    
    Returns:
        Estado de la ejecución del análisis
    """
    import subprocess
    import threading
    from datetime import datetime
    
    def run_analysis():
        """Ejecutar análisis en background."""
        try:
            script_path = "/Users/sbriceno/analizar_videos.sh"
            result = subprocess.run(
                [script_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos máximo
            )
            
            log_path = Path(__file__).parent.parent / "logs" / "manual_analysis.log"
            with open(log_path, "a") as f:
                f.write(f"\n[{datetime.now()}] Análisis manual ejecutado\n")
                if result.returncode == 0:
                    f.write("✅ Completado exitosamente\n")
                else:
                    f.write(f"❌ Error: {result.stderr}\n")
        except Exception as e:
            log_path = Path(__file__).parent.parent / "logs" / "manual_analysis.log"
            with open(log_path, "a") as f:
                f.write(f"\n[{datetime.now()}] ❌ Error: {str(e)}\n")
    
    try:
        # Verificar que el script existe
        script_path = Path("/Users/sbriceno/analizar_videos.sh")
        if not script_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Script de análisis no encontrado. Ejecutar: AUTOMATIZAR_ANALISIS.md"
            )
        
        # Ejecutar análisis en background (no bloqueante)
        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()
        
        return {
            "success": True,
            "message": "Análisis iniciado en segundo plano",
            "status": "processing",
            "estimated_time": "1-3 minutos",
            "info": "Refresca la página en unos minutos para ver los nuevos frames"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
