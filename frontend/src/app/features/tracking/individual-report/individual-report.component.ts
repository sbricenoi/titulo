/**
 * Componente para reporte de movimientos de individuos
 */

import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatPaginatorModule, MatPaginator } from '@angular/material/paginator';
import { MatSortModule, MatSort } from '@angular/material/sort';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Subject, interval } from 'rxjs';
import { takeUntil, switchMap } from 'rxjs/operators';

import { ApiService } from '../../../core/services/api.service';
import { TrackedIndividual, BEHAVIOR_NAMES_ES, BEHAVIOR_COLORS } from '../../../core/models/individual.model';

@Component({
  selector: 'app-individual-report',
  standalone: true,
  imports: [
    CommonModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatChipsModule,
    MatTooltipModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './individual-report.component.html',
  styleUrls: ['./individual-report.component.scss']
})
export class IndividualReportComponent implements OnInit, OnDestroy {
  displayedColumns: string[] = [
    'id',
    'status',
    'behavior',
    'cameras',
    'confidence',
    'timeActive',
    'lastSeen',
    'actions'
  ];

  dataSource = new MatTableDataSource<TrackedIndividual>();
  
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  individuals: TrackedIndividual[] = [];
  loading = true;
  error: string | null = null;
  selectedIndividual: TrackedIndividual | null = null;
  
  // Estadísticas
  totalIndividuals = 0;
  activeIndividuals = 0;
  totalDetections = 0;
  
  // Historial de comportamientos
  behaviorHistory: any[] = [];
  behaviorStats: any = null;
  loadingHistory = false;
  historyError: string | null = null;
  showHistory = false;
  
  private destroy$ = new Subject<void>();

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadIndividuals();
    this.startAutoRefresh();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  ngAfterViewInit(): void {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }

  /**
   * Cargar individuos tracked
   */
  private loadIndividuals(): void {
    this.apiService.getIndividuals()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (individuals) => {
          this.individuals = individuals;
          this.dataSource.data = individuals;
          this.updateStats();
          this.loading = false;
        },
        error: (error) => {
          this.error = 'Error cargando individuos';
          this.loading = false;
          console.error(error);
        }
      });
  }

  /**
   * Actualizar automáticamente cada 5 segundos
   */
  private startAutoRefresh(): void {
    interval(5000)
      .pipe(
        takeUntil(this.destroy$),
        switchMap(() => this.apiService.getIndividuals())
      )
      .subscribe({
        next: (individuals) => {
          this.individuals = individuals;
          this.dataSource.data = individuals;
          this.updateStats();
        },
        error: (error) => console.error('Error en auto-refresh:', error)
      });
  }

  /**
   * Actualizar estadísticas
   */
  private updateStats(): void {
    this.totalIndividuals = this.individuals.length;
    this.activeIndividuals = this.individuals.filter(i => this.isActive(i)).length;
    this.totalDetections = this.individuals.reduce((sum, i) => sum + i.cameras.length, 0);
  }

  /**
   * Verificar si un individuo está activo (visto en los últimos 10 segundos)
   */
  isActive(individual: TrackedIndividual): boolean {
    const lastSeen = new Date(individual.lastSeen);
    const now = new Date();
    const diff = now.getTime() - lastSeen.getTime();
    return diff < 10000; // 10 segundos
  }

  /**
   * Obtener nombre del comportamiento en español
   */
  getBehaviorName(behavior: string): string {
    return BEHAVIOR_NAMES_ES[behavior] || behavior;
  }

  /**
   * Obtener color del comportamiento
   */
  getBehaviorColor(behavior: string): string {
    return BEHAVIOR_COLORS[behavior] || '#9E9E9E';
  }

  /**
   * Formatear tiempo transcurrido
   */
  formatTimeAgo(dateString: string): string {
    try {
      const now = new Date();
      const date = new Date(dateString);
      const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
      
      if (seconds < 60) return `hace ${seconds} segundos`;
      if (seconds < 3600) return `hace ${Math.floor(seconds / 60)} minutos`;
      if (seconds < 86400) return `hace ${Math.floor(seconds / 3600)} horas`;
      return `hace ${Math.floor(seconds / 86400)} días`;
    } catch {
      return 'Desconocido';
    }
  }

  /**
   * Formatear duración en formato legible
   */
  formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  }

  /**
   * Aplicar filtro a la tabla
   */
  applyFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource.filter = filterValue.trim().toLowerCase();

    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }

  /**
   * Ver detalles de un individuo (incluye historial de comportamientos)
   */
  viewDetails(individual: TrackedIndividual): void {
    this.selectedIndividual = individual;
    this.showHistory = true;
    this.loadBehaviorHistory(individual.id);
    this.loadBehaviorStats(individual.id);
  }

  /**
   * Cargar historial de comportamientos de un individuo
   */
  private loadBehaviorHistory(individualId: string): void {
    this.loadingHistory = true;
    this.historyError = null;

    this.apiService.getIndividualBehaviorHistory(individualId, 20, 0)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.behaviorHistory = data.behaviors || [];
          this.loadingHistory = false;
        },
        error: (error) => {
          this.historyError = 'Error cargando historial';
          this.loadingHistory = false;
          console.error(error);
        }
      });
  }

  /**
   * Cargar estadísticas de comportamiento de un individuo
   */
  private loadBehaviorStats(individualId: string): void {
    this.apiService.getIndividualBehaviorStats(individualId, 24)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.behaviorStats = data;
        },
        error: (error) => {
          console.error('Error cargando estadísticas:', error);
        }
      });
  }

  /**
   * Cerrar vista de detalles
   */
  closeDetails(): void {
    this.showHistory = false;
    this.selectedIndividual = null;
    this.behaviorHistory = [];
    this.behaviorStats = null;
  }

  /**
   * Convertir objeto de comportamientos a array para iteración
   */
  getBehaviorsArray(): Array<{ key: string; count: number; percentage: number; nameEs: string }> {
    if (!this.behaviorStats || !this.behaviorStats.behaviors) {
      return [];
    }

    return Object.keys(this.behaviorStats.behaviors).map(key => {
      const behavior = this.behaviorStats.behaviors[key];
      return {
        key: key,
        count: behavior.count || 0,
        percentage: behavior.percentage || 0,
        nameEs: behavior.name_es || this.getBehaviorName(key)
      };
    });
  }

  /**
   * Descargar bitácora completa de un individuo
   */
  downloadBehaviorLog(individualId: string): void {
    const url = this.apiService.exportIndividualBehaviors(individualId);
    window.open(url, '_blank');
  }

  /**
   * Ver trayectoria de un individuo
   */
  viewTrajectory(individual: TrackedIndividual): void {
    console.log('Ver trayectoria de:', individual);
    // Implementar visualización de trayectoria
  }

  /**
   * Exportar datos
   */
  exportData(): void {
    const data = this.individuals.map(i => ({
      ID: i.id,
      'Comportamiento': this.getBehaviorName(i.currentBehavior || ''),
      'Confianza': i.confidence !== undefined && i.confidence !== null ? i.confidence.toFixed(2) : 'N/A',
      'Cámaras': i.cameras.join(', '),
      'Tiempo Activo': this.formatDuration(i.totalTime || 0),
      'Última Vez Visto': i.lastSeen
    }));

    // Convertir a CSV
    const csv = this.convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `individuos_${new Date().toISOString()}.csv`;
    link.click();
  }

  /**
   * Convertir datos a CSV
   */
  private convertToCSV(data: any[]): string {
    if (data.length === 0) return '';
    
    const headers = Object.keys(data[0]).join(',');
    const rows = data.map(row => Object.values(row).join(','));
    
    return [headers, ...rows].join('\n');
  }

  /**
   * Recargar datos
   */
  reload(): void {
    this.loading = true;
    this.error = null;
    this.loadIndividuals();
  }
}

