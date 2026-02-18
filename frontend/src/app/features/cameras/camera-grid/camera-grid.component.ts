/**
 * Componente para mostrar mosaico de cámaras en tiempo real
 */

import { Component, OnInit, OnDestroy, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatBadgeModule } from '@angular/material/badge';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatButtonModule } from '@angular/material/button';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { ApiService } from '../../../core/services/api.service';
import { WebSocketService } from '../../../core/services/websocket.service';
import { MockDataService } from '../../../core/services/mock-data.service';
import { Camera } from '../../../core/models/camera.model';

// Definir tipo para HLS.js
declare var Hls: any;

@Component({
  selector: 'app-camera-grid',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatBadgeModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
    MatButtonModule
  ],
  templateUrl: './camera-grid.component.html',
  styleUrls: ['./camera-grid.component.scss']
})
export class CameraGridComponent implements OnInit, AfterViewInit, OnDestroy {
  cameras: Camera[] = [];
  loading = true;
  error: string | null = null;
  
  private destroy$ = new Subject<void>();
  private hlsPlayers: Map<number, any> = new Map(); // HLS.js players

  constructor(
    private apiService: ApiService,
    private wsService: WebSocketService,
    private mockDataService: MockDataService
  ) {}

  ngOnInit(): void {
    this.loadCameras();
    this.subscribeToUpdates();
  }

  ngAfterViewInit(): void {
    // Inicializar players HLS después de que la vista esté lista
    setTimeout(() => {
      this.initializeHLSPlayers();
    }, 500);
  }

