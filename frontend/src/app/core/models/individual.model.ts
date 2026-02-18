/**
 * Modelos de datos para individuos tracked
 */

export interface TrackedIndividual {
  id: string;
  confidence: number;
  cameras: number[];
  currentBehavior?: string;
  behaviorConfidence?: number;
  position?: Position3D;
  trajectory: TrajectoryPoint[];
  firstSeen: string;
  lastSeen: string;
  totalTime: number;
}

export interface Position3D {
  x: number;
  y: number;
  z: number;
}

export interface TrajectoryPoint {
  x: number;
  y: number;
  timestamp: string;
  cameraId: number;
}

export interface BehaviorEvent {
  id: string;
  individualId: string;
  behavior: string;
  confidence: number;
  timestamp: string;
  duration?: number;
}

export interface BehaviorStats {
  behavior: string;
  count: number;
  totalDuration: number;
  averageDuration: number;
  color: string;
}

export const BEHAVIOR_NAMES_ES: Record<string, string> = {
  'eating': 'Comiendo',
  'sleeping': 'Durmiendo',
  'running': 'Corriendo',
  'fighting': 'Peleando',
  'defecating': 'Haciendo necesidades',
  'walking': 'Caminando',
  'idle': 'Inactivo',
  // Legacy behaviors (mantener por compatibilidad)
  'playing': 'Jugando',
  'interacting': 'Interactuando',
  'exploring': 'Explorando'
};

export const BEHAVIOR_COLORS: Record<string, string> = {
  'eating': '#4CAF50',      // Verde
  'sleeping': '#2196F3',    // Azul
  'running': '#FF5722',     // Rojo-Naranja
  'fighting': '#F44336',    // Rojo
  'defecating': '#795548',  // Marrón
  'walking': '#9C27B0',     // Púrpura
  'idle': '#9E9E9E',        // Gris
  // Legacy behaviors
  'playing': '#FF9800',
  'interacting': '#E91E63',
  'exploring': '#00BCD4'
};





