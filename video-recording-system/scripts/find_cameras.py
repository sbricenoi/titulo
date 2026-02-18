#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para encontrar todas las cámaras Reolink en la red local.
Escanea la red y prueba conexiones RTSP.
"""

import subprocess
import socket
import sys
import concurrent.futures
from typing import List, Dict, Optional

# Colores
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

# Configuración
NETWORK_PREFIX = "192.168.0"
START_IP = 1
END_IP = 254
TIMEOUT = 1.0
MAX_WORKERS = 50

# Credenciales a probar
CREDENTIALS = [
    ("admin", "Sb123456"),
    ("admin", "admin"),
    ("admin", ""),
]

# Rutas RTSP a probar
RTSP_PATHS = [
    "/Preview_01_main",
    "/h264Preview_01_main",
    "/",
]


def print_header(text: str):
    """Imprimir encabezado."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")


def print_success(text: str):
    """Imprimir mensaje de éxito."""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    """Imprimir mensaje de error."""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text: str):
    """Imprimir mensaje informativo."""
    print(f"{CYAN}ℹ {text}{RESET}")


def check_host(ip: str) -> Optional[Dict]:
    """
    Verificar si un host está activo y tiene puerto RTSP abierto.
    
    Args:
        ip: Dirección IP a verificar
        
    Returns:
        Diccionario con info del host o None
    """
    # Verificar puerto RTSP (554)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)
    
    try:
        result = sock.connect_ex((ip, 554))
        sock.close()
        
        if result == 0:
            return {
                "ip": ip,
                "rtsp_open": True
            }
    except:
        pass
    finally:
        sock.close()
    
    return None


def test_rtsp_connection(ip: str, user: str, password: str, path: str) -> Optional[str]:
    """
    Probar conexión RTSP.
    
    Args:
        ip: IP de la cámara
        user: Usuario
        password: Contraseña
        path: Ruta RTSP
        
    Returns:
        URL RTSP funcional o None
    """
    rtsp_url = f"rtsp://{user}:{password}@{ip}:554{path}"
    
    cmd = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", rtsp_url,
        "-t", "1",
        "-f", "null",
        "-"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3,
            universal_newlines=True
        )
        
        stderr = result.stderr
        
        if "Stream #0" in stderr or "Video:" in stderr:
            return rtsp_url
            
    except:
        pass
    
    return None


def scan_network() -> List[Dict]:
    """
    Escanear la red en busca de cámaras.
    
    Returns:
        Lista de hosts con puerto RTSP abierto
    """
    print_info(f"Escaneando red {NETWORK_PREFIX}.{START_IP}-{END_IP}...")
    print_info(f"Buscando puerto RTSP (554) abierto...")
    print()
    
    hosts_to_check = [f"{NETWORK_PREFIX}.{i}" for i in range(START_IP, END_IP + 1)]
    found_hosts = []
    
    # Escaneo paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_host, ip): ip for ip in hosts_to_check}
        
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            if completed % 50 == 0:
                print(f"  Progreso: {completed}/{len(hosts_to_check)}", end='\r')
            
            result = future.result()
            if result:
                found_hosts.append(result)
    
    print(f"  Progreso: {len(hosts_to_check)}/{len(hosts_to_check)}")
    print()
    
    return found_hosts


def identify_cameras(hosts: List[Dict]) -> List[Dict]:
    """
    Identificar cámaras y obtener URLs RTSP funcionales.
    
    Args:
        hosts: Lista de hosts con puerto RTSP abierto
        
    Returns:
        Lista de cámaras identificadas con URLs funcionales
    """
    cameras = []
    
    print_info(f"Identificando cámaras en {len(hosts)} hosts encontrados...")
    print()
    
    for host in hosts:
        ip = host['ip']
        print(f"{CYAN}Probando {ip}...{RESET}")
        
        found_working_url = False
        
        # Probar diferentes combinaciones de credenciales y rutas
        for user, password in CREDENTIALS:
            for path in RTSP_PATHS:
                rtsp_url = test_rtsp_connection(ip, user, password, path)
                
                if rtsp_url:
                    print_success(f"Cámara encontrada en {ip}")
                    print(f"  URL: {rtsp_url}")
                    
                    cameras.append({
                        "ip": ip,
                        "url": rtsp_url,
                        "user": user,
                        "path": path
                    })
                    
                    found_working_url = True
                    break
            
            if found_working_url:
                break
        
        if not found_working_url:
            print_error(f"No se pudo conectar a {ip} (puerto abierto pero sin acceso RTSP)")
        
        print()
    
    return cameras


def generate_config(cameras: List[Dict]):
    """
    Generar configuración para .env
    
    Args:
        cameras: Lista de cámaras encontradas
    """
    print_header("📝 CONFIGURACIÓN PARA .env")
    
    if not cameras:
        print_error("No se encontraron cámaras funcionales")
        return
    
    print("Agrega estas líneas a tu archivo .env:\n")
    
    for i, camera in enumerate(cameras, 1):
        print(f"{YELLOW}# Cámara {i} - {camera['ip']}{RESET}")
        print(f"CAMERA_{i}_URL={camera['url']}")
        print(f"CAMERA_{i}_NAME=Reolink_Camera_{i}")
        print()
    
    print(f"{GREEN}Total de cámaras encontradas: {len(cameras)}{RESET}")


def main():
    """Función principal."""
    print_header("🔍 BUSCADOR DE CÁMARAS REOLINK")
    
    print_info("Este script escaneará tu red local en busca de cámaras Reolink")
    print_info(f"Red a escanear: {NETWORK_PREFIX}.0/24")
    print()
    
    # Paso 1: Escanear red
    hosts = scan_network()
    
    if not hosts:
        print_error("No se encontraron dispositivos con puerto RTSP abierto")
        print()
        print("Posibles causas:")
        print("  - Las cámaras están apagadas")
        print("  - Las cámaras están en otra red")
        print("  - Firewall bloqueando el escaneo")
        return
    
    print_success(f"Encontrados {len(hosts)} dispositivos con puerto RTSP abierto:")
    for host in hosts:
        print(f"  • {host['ip']}")
    print()
    
    # Paso 2: Identificar cámaras
    cameras = identify_cameras(hosts)
    
    # Paso 3: Generar configuración
    generate_config(cameras)
    
    # Resumen
    print_header("📊 RESUMEN")
    print(f"Hosts escaneados: {END_IP - START_IP + 1}")
    print(f"Puertos RTSP abiertos: {len(hosts)}")
    print(f"Cámaras funcionales: {len(cameras)}")
    print()
    
    if cameras:
        print_success("¡Listo! Copia la configuración de arriba a tu archivo .env")
    else:
        print_error("No se pudieron identificar cámaras funcionales")
        print()
        print("Verifica:")
        print("  1. Las credenciales son correctas")
        print("  2. Las cámaras permiten conexiones RTSP")
        print("  3. No hay firewall bloqueando las conexiones")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Escaneo interrumpido por el usuario{RESET}")
        sys.exit(0)
