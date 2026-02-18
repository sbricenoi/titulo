/**
 * Componente del dashboard principal
 * Combina visualización de cámaras y reporte de individuos
 */

import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTabsModule } from '@angular/material/tabs';
import { CameraGridComponent } from '../../cameras/camera-grid/camera-grid.component';
import { CameraManagerComponent } from '../../cameras/camera-manager/camera-manager.component';
import { IndividualReportComponent } from '../../tracking/individual-report/individual-report.component';

@Component({
  selector: 'app-main-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatTabsModule,
    CameraGridComponent,
    CameraManagerComponent,
    IndividualReportComponent
  ],
  templateUrl: './main-dashboard.component.html',
  styleUrls: ['./main-dashboard.component.scss']
})
export class MainDashboardComponent {
  constructor() {}
}





