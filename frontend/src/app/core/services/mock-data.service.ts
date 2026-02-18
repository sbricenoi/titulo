/**
 * Servicio Mock para generar datos dummy del dashboard
 */

import { Injectable } from '@angular/core';
import { Observable, interval, BehaviorSubject } from 'rxjs';
import { map } from 'rxjs/operators';
import { Camera } from '../models/camera.model';
import { TrackedIndividual } from '../models/individual.model';
import { SystemMetrics } from '../models/metrics.model';

@Injectable({
  providedIn: 'root'
})
export class MockDataService {
  private individualsSubject = new BehaviorSubject<TrackedIndividual[]>([]);
  private frameCounter = 0;

  constructor() {
    this.initializeMockData();
    this.startSimulation();
  }

  /**
   * Obtener cámaras mock
   */
  getMockCameras(): Observable<Camera[]> {
    const cameras: Camera[] = [
      {
        id: 0,
        name: 'Cámara Superior',
        status: 'connected',
        fps: 30.2 + Math.random() * 0.5,
        resolution: [1920, 1080],
        lastFrameTime: new Date().toISOString()
      },
      {
        id: 1,
        name: 'Cámara Inferior',
        status: 'connected',
        fps: 29.8 + Math.random() * 0.5,
        resolution: [1920, 1080],
        lastFrameTime: new Date().toISOString()
      },
      {
        id: 2,
        name: 'Cámara Lateral',
        status: Math.random() > 0.7 ? 'connected' : 'disconnected',
        fps: Math.random() > 0.7 ? 28.5 + Math.random() * 0.5 : 0,
        resolution: [1920, 1080],
        lastFrameTime: new Date().toISOString()
      }
    ];

    return new Observable(observer => {
      observer.next(cameras);
      
      // Actualizar cada 2 segundos
      const interval$ = setInterval(() => {
        cameras.forEach(cam => {
          if (cam.status === 'connected') {
            cam.fps = 29 + Math.random() * 2;
            cam.lastFrameTime = new Date().toISOString();
          }
        });
        observer.next(cameras);
      }, 2000);

      return () => clearInterval(interval$);
    });
  }

  /**
   * Obtener individuos mock
   */
  getMockIndividuals(): Observable<TrackedIndividual[]> {
    return this.individualsSubject.asObservable();
  }

  /**
   * Obtener métricas mock
   */
  getMockMetrics(): Observable<SystemMetrics> {
    return interval(1000).pipe(
      map(() => ({
        fps: 28 + Math.random() * 4,
        totalFrames: this.frameCounter,
        activeCameras: 2 + Math.floor(Math.random() * 2),
        totalCameras: 3,
        activeIndividuals: this.individualsSubject.value.filter(i => this.isRecentlySeen(i.lastSeen)).length,
        totalDetections: this.individualsSubject.value.reduce((sum, i) => sum + i.cameras.length, 0),
        uptime: Date.now() / 1000,
        cpuUsage: 40 + Math.random() * 20,
        memoryUsage: 60 + Math.random() * 15,
        gpuUsage: 70 + Math.random() * 15
      }))
    );
  }

  /**
   * Inicializar datos mock
   */
  private initializeMockData(): void {
    const behaviors = ['eating', 'sleeping', 'playing', 'walking', 'interacting', 'exploring', 'idle'];
    const now = new Date();

    const individuals: TrackedIndividual[] = [
      {
        id: 'F0',
        confidence: 0.92,
        cameras: [0, 1],
        currentBehavior: 'playing',
        behaviorConfidence: 0.87,
        position: { x: 150, y: 200, z: 0 },
        trajectory: this.generateTrajectory(20, 0),
        firstSeen: new Date(now.getTime() - 323000).toISOString(), // 5m 23s atrás
        lastSeen: new Date(now.getTime() - 1000).toISOString(), // 1s atrás
        totalTime: 323
      },
      {
        id: 'F1',
        confidence: 0.78,
        cameras: [0],
        currentBehavior: 'sleeping',
        behaviorConfidence: 0.94,
        position: { x: 450, y: 300, z: 0 },
        trajectory: this.generateTrajectory(15, 1),
        firstSeen: new Date(now.getTime() - 4320000).toISOString(), // 1h 12m atrás
        lastSeen: new Date(now.getTime() - 180000).toISOString(), // 3min atrás
        totalTime: 4320
      },
      {
        id: 'F2',
        confidence: 0.85,
        cameras: [1, 2],
        currentBehavior: 'walking',
        behaviorConfidence: 0.71,
        position: { x: 320, y: 450, z: 0 },
        trajectory: this.generateTrajectory(30, 2),
        firstSeen: new Date(now.getTime() - 45000).toISOString(), // 45s atrás
        lastSeen: new Date(now.getTime() - 1000).toISOString(),
        totalTime: 45
      },
      {
        id: 'F3',
        confidence: 0.89,
        cameras: [0, 1],
        currentBehavior: 'interacting',
        behaviorConfidence: 0.82,
        position: { x: 280, y: 350, z: 0 },
        trajectory: this.generateTrajectory(25, 3),
        firstSeen: new Date(now.getTime() - 135000).toISOString(), // 2m 15s atrás
        lastSeen: new Date(now.getTime() - 2000).toISOString(),
        totalTime: 135
      },
      {
        id: 'F4',
        confidence: 0.65,
        cameras: [2],
        currentBehavior: 'eating',
        behaviorConfidence: 0.76,
        position: { x: 500, y: 250, z: 0 },
        trajectory: this.generateTrajectory(10, 4),
        firstSeen: new Date(now.getTime() - 510000).toISOString(), // 8m 30s atrás
        lastSeen: new Date(now.getTime() - 300000).toISOString(), // 5min atrás
        totalTime: 510
      }
    ];

    this.individualsSubject.next(individuals);
  }

