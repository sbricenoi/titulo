/**
 * Configuración de rutas de la aplicación
 */

import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  },
  {
    path: 'dashboard',
    loadComponent: () => 
      import('./features/dashboard/main-dashboard/main-dashboard.component')
        .then(m => m.MainDashboardComponent)
  },
  {
    path: 'cameras',
    loadComponent: () => 
      import('./features/cameras/camera-grid/camera-grid.component')
        .then(m => m.CameraGridComponent)
  },
  {
    path: 'cameras/manage',
    loadComponent: () => 
      import('./features/cameras/camera-manager/camera-manager.component')
        .then(m => m.CameraManagerComponent)
  },
  {
    path: 'tracking',
    loadComponent: () => 
      import('./features/tracking/individual-report/individual-report.component')
        .then(m => m.IndividualReportComponent)
  },
  {
    path: 'classifier',
    loadComponent: () => 
      import('./features/classification/frame-classifier/frame-classifier.component')
        .then(m => m.FrameClassifierComponent),
    title: 'Clasificador de Frames'
  },
  {
    path: '**',
    redirectTo: '/dashboard'
  }
];





