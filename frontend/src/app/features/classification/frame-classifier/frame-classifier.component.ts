import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

interface Detection {
  bbox: number[];
  confidence: number;
  class_name: string;
  entity_type: string;
}

interface FrameInfo {
  id: string;
  filename: string;
  video_name: string;
  frame_number: number;
  timestamp: number;
  detections: Detection[];
  image_path: string;
  classified: boolean;
  classification?: string;
  classification_date?: string;
}

interface ClassificationStats {
  total_frames_available: number;
  total_classified: number;
  unclassified: number;
  progress_percent: number;
  by_behavior: { [key: string]: number };
}

@Component({
  selector: 'app-frame-classifier',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './frame-classifier.component.html',
  styleUrls: ['./frame-classifier.component.css']
})
export class FrameClassifierComponent implements OnInit {
  frames: FrameInfo[] = [];
  currentFrameIndex = 0;
  loading = false;
  analyzing = false;
  error: string | null = null;
  stats: ClassificationStats | null = null;
  
  // Filtros
  showOnlyUnclassified = true;
  showOnlyWithAnimals = false;
  
  // Categorías de comportamiento
  behaviors = [
    { id: 'playing', label: '🎮 Jugando', description: 'Hurón jugando activamente' },
    { id: 'resting', label: '😴 Descansando', description: 'Hurón durmiendo o descansando' },
    { id: 'exploring', label: '🔍 Explorando', description: 'Hurón explorando el entorno' },
    { id: 'eating', label: '🍖 Comiendo', description: 'Hurón comiendo' },
    { id: 'drinking', label: '💧 Bebiendo', description: 'Hurón bebiendo agua' },
    { id: 'unknown', label: '❓ Desconocido', description: 'Comportamiento no claro' },
    { id: 'no_ferret', label: '🚫 Sin hurón', description: 'No hay hurón visible' }
  ];
  
  notes = '';
  
  private apiUrl = 'http://localhost:8000/api/classification';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadFrames();
    this.loadStats();
  }
  
  get currentFrame(): FrameInfo | null {
    return this.frames.length > 0 ? this.frames[this.currentFrameIndex] : null;
  }
  
  get progress(): number {
    return this.frames.length > 0 
      ? ((this.currentFrameIndex + 1) / this.frames.length) * 100 
      : 0;
  }

  async loadFrames(): Promise<void> {
    this.loading = true;
    this.error = null;
    
    try {
      const params: any = {
        limit: 100,
        skip: 0
      };
      
      if (this.showOnlyUnclassified) {
        params.classified = false;
      }
      
      if (this.showOnlyWithAnimals) {
        params.has_animals = true;
      }
      
      this.http.get<FrameInfo[]>(
        `${this.apiUrl}/frames`,
        { params }
      ).subscribe({
        next: (data) => {
          this.frames = data || [];
          this.currentFrameIndex = 0;
          
          if (this.frames.length === 0) {
            this.error = 'No hay frames disponibles para clasificar';
          }
          this.loading = false;
        },
        error: (err: any) => {
          this.error = err.message || 'Error cargando frames';
          console.error('Error loading frames:', err);
          this.loading = false;
        }
      });
    } catch (err: any) {
      this.error = err.message || 'Error cargando frames';
      console.error('Error loading frames:', err);
      this.loading = false;
    }
  }
  
  loadStats(): void {
    this.http.get<ClassificationStats>(
      `${this.apiUrl}/stats`
    ).subscribe({
      next: (data) => {
        this.stats = data;
      },
      error: (err) => {
        console.error('Error loading stats:', err);
      }
    });
  }

  classifyFrame(behavior: string): void {
    const frame = this.currentFrame;
    if (!frame) return;
    
    this.loading = true;
    this.error = null;
    
    this.http.post(
      `${this.apiUrl}/classify`,
      {
        frame_id: frame.id,
        behavior: behavior,
        notes: this.notes || null
      }
    ).subscribe({
      next: () => {
        // Marcar frame como clasificado
        frame.classified = true;
        frame.classification = behavior;
        
        // Limpiar notas
        this.notes = '';
        
        // Ir al siguiente frame
        this.nextFrame();
        
        // Actualizar stats
        this.loadStats();
        
        this.loading = false;
      },
      error: (err: any) => {
        this.error = err.error?.detail || 'Error guardando clasificación';
        console.error('Error classifying frame:', err);
        this.loading = false;
      }
    });
  }

  async nextFrame(): Promise<void> {
    if (this.currentFrameIndex < this.frames.length - 1) {
      this.currentFrameIndex++;
    } else {
      // Si llegamos al final, recargar frames
      await this.loadFrames();
    }
  }

  async previousFrame(): Promise<void> {
    if (this.currentFrameIndex > 0) {
      this.currentFrameIndex--;
    }
  }

  async skipFrame(): Promise<void> {
    await this.nextFrame();
  }

  toggleUnclassifiedFilter(): void {
    this.showOnlyUnclassified = !this.showOnlyUnclassified;
    this.loadFrames();
  }
  
  toggleAnimalFilter(): void {
    this.showOnlyWithAnimals = !this.showOnlyWithAnimals;
    this.loadFrames();
  }
  
  triggerAnalysis(): void {
    if (this.analyzing) return;
    
    this.analyzing = true;
    this.error = null;
    
    this.http.post<any>(`${this.apiUrl}/analyze`, {}).subscribe({
      next: (response) => {
        console.log('Análisis iniciado:', response);
        alert(`✅ ${response.message}\n\n` +
              `Tiempo estimado: ${response.estimated_time}\n\n` +
              `${response.info}`);
        
        // Recargar frames después de 2 minutos
        setTimeout(() => {
          this.analyzing = false;
          this.loadFrames();
          this.loadStats();
          alert('🎉 Análisis completado. Los nuevos frames ya están disponibles.');
        }, 120000); // 2 minutos
      },
      error: (err) => {
        console.error('Error al iniciar análisis:', err);
        this.error = 'Error al iniciar el análisis: ' + (err.error?.detail || err.message);
        this.analyzing = false;
        alert('❌ Error al iniciar el análisis. Ver consola para detalles.');
      }
    });
  }
  
  getImageUrl(frame: FrameInfo): string {
    return `${this.apiUrl}/frames/${frame.filename}`;
  }
  
  getBehaviorLabel(behaviorId: string): string {
    const behavior = this.behaviors.find(b => b.id === behaviorId);
    return behavior ? behavior.label : behaviorId;
  }
  
  formatTimestamp(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
  
  // Atajos de teclado
  onKeyPress(event: KeyboardEvent): void {
    if (this.loading) return;
    
    switch (event.key) {
      case '1':
        this.classifyFrame('playing');
        break;
      case '2':
        this.classifyFrame('resting');
        break;
      case '3':
        this.classifyFrame('exploring');
        break;
      case '4':
        this.classifyFrame('eating');
        break;
      case '5':
        this.classifyFrame('drinking');
        break;
      case '0':
        this.classifyFrame('unknown');
        break;
      case 'ArrowLeft':
        this.previousFrame();
        break;
      case 'ArrowRight':
      case ' ':
        event.preventDefault();
        this.skipFrame();
        break;
    }
  }
}
