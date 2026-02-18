/**
 * Componente para gestionar cámaras (CRUD)
 */

import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { ApiService } from '../../../core/services/api.service';
import { Camera } from '../../../core/models/camera.model';

interface CameraFormData {
  name: string;
  rtsp_url: string;
  description?: string;
  location?: string;
}

@Component({
  selector: 'app-camera-manager',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatDialogModule,
    MatSnackBarModule,
    MatTooltipModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './camera-manager.component.html',
  styleUrls: ['./camera-manager.component.scss']
})
export class CameraManagerComponent implements OnInit, OnDestroy {
  displayedColumns: string[] = ['id', 'name', 'location', 'status', 'actions'];
  dataSource = new MatTableDataSource<Camera>();
  
  cameras: Camera[] = [];
  loading = true;
  error: string | null = null;
  
  // Formulario
  cameraForm: FormGroup;
  isEditing = false;
  editingCameraId: number | null = null;
  showForm = false;
  
  private destroy$ = new Subject<void>();

  constructor(
    private apiService: ApiService,
    private fb: FormBuilder,
    private snackBar: MatSnackBar,
    private dialog: MatDialog
  ) {
    this.cameraForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(3)]],
      rtsp_url: ['', [Validators.required, Validators.pattern(/^rtsp:\/\/.+/)]],
      description: [''],
      location: ['']
    });
  }

  ngOnInit(): void {
    this.loadCameras();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Cargar lista de cámaras
   */
  private loadCameras(): void {
    this.loading = true;
    this.error = null;
    
    this.apiService.getCameras()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (cameras) => {
          this.cameras = cameras;
          this.dataSource.data = cameras;
          this.loading = false;
        },
        error: (error) => {
          this.error = 'Error cargando cámaras';
          this.loading = false;
          console.error(error);
          this.showSnackBar('Error al cargar cámaras', 'error');
        }
      });
  }

  /**
   * Mostrar formulario para nueva cámara
   */
  showAddForm(): void {
    this.isEditing = false;
    this.editingCameraId = null;
    this.cameraForm.reset();
    this.showForm = true;
  }

  /**
   * Mostrar formulario para editar cámara
   */
  editCamera(camera: Camera): void {
    this.isEditing = true;
    this.editingCameraId = camera.id;
    this.showForm = true;
    
    // Cargar datos completos de la cámara desde el backend
    this.apiService.getCamera(camera.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (fullCamera) => {
          this.cameraForm.patchValue({
            name: fullCamera.name,
            rtsp_url: fullCamera.rtsp_url || '',
            description: fullCamera.description || '',
            location: fullCamera.location || ''
          });
        },
        error: (error) => {
          console.error('Error cargando datos de cámara:', error);
          this.showSnackBar('Error al cargar datos de la cámara', 'error');
        }
      });
  }

  /**
   * Guardar cámara (crear o actualizar)
   */
  saveCamera(): void {
    if (this.cameraForm.invalid) {
      this.showSnackBar('Por favor complete todos los campos requeridos', 'error');
      return;
    }

    const formData: CameraFormData = this.cameraForm.value;
    
    if (this.isEditing && this.editingCameraId !== null) {
      // Actualizar cámara existente
      this.updateCamera(this.editingCameraId, formData);
    } else {
      // Crear nueva cámara
      this.createCamera(formData);
    }
  }

  /**
   * Crear nueva cámara
   */
  private createCamera(data: CameraFormData): void {
    this.apiService.createCamera(data)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.showSnackBar('Cámara creada exitosamente', 'success');
          this.cancelForm();
          this.loadCameras();
        },
        error: (error) => {
          console.error('Error creando cámara:', error);
          this.showSnackBar('Error al crear la cámara', 'error');
        }
      });
  }

  /**
   * Actualizar cámara existente
   */
  private updateCamera(id: number, data: CameraFormData): void {
    this.apiService.updateCamera(id, data)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.showSnackBar('Cámara actualizada exitosamente', 'success');
          this.cancelForm();
          this.loadCameras();
        },
        error: (error) => {
          console.error('Error actualizando cámara:', error);
          this.showSnackBar('Error al actualizar la cámara', 'error');
        }
      });
  }

  /**
   * Eliminar cámara
   */
  deleteCamera(camera: Camera): void {
    if (confirm(`¿Está seguro de eliminar la cámara "${camera.name}"?`)) {
      this.apiService.deleteCamera(camera.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            this.showSnackBar('Cámara eliminada exitosamente', 'success');
            this.loadCameras();
          },
          error: (error) => {
            console.error('Error eliminando cámara:', error);
            this.showSnackBar('Error al eliminar la cámara', 'error');
          }
        });
    }
  }

  /**
   * Iniciar stream de cámara
   */
  startCamera(camera: Camera): void {
    this.showSnackBar(`Iniciando stream de ${camera.name}...`, 'info');
    
    this.apiService.startCameraStream(camera.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.showSnackBar(`Stream de ${camera.name} iniciado`, 'success');
          this.loadCameras();
        },
        error: (error) => {
          console.error('Error iniciando stream:', error);
          this.showSnackBar('Error al iniciar el stream', 'error');
        }
      });
  }

  /**
   * Detener stream de cámara
   */
  stopCamera(camera: Camera): void {
    this.showSnackBar(`Deteniendo stream de ${camera.name}...`, 'info');
    
    this.apiService.stopCameraStream(camera.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.showSnackBar(`Stream de ${camera.name} detenido`, 'success');
          this.loadCameras();
        },
        error: (error) => {
          console.error('Error deteniendo stream:', error);
          this.showSnackBar('Error al detener el stream', 'error');
        }
      });
  }

  /**
   * Cancelar formulario
   */
  cancelForm(): void {
    this.showForm = false;
    this.isEditing = false;
    this.editingCameraId = null;
    this.cameraForm.reset();
  }

  /**
   * Recargar lista
   */
  reload(): void {
    this.loadCameras();
  }

  /**
   * Obtener clase CSS según estado
   */
  getStatusClass(status: string): string {
    return `status-${status}`;
  }

  /**
   * Obtener icono según estado
   */
  getStatusIcon(status: string): string {
    const icons: Record<string, string> = {
      'connected': 'check_circle',
      'disconnected': 'cancel',
      'error': 'error',
      'connecting': 'sync'
    };
    return icons[status] || 'help';
  }

  /**
   * Obtener texto de estado
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
   * Mostrar notificación
   */
  private showSnackBar(message: string, type: 'success' | 'error' | 'info'): void {
    this.snackBar.open(message, 'Cerrar', {
      duration: 3000,
      horizontalPosition: 'end',
      verticalPosition: 'top',
      panelClass: [`snackbar-${type}`]
    });
  }
}
