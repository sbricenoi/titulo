/**
 * Servicio para comunicación con la API REST
 */

import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, of, Subject } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { Camera } from '../models/camera.model';
import { TrackedIndividual, BehaviorEvent } from '../models/individual.model';
import { SystemMetrics, Alert } from '../models/metrics.model';
import { MockDataService } from './mock-data.service';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';

interface ApiResponse<T> {
  trace_id: string;
  code: number;
  message: string;
  data: T;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = environment.apiUrl;
  private readonly useMockData = false; // ✅ Cambiado a FALSE para usar API real con cámaras en vivo
  private wsStream$: WebSocketSubject<any> | null = null;
  private wsData$: WebSocketSubject<any> | null = null;

  constructor(
    private http: HttpClient,
    private mockDataService: MockDataService
  ) {}

  /**
   * Obtener todas las cámaras
   */
  getCameras(): Observable<Camera[]> {
    if (this.useMockData) {
      return this.mockDataService.getMockCameras();
    }
    return this.http.get<ApiResponse<any[]>>(`${this.baseUrl}/api/cameras`)
      .pipe(
        map(response => {
          const cameras = response.data || [];
          // Mapear datos del backend al modelo del frontend
          return cameras.map(cam => this.mapBackendCameraToFrontend(cam));
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Mapear datos de cámara del backend al modelo del frontend
   */
  private mapBackendCameraToFrontend(backendCamera: any): Camera {
    // Mapear stream_status a status
    let status: 'connected' | 'disconnected' | 'error' | 'connecting' = 'disconnected';
    if (backendCamera.stream_status === 'active' || backendCamera.stream_status === 'running') {
      status = 'connected';
    } else if (backendCamera.stream_status === 'error') {
      status = 'error';
    } else if (backendCamera.stream_status === 'starting') {
      status = 'connecting';
    } else if (backendCamera.is_active === 1) {
      // Si está activa pero stream_status es unknown, asumimos conectada
      status = 'connected';
    }

    return {
      id: backendCamera.id,
      name: backendCamera.name,
      status: status,
      fps: backendCamera.fps || 0, // Valor por defecto si no existe
      resolution: backendCamera.resolution || [1920, 1080], // Valor por defecto
      lastFrameTime: backendCamera.updated_at
    };
  }

  /**
   * Obtener una cámara específica
   */
  getCamera(id: number): Observable<Camera> {
    return this.http.get<ApiResponse<any>>(`${this.baseUrl}/api/cameras/${id}`)
      .pipe(
        map(response => this.mapBackendCameraToFrontend(response.data)),
        catchError(this.handleError)
      );
  }

  /**
   * Crear nueva cámara
   */
  createCamera(data: {
    name: string;
    rtsp_url: string;
    description?: string;
    location?: string;
  }): Observable<Camera> {
    return this.http.post<ApiResponse<any>>(`${this.baseUrl}/api/cameras`, data)
      .pipe(
        map(response => this.mapBackendCameraToFrontend(response.data)),
        catchError(this.handleError)
      );
  }

  /**
   * Actualizar cámara existente
   */
  updateCamera(id: number, data: {
    name?: string;
    rtsp_url?: string;
    description?: string;
    location?: string;
    is_active?: boolean;
  }): Observable<Camera> {
    return this.http.put<ApiResponse<any>>(`${this.baseUrl}/api/cameras/${id}`, data)
      .pipe(
        map(response => this.mapBackendCameraToFrontend(response.data)),
        catchError(this.handleError)
      );
  }

  /**
   * Eliminar cámara
   */
  deleteCamera(id: number): Observable<any> {
    return this.http.delete<ApiResponse<any>>(`${this.baseUrl}/api/cameras/${id}`)
      .pipe(
        map(response => response.data),
        catchError(this.handleError)
      );
  }

  /**
   * Iniciar stream de cámara
   */
  startCameraStream(id: number): Observable<any> {
    return this.http.post<ApiResponse<any>>(`${this.baseUrl}/api/cameras/${id}/start`, {})
      .pipe(
        map(response => response.data),
        catchError(this.handleError)
      );
  }

  /**
   * Detener stream de cámara
   */
  stopCameraStream(id: number): Observable<any> {
    return this.http.post<ApiResponse<any>>(`${this.baseUrl}/api/cameras/${id}/stop`, {})
      .pipe(
        map(response => response.data),
        catchError(this.handleError)
      );
  }

  /**
   * Obtener todos los individuos tracked
   */
  getIndividuals(): Observable<TrackedIndividual[]> {
    if (this.useMockData) {
      return this.mockDataService.getMockIndividuals();
    }
    return this.http.get<TrackedIndividual[]>(`${this.baseUrl}/api/individuals`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Obtener un individuo específico
   */
  getIndividual(id: string): Observable<TrackedIndividual> {
    return this.http.get<ApiResponse<TrackedIndividual>>(`${this.baseUrl}/api/individuals/${id}`)
      .pipe(
        map(response => response.data),
        catchError(this.handleError)
      );
  }

  /**
   * Obtener historial de comportamientos (legacy - usar los métodos específicos abajo)
   */
  getBehaviors(limit: number = 100): Observable<BehaviorEvent[]> {
    return this.http.get<BehaviorEvent[]>(`${this.baseUrl}/api/behaviors?limit=${limit}`)
      .pipe(catchError(this.handleError));
  }

  // ==================== BITÁCORA DE COMPORTAMIENTOS ====================

  /**
   * Obtener lista de individuos registrados en bitácora
   */
  getBehaviorIndividuals(): Observable<any[]> {
    return this.http.get<ApiResponse<any[]>>(`${this.baseUrl}/api/behaviors/individuals`)
      .pipe(
        map(response => response.data),
        catchError(this.handleError)
      );
  }

  /**
   * Obtener historial de comportamientos de un individuo
   */
  getIndividualBehaviorHistory(
    individualId: string, 
    limit: number = 50, 
    offset: number = 0
  ): Observable<any> {
    return this.http.get<ApiResponse<any>>(
      `${this.baseUrl}/api/behaviors/individual/${individualId}?limit=${limit}&offset=${offset}`
    ).pipe(
      map(response => response.data),
      catchError(this.handleError)
    );
  }

  /**
   * Obtener estadísticas de comportamiento de un individuo
   */
  getIndividualBehaviorStats(
    individualId: string, 
    timeRangeHours?: number
  ): Observable<any> {
    let url = `${this.baseUrl}/api/behaviors/individual/${individualId}/statistics`;
    if (timeRangeHours) {
      url += `?time_range_hours=${timeRangeHours}`;
    }
    return this.http.get<ApiResponse<any>>(url)
      .pipe(
        map(response => response.data),
        catchError(this.handleError)
      );
  }

  /**
   * Obtener comportamientos recientes
   */
  getRecentBehaviors(
    minutes: number = 60, 
    individualId?: string
  ): Observable<any> {
    let url = `${this.baseUrl}/api/behaviors/recent?minutes=${minutes}`;
    if (individualId) {
      url += `&individual_id=${individualId}`;
    }
    return this.http.get<ApiResponse<any>>(url)
      .pipe(
        map(response => response.data),
        catchError(this.handleError)
      );
  }

  /**
   * Obtener comportamientos por tipo
   */
  getBehaviorsByType(
    behavior: string, 
    individualId?: string, 
    limit: number = 50
  ): Observable<any> {
    let url = `${this.baseUrl}/api/behaviors/by-type/${behavior}?limit=${limit}`;
    if (individualId) {
      url += `&individual_id=${individualId}`;
    }
    return this.http.get<ApiResponse<any>>(url)
      .pipe(
        map(response => response.data),
        catchError(this.handleError)
      );
  }

  /**
   * Exportar bitácora de un individuo
   */
  exportIndividualBehaviors(individualId: string): string {
    return `${this.baseUrl}/api/behaviors/export/${individualId}`;
  }

  /**
   * Obtener métricas del sistema
   */
  getMetrics(): Observable<SystemMetrics> {
    if (this.useMockData) {
      return this.mockDataService.getMockMetrics();
    }
    return this.http.get<SystemMetrics>(`${this.baseUrl}/api/metrics`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Obtener alertas
   */
  getAlerts(limit: number = 50): Observable<Alert[]> {
    return this.http.get<Alert[]>(`${this.baseUrl}/api/alerts?limit=${limit}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Reconocer una alerta
   */
  acknowledgeAlert(alertId: string): Observable<Alert> {
    return this.http.post<ApiResponse<Alert>>(
      `${this.baseUrl}/api/alerts/${alertId}/acknowledge`,
      {}
    ).pipe(
      map(response => response.data),
      catchError(this.handleError)
    );
  }

  // ==================== STREAMING ====================

  /**
   * Obtener URL para stream MJPEG de cámara (para usar en <img>)
   */
  getStreamUrl(cameraId: number): string {
    return `${this.baseUrl}/api/stream/mjpeg/${cameraId}`;
  }

  /**
   * Obtener frame estático de una cámara
   */
  getFrameUrl(cameraId: number): string {
    return `${this.baseUrl}/api/stream/frame/${cameraId}?t=${Date.now()}`;
  }

  /**
   * Obtener URL del stream HLS para una cámara
   */
  getHLSUrl(cameraId: number): Observable<{ cameraId: number; hlsUrl: string; status: string }> {
    return this.http.get<{ cameraId: number; hlsUrl: string; status: string }>(
      `${this.baseUrl}/api/stream/hls/${cameraId}`
    );
  }

  /**
   * Obtener URL completa del stream HLS para el reproductor
   */
  getHLSStreamUrl(cameraId: number): string {
    return `${this.baseUrl}/hls/camera_${cameraId}/stream.m3u8`;
  }

  /**
   * Conectar a WebSocket de streaming de frames
   */
  connectStreamWebSocket(cameraId: number = 0, fps: number = 10): Observable<any> {
    const wsUrl = this.baseUrl.replace('http', 'ws');
    
    if (!this.wsStream$ || this.wsStream$.closed) {
      this.wsStream$ = webSocket({
        url: `${wsUrl}/ws/stream`,
        openObserver: {
          next: () => {
            // Enviar configuración al conectar
            this.wsStream$?.next({
              camera_id: cameraId,
              fps: fps
            });
          }
        }
      });
    }

    return this.wsStream$.asObservable();
  }

  /**
   * Conectar a WebSocket de datos en tiempo real
   */
  connectDataWebSocket(): Observable<any> {
    const wsUrl = this.baseUrl.replace('http', 'ws');
    
    if (!this.wsData$ || this.wsData$.closed) {
      this.wsData$ = webSocket(`${wsUrl}/ws/data`);
    }

    return this.wsData$.asObservable();
  }

  /**
   * Cerrar conexión WebSocket de streaming
   */
  disconnectStreamWebSocket(): void {
    if (this.wsStream$ && !this.wsStream$.closed) {
      this.wsStream$.complete();
      this.wsStream$ = null;
    }
  }

  /**
   * Cerrar conexión WebSocket de datos
   */
  disconnectDataWebSocket(): void {
    if (this.wsData$ && !this.wsData$.closed) {
      this.wsData$.complete();
      this.wsData$ = null;
    }
  }

  /**
   * Manejo de errores HTTP
   */
  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'Error desconocido';
    
    if (error.error instanceof ErrorEvent) {
      // Error del lado del cliente
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Error del lado del servidor
      errorMessage = `Error ${error.status}: ${error.message}`;
    }
    
    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}

