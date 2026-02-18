/**
 * Servicio para comunicación WebSocket en tiempo real
 */

import { Injectable } from '@angular/core';
import { Observable, Subject, timer } from 'rxjs';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { retryWhen, tap, delayWhen } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface WebSocketMessage {
  type: string;
  timestamp: string;
  data: any;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private streamSocket$: WebSocketSubject<any> | null = null;
  private dataSocket$: WebSocketSubject<any> | null = null;
  
  private streamSubject = new Subject<WebSocketMessage>();
  private dataSubject = new Subject<WebSocketMessage>();
  
  private reconnectInterval = 5000; // 5 segundos
  private isConnected = false;

  constructor() {}

  /**
   * Conectar al WebSocket de streaming de video
   */
  connectStream(): Observable<WebSocketMessage> {
    if (!this.streamSocket$ || this.streamSocket$.closed) {
      this.streamSocket$ = this.createWebSocket(`${environment.wsUrl}/ws/stream`);
      
      this.streamSocket$
        .pipe(
          retryWhen(errors =>
            errors.pipe(
              tap(err => console.error('WebSocket Stream error:', err)),
              delayWhen(() => timer(this.reconnectInterval))
            )
          )
        )
        .subscribe({
          next: (message) => this.streamSubject.next(message),
          error: (err) => console.error('Stream error:', err),
          complete: () => console.log('Stream complete')
        });
    }
    
    return this.streamSubject.asObservable();
  }

  /**
   * Conectar al WebSocket de datos
   */
  connectData(): Observable<WebSocketMessage> {
    if (!this.dataSocket$ || this.dataSocket$.closed) {
      this.dataSocket$ = this.createWebSocket(`${environment.wsUrl}/ws/data`);
      
      this.dataSocket$
        .pipe(
          retryWhen(errors =>
            errors.pipe(
              tap(err => console.error('WebSocket Data error:', err)),
              delayWhen(() => timer(this.reconnectInterval))
            )
          )
        )
        .subscribe({
          next: (message) => {
            this.dataSubject.next(message);
            this.isConnected = true;
          },
          error: (err) => {
            console.error('Data error:', err);
            this.isConnected = false;
          },
          complete: () => {
            console.log('Data complete');
            this.isConnected = false;
          }
        });
    }
    
    return this.dataSubject.asObservable();
  }

  /**
   * Enviar mensaje al servidor
   */
  send(message: any, socketType: 'stream' | 'data' = 'data'): void {
    const socket = socketType === 'stream' ? this.streamSocket$ : this.dataSocket$;
    
    if (socket && !socket.closed) {
      socket.next(message);
    } else {
      console.warn('WebSocket no está conectado');
    }
  }

  /**
   * Enviar ping para mantener conexión
   */
  sendPing(): void {
    this.send({ type: 'ping' }, 'stream');
    this.send({ type: 'ping' }, 'data');
  }

  /**
   * Desconectar WebSockets
   */
  disconnect(): void {
    if (this.streamSocket$) {
      this.streamSocket$.complete();
      this.streamSocket$ = null;
    }
    
    if (this.dataSocket$) {
      this.dataSocket$.complete();
      this.dataSocket$ = null;
    }
    
    this.isConnected = false;
  }

  /**
   * Verificar si está conectado
   */
  getConnectionStatus(): boolean {
    return this.isConnected;
  }

  /**
   * Crear WebSocket con configuración
   */
  private createWebSocket(url: string): WebSocketSubject<any> {
    return webSocket({
      url,
      openObserver: {
        next: () => {
          console.log(`WebSocket conectado: ${url}`);
          this.isConnected = true;
        }
      },
      closeObserver: {
        next: () => {
          console.log(`WebSocket cerrado: ${url}`);
          this.isConnected = false;
        }
      }
    });
  }
}