  /**
   * Generar trayectoria simulada
   */
  private generateTrajectory(points: number, seed: number): any[] {
    const trajectory = [];
    const baseX = 200 + seed * 100;
    const baseY = 200 + seed * 80;

    for (let i = 0; i < points; i++) {
      const angle = (i / points) * Math.PI * 2 + seed;
      const radius = 50 + Math.random() * 30;
      
      trajectory.push({
        x: baseX + Math.cos(angle) * radius,
        y: baseY + Math.sin(angle) * radius,
        timestamp: new Date(Date.now() - (points - i) * 1000).toISOString(),
        cameraId: Math.floor(Math.random() * 3)
      });
    }

    return trajectory;
  }

  /**
   * Iniciar simulación de movimiento
   */
  private startSimulation(): void {
    interval(3000).subscribe(() => {
      this.frameCounter += 90; // ~30 FPS * 3 segundos

      const individuals = this.individualsSubject.value;
      const behaviors = ['eating', 'sleeping', 'playing', 'walking', 'interacting', 'exploring', 'idle'];
      
      individuals.forEach((individual, index) => {
        // Actualizar timestamp de última vez visto (algunos)
        if (Math.random() > 0.3) {
          individual.lastSeen = new Date().toISOString();
          individual.totalTime += 3;
        }

        // Cambiar comportamiento ocasionalmente
        if (Math.random() > 0.85) {
          individual.currentBehavior = behaviors[Math.floor(Math.random() * behaviors.length)];
          individual.behaviorConfidence = 0.6 + Math.random() * 0.35;
        }

        // Actualizar posición
        if (individual.position) {
          individual.position.x += (Math.random() - 0.5) * 20;
          individual.position.y += (Math.random() - 0.5) * 20;
          
          // Mantener dentro de límites
          individual.position.x = Math.max(50, Math.min(600, individual.position.x));
          individual.position.y = Math.max(50, Math.min(450, individual.position.y));
        }

        // Agregar punto a trayectoria
        if (Math.random() > 0.5 && individual.position) {
          individual.trajectory.push({
            x: individual.position.x,
            y: individual.position.y,
            timestamp: new Date().toISOString(),
            cameraId: individual.cameras[Math.floor(Math.random() * individual.cameras.length)]
          });

          // Mantener solo últimos 50 puntos
          if (individual.trajectory.length > 50) {
            individual.trajectory.shift();
          }
        }

        // Cambiar cámaras ocasionalmente
        if (Math.random() > 0.9) {
          const availableCameras = [0, 1, 2];
          const numCameras = Math.floor(Math.random() * 2) + 1;
          individual.cameras = availableCameras
            .sort(() => Math.random() - 0.5)
            .slice(0, numCameras);
        }

        // Actualizar confianza
        individual.confidence = Math.max(0.5, Math.min(0.98, individual.confidence + (Math.random() - 0.5) * 0.05));
      });

      this.individualsSubject.next([...individuals]);
    });
  }

  /**
   * Verificar si fue visto recientemente (últimos 10 segundos)
   */
  private isRecentlySeen(lastSeenStr: string): boolean {
    const lastSeen = new Date(lastSeenStr);
    const now = new Date();
    return (now.getTime() - lastSeen.getTime()) < 10000;
  }

  /**
   * Obtener imagen placeholder para cámara
   * 
   * Para usar imágenes locales:
   * 1. Coloca tus imágenes en: frontend/src/assets/images/cameras/
   * 2. Nombra los archivos: camera-1.jpg, camera-2.jpg, camera-3.jpg, etc.
   * 3. Cambia useLocalImages a true
   */
  getCameraPlaceholderUrl(cameraId: number): string {
    const useLocalImages = false; // Cambiar a true cuando tengas imágenes locales
    
    if (useLocalImages) {
      // Usar imágenes locales
      return `assets/images/cameras/camera-${cameraId}.jpeg`;
    }
    
    // Usar placeholders externos temporales
    const placeholders = [
      'assets/images/cameras/camera-1.jpeg',
      'assets/images/cameras/camera-1.jpeg',
      'assets/images/cameras/camera-1.jpeg',
      'assets/images/cameras/camera-1.jpeg',
      'assets/images/cameras/camera-1.jpeg'
    ];
    
    return placeholders[(cameraId - 1) % placeholders.length] || placeholders[0];
  }

  /**
   * Obtener frame simulado con detecciones
   */
  getMockFrame(cameraId: number): Observable<string> {
    return interval(100).pipe(
      map(() => {
        // Aquí podrías generar un canvas con bounding boxes
        // Por ahora retornamos URL de placeholder
        return this.getCameraPlaceholderUrl(cameraId);
      })
    );
  }
}

