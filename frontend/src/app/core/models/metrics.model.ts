/**
 * Modelos de datos para métricas del sistema
 */

export interface SystemMetrics {
  fps: number;
  totalFrames: number;
  activeCameras: number;
  totalCameras: number;
  activeIndividuals: number;
  totalDetections: number;
  uptime: number;
  cpuUsage?: number;
  memoryUsage?: number;
  gpuUsage?: number;
}

export interface Alert {
  id: string;
  type: AlertType;
  message: string;
  individualId?: string;
  timestamp: string;
  acknowledged: boolean;
}

export type AlertType = 'info' | 'warning' | 'error';





