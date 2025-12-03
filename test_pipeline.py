#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba del pipeline ETL completo con descarga automática a Power BI.
Permite ejecutar N ciclos con intervalo personalizado.
"""

import sys
import time
import argparse
from main import ETLSystem

# Configurar UTF-8 en Windows
if sys.platform == 'win32':
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8')


def test_pipeline(num_cycles: int = 1, interval: int = 5, verbose: bool = True):
    """
    Ejecuta N ciclos del pipeline para testing.
    
    Args:
        num_cycles: Número de ciclos a ejecutar
        interval: Segundos entre ciclos
        verbose: Mostrar detalles
    
    Returns:
        True si todos los ciclos completaron exitosamente
    """
    print("\n" + "="*80)
    print("🧪 TEST DE PIPELINE ETL CON DESCARGA A POWER BI")
    print("="*80)
    print(f"Ciclos: {num_cycles}")
    print(f"Intervalo: {interval}s")
    print("="*80 + "\n")
    
    system = ETLSystem(extraction_interval=interval)
    system.display_config()
    
    success_count = 0
    
    try:
        for cycle_num in range(1, num_cycles + 1):
            print(f"\n{'='*80}")
            print(f"📍 CICLO {cycle_num} / {num_cycles}")
            print(f"{'='*80}")
            
            try:
                result = system.run_cycle(cycle_num)
                if result:
                    success_count += 1
                    print(f"\n✅ CICLO {cycle_num} EXITOSO")
                else:
                    print(f"\n❌ CICLO {cycle_num} CON ERRORES")
                
                # Esperar antes del próximo ciclo (excepto en el último)
                if cycle_num < num_cycles:
                    print(f"\n[INFO] Esperando {interval}s antes del próximo ciclo...")
                    time.sleep(interval)
            
            except Exception as e:
                print(f"\n❌ ERROR en ciclo {cycle_num}: {e}")
                import traceback
                traceback.print_exc()
        
        # Resumen
        print(f"\n{'='*80}")
        print(f"📊 RESUMEN DEL TEST")
        print(f"{'='*80}")
        print(f"✅ Ciclos exitosos: {success_count}/{num_cycles}")
        print(f"❌ Ciclos fallidos: {num_cycles - success_count}/{num_cycles}")
        
        if success_count == num_cycles:
            print("\n🎉 ¡TODOS LOS CICLOS COMPLETADOS EXITOSAMENTE!")
            print("\n📝 Pasos siguientes:")
            print("1. El archivo CSV está en: file/metricas_kpi_gold.csv")
            print("2. Abre Power BI Desktop")
            print("3. Get Data → Text/CSV")
            print("4. Selecciona: file/metricas_kpi_gold.csv")
            print("5. Crea tus visualizaciones con los KPIs")
            print("\n💡 Tip: El archivo se actualiza automáticamente en cada ciclo")
            return True
        else:
            print(f"\n⚠️  Algunos ciclos fallaron. Revisar logs arriba.")
            return False
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrumpido por el usuario")
        print(f"Ciclos completados: {success_count}/{num_cycles}")
        return False


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Test del pipeline ETL con descarga automática a Power BI"
    )
    parser.add_argument(
        "-c", "--cycles",
        type=int,
        default=1,
        help="Número de ciclos a ejecutar (default: 1)"
    )
    parser.add_argument(
        "-i", "--interval",
        type=int,
        default=5,
        help="Segundos entre ciclos (default: 5)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Modo silencioso (menos información)"
    )
    
    args = parser.parse_args()
    
    success = test_pipeline(
        num_cycles=args.cycles,
        interval=args.interval,
        verbose=not args.quiet
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
