/**
 * Modelos de datos para cámaras
 */

export interface Camera {
  id: number;
  name: string;
  status: CameraStatus;
  fps: number;
  resolution: [number, number];
  lastFrameTime?: string;
  location?: string;
  description?: string;
  rtsp_url?: string;
}

export type CameraStatus = 'connected' | 'disconnected' | 'error' | 'connecting';

export interface CameraFrame {
  cameraId: number;
  frame: string; // Base64
  timestamp: string;
  detections: Detection[];
}

export interface Detection {
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  confidence: number;
  classId: number;
  className: string;
  trackId?: number;
}





