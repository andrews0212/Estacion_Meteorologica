#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor de actualizaciones del archivo Gold para Power BI.
Muestra cuándo se actualiza el archivo y cuántos registros contiene.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Configurar UTF-8 en Windows
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8')


def count_csv_rows(filepath: Path) -> int:
    """Cuenta las filas de un CSV (excluyendo header)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f) - 1  # -1 para el header
    except Exception:
        return 0


def get_file_info(filepath: Path) -> dict:
    """Obtiene información del archivo."""
    if not filepath.exists():
        return {'exists': False}
    
    stat = filepath.stat()
    return {
        'exists': True,
        'size': stat.st_size,
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'rows': count_csv_rows(filepath)
    }


def monitor_gold_file(check_interval: int = 10, duration: int = 0):
    """
    Monitorea el archivo Gold para cambios.
    
    Args:
        check_interval: Segundos entre verificaciones
        duration: Duración total en segundos (0 = infinito)
    """
    filepath = Path("file") / "metricas_kpi_gold.csv"
    
    print("\n" + "="*80)
    print("🔍 MONITOR DE ACTUALIZACIONES GOLD PARA POWER BI")
    print("="*80)
    print(f"📍 Archivo: {filepath.absolute()}")
    print(f"⏱️  Intervalo: {check_interval}s")
    if duration > 0:
        print(f"⏰ Duración: {duration}s")
    print("="*80 + "\n")
    
    last_info = None
    start_time = time.time()
    check_count = 0
    
    try:
        while True:
            check_count += 1
            current_info = get_file_info(filepath)
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Verificación #{check_count}...", end=' ')
            
            if not current_info['exists']:
                print("❌ Archivo NO existe")
            else:
                size = current_info['size']
                rows = current_info['rows']
                modified = current_info['modified'].strftime('%H:%M:%S')
                
                status = "✅"
                if last_info and current_info != last_info:
                    status = "🔄 ACTUALIZADO"
                
                print(f"{status} | Tamaño: {size} bytes | Registros: {rows} | Modificado: {modified}")
                
                last_info = current_info
            
            # Verificar duración
            if duration > 0:
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    print(f"\n⏰ Tiempo de monitoreo completado ({duration}s)")
                    break
            
            time.sleep(check_interval)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoreo detenido por el usuario")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    print("\n" + "="*80)
    return True


def main():
    """Función principal."""
    # Por defecto: monitorear indefinidamente cada 10 segundos
    # Presionar Ctrl+C para detener
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor de actualizaciones Gold para Power BI")
    parser.add_argument("--interval", type=int, default=10, help="Segundos entre verificaciones (default: 10)")
    parser.add_argument("--duration", type=int, default=0, help="Duración total en segundos (default: 0 = infinito)")
    
    args = parser.parse_args()
    
    success = monitor_gold_file(check_interval=args.interval, duration=args.duration)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
