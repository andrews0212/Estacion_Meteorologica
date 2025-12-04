#!/usr/bin/env python3
"""Script para probar creación automática de buckets en MinIO."""

import sys
sys.path.insert(0, '.')

from config import MinIOConfig, DatabaseConfig
from etl.pipeline import ETLPipeline
from minio import Minio

print('=' * 80)
print('[TEST] Probando creación automática de buckets en MinIO')
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

# Crear ETLPipeline (debe crear bucket Bronze automáticamente)
print('\n[PASO 2] Creando ETLPipeline (debe crear bucket Bronze)...')
try:
    pipeline = ETLPipeline(db_cfg, minio_cfg)
    print('  ✅ ETLPipeline creado exitosamente')
except Exception as e:
    print(f'  ❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Verificar que los buckets existen
print('\n[PASO 3] Verificando existencia de buckets...')
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
    print(f'  Buckets esperados:')
    
    todos_existen = True
    for bucket, descripcion in buckets_esperados.items():
        try:
            exists = client.bucket_exists(bucket)
            if exists:
                print(f'    ✅ {bucket} ({descripcion})')
            else:
                print(f'    ❌ {bucket} ({descripcion}) - NO EXISTE')
                todos_existen = False
        except Exception as e:
            print(f'    ❌ {bucket} ({descripcion}) - ERROR: {e}')
            todos_existen = False

    print()
    if todos_existen:
        print('=' * 80)
        print('✅ PRUEBA EXITOSA: Todos los buckets se crearon automáticamente')
        print('=' * 80)
    else:
        print('=' * 80)
        print('❌ PRUEBA FALLIDA: No todos los buckets fueron creados')
        print('=' * 80)

except Exception as e:
    print(f'\n  ❌ Error verificando buckets: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
