/**
 * Configuración de entorno para producción
 * NOTA: En Docker, el proxy de Nginx redirige /api al backend
 */
export const environment = {
  production: true,
  apiUrl: 'http://localhost:8000',  // Backend directo
  wsUrl: 'ws://localhost:8000',     // WebSocket directo
  updateInterval: 2000, // ms
  version: '1.0.0'
};





