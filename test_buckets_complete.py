#!/usr/bin/env python3
"""Script completo para probar creación automática de los 3 buckets."""

import sys
sys.path.insert(0, '.')

from config import MinIOConfig, DatabaseConfig
from etl.pipeline import ETLPipeline
from etl.managers import SilverManager, GoldManager
from minio import Minio

print('=' * 80)
print('[TEST COMPLETO] Probando creación automática de todos los buckets')
print('=' * 80)

# Cargar configuraciones
print('\n[PASO 1] Cargando configuraciones...')
try:
    db_cfg = DatabaseConfig()
    minio_cfg = MinIOConfig()
    print('  ✅ Configuraciones cargadas correctamente')
except Exception as e:
    print(f'  ❌ Error: {e}')
    sys.exit(1)

# Crear ETLPipeline (crea Bronze automáticamente)
print('\n[PASO 2] Creando ETLPipeline (crea bucket Bronze)...')
try:
    pipeline = ETLPipeline(db_cfg, minio_cfg)
    print('  ✅ ETLPipeline creado')
except Exception as e:
    print(f'  ❌ Error: {e}')
    sys.exit(1)

# Crear SilverManager (crea Silver automáticamente)
print('\n[PASO 3] Creando SilverManager (crea bucket Silver)...')
try:
    silver_mgr = SilverManager(minio_cfg)
    print('  ✅ SilverManager creado')
except Exception as e:
    print(f'  ❌ Error: {e}')
    import traceback
    traceback.print_exc()

# Crear GoldManager (crea Gold automáticamente)
print('\n[PASO 4] Creando GoldManager (crea bucket Gold)...')
try:
    gold_mgr = GoldManager(minio_cfg)
    print('  ✅ GoldManager creado')
except Exception as e:
    print(f'  ❌ Error: {e}')
    import traceback
    traceback.print_exc()

# Verificar que los buckets existen
print('\n[PASO 5] Verificando existencia de buckets...')
try:
    client = Minio(
        minio_cfg.endpoint,
        access_key=minio_cfg.access_key,
        secret_key=minio_cfg.secret_key,
        secure=False
    )

    bucket_base = minio_cfg.bucket.replace('-bronze', '')
    buckets_esperados = {
        f'{bucket_base}-bronze': 'Bronze (datos crudos)',
        f'{bucket_base}-silver': 'Silver (datos limpios)',
        f'{bucket_base}-gold': 'Gold (KPIs)',
    }

    print(f'\n  Bucket base: {bucket_base}')
    print(f'  Verificando buckets:')
    
    todos_existen = True
    for bucket, descripcion in buckets_esperados.items():
        try:
            exists = client.bucket_exists(bucket)
            if exists:
                print(f'    ✅ {bucket:<30} ({descripcion})')
            else:
                print(f'    ❌ {bucket:<30} ({descripcion}) - NO EXISTE')
                todos_existen = False
        except Exception as e:
            print(f'    ❌ {bucket:<30} ({descripcion}) - ERROR: {e}')
            todos_existen = False

    print()
    if todos_existen:
        print('=' * 80)
        print('✅ PRUEBA EXITOSA: Todos los 3 buckets se crearon automáticamente')
        print('   - meteo-bronze: Bronze layer ✓')
        print('   - meteo-silver: Silver layer ✓')
        print('   - meteo-gold: Gold layer ✓')
        print('=' * 80)
        sys.exit(0)
    else:
        print('=' * 80)
        print('❌ PRUEBA FALLIDA: No todos los buckets fueron creados')
        print('=' * 80)
        sys.exit(1)

except Exception as e:
    print(f'\n  ❌ Error verificando buckets: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