  ngOnDestroy(): void {
    // Destruir todos los players HLS
    this.hlsPlayers.forEach((hls, cameraId) => {
      if (hls) {
        hls.destroy();
      }
    });
    this.hlsPlayers.clear();
    
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Cargar información inicial de cámaras
   */
  private loadCameras(): void {
    this.apiService.getCameras()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (cameras) => {
          this.cameras = cameras;
          this.loading = false;
        },
        error: (error) => {
          this.error = 'Error cargando cámaras';
          this.loading = false;
          console.error(error);
        }
      });
  }
  
  /**
   * Inicializar reproductores HLS para todas las cámaras activas
   */
  private initializeHLSPlayers(): void {
    this.cameras.forEach(camera => {
      // Inicializar HLS para todas las cámaras activas, sin importar el status
      // El HLS player manejará automáticamente si el stream está disponible o no
      this.initializeHLSPlayer(camera.id);
    });
  }

  /**
   * Inicializar reproductor HLS para una cámara específica
   */
  private initializeHLSPlayer(cameraId: number): void {
    const videoElement = document.getElementById(`video-${cameraId}`) as HTMLVideoElement;
    
    if (!videoElement) {
      console.warn(`Video element not found for camera ${cameraId}`);
      return;
    }

    // IMPORTANTE: Asegurar que el video esté muted para autoplay
    videoElement.muted = true;
    videoElement.playsInline = true;

    const hlsUrl = this.apiService.getHLSStreamUrl(cameraId);
    console.log(`🎬 Initializing HLS player for camera ${cameraId}`);
    console.log(`📺 HLS URL: ${hlsUrl}`);

    // Verificar si el navegador soporta HLS nativamente (Safari)
    if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
      console.log(`✅ Using native HLS support for camera ${cameraId}`);
      console.log(`🔗 Setting video.src to: ${hlsUrl}`);
      videoElement.src = hlsUrl;
      
      // Event listeners para debugging
      videoElement.addEventListener('loadstart', () => console.log(`📥 Video loadstart for camera ${cameraId}`));
      videoElement.addEventListener('loadeddata', () => console.log(`✅ Video loaded for camera ${cameraId}`));
      videoElement.addEventListener('error', (e) => {
        console.error(`❌ Video error for camera ${cameraId}:`, e);
        console.error(`   Error code: ${videoElement.error?.code}`);
        console.error(`   Error message: ${videoElement.error?.message}`);
      });
      
      // Intentar reproducir con manejo de errores
      videoElement.play().catch(err => {
        console.warn(`Autoplay bloqueado para cámara ${cameraId}:`, err.name);
        
        // Intentar reproducir en el primer click del usuario
        const playOnInteraction = () => {
          videoElement.play().then(() => {
            console.log(`Video iniciado para cámara ${cameraId} tras interacción`);
            document.removeEventListener('click', playOnInteraction);
          });
        };
        
        document.addEventListener('click', playOnInteraction, { once: true });
      });
    } 
    // Usar HLS.js para otros navegadores
    else if (typeof Hls !== 'undefined' && Hls.isSupported()) {
      console.log(`Using HLS.js for camera ${cameraId}`);
      
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 10,
        maxBufferLength: 20,
        maxMaxBufferLength: 30,
        liveDurationInfinity: true,
        liveBackBufferLength: 0
      });

      hls.loadSource(hlsUrl);
      hls.attachMedia(videoElement);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        console.log(`HLS manifest loaded for camera ${cameraId}`);
        
        // Intentar reproducir con manejo de errores
        videoElement.play().catch(err => {
          console.warn(`Autoplay bloqueado para cámara ${cameraId}:`, err.name);
          
          // Intentar reproducir en el primer click del usuario
          const playOnInteraction = () => {
            videoElement.play().then(() => {
              console.log(`Video iniciado para cámara ${cameraId} tras interacción`);
              document.removeEventListener('click', playOnInteraction);
            });
          };
          
          document.addEventListener('click', playOnInteraction, { once: true });
        });
      });

      hls.on(Hls.Events.ERROR, (event: any, data: any) => {
        console.error(`HLS error for camera ${cameraId}:`, data);
        
        // Si es un error fatal, intentar recuperar
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.log(`Attempting to recover from network error for camera ${cameraId}`);
              hls.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.log(`Attempting to recover from media error for camera ${cameraId}`);
              hls.recoverMediaError();
              break;
            default:
              console.error(`Cannot recover from fatal error for camera ${cameraId}`);
              hls.destroy();
              break;
          }
        }
      });

      this.hlsPlayers.set(cameraId, hls);
    } else {
      console.error(`HLS is not supported in this browser for camera ${cameraId}`);
    }
  }

  /**
   * Suscribirse a actualizaciones en tiempo real
   */
  private subscribeToUpdates(): void {
    this.wsService.connectData()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (message) => {
          // Manejar actualización de estado que incluye cámaras
          if (message.type === 'state_update' && message.data?.cameras) {
            this.updateCamerasFromWebSocket(message.data.cameras);
          }
          // También manejar actualizaciones individuales de cámara
          else if (message.type === 'camera_update') {
            this.updateCamera(message.data);
          }
        },
        error: (error) => console.error('WebSocket error:', error)
      });
  }

  /**
   * Actualizar todas las cámaras desde datos del WebSocket
   */
  private updateCamerasFromWebSocket(camerasData: any): void {
    // Actualizar cada cámara existente con los nuevos datos
    Object.keys(camerasData).forEach(cameraIdStr => {
      const cameraId = parseInt(cameraIdStr);
      const index = this.cameras.findIndex(c => c.id === cameraId);
      if (index !== -1) {
        const newData = camerasData[cameraIdStr];
        this.cameras[index] = {
          ...this.cameras[index],
          status: newData.status,
          fps: newData.fps,
          resolution: newData.resolution || this.cameras[index].resolution
        };
      }
    });
  }

  /**
   * Actualizar datos de una cámara individual
   */
  private updateCamera(data: any): void {
    const index = this.cameras.findIndex(c => c.id === data.id);
    if (index !== -1) {
      this.cameras[index] = { ...this.cameras[index], ...data };
    }
  }

  /**
   * Obtener clase CSS según el estado
   */
  getStatusClass(status: string): string {
    return `status-${status}`;
  }

  /**
   * Obtener icono según el estado
   */
  getStatusIcon(status: string): string {
    const icons: Record<string, string> = {
      'connected': 'videocam',
      'disconnected': 'videocam_off',
      'error': 'error',
      'connecting': 'sync'
    };
    return icons[status] || 'help';
  }

  /**
   * Obtener texto de estado en español
   */
  getStatusText(status: string): string {
    const texts: Record<string, string> = {
      'connected': 'Conectada',
      'disconnected': 'Desconectada',
      'error': 'Error',
      'connecting': 'Conectando...'
    };
    return texts[status] || status;
  }

  /**
   * Recargar cámaras
   */
  reload(): void {
    this.loading = true;
    this.error = null;
    this.loadCameras();
  }

  /**
   * Obtener número de cámaras conectadas
   */
  getConnectedCount(): number {
    return this.cameras.filter(c => c.status === 'connected').length;
  }

  /**
   * Obtener número de cámaras desconectadas
   */
  getDisconnectedCount(): number {
    return this.cameras.filter(c => c.status === 'disconnected').length;
  }

  /**
   * Obtener imagen placeholder de cámara
   */
  getCameraPlaceholder(cameraId: number): string {
    return this.mockDataService.getCameraPlaceholderUrl(cameraId);
  }

}

