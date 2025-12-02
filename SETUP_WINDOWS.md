# ⚙️ Configuración para Windows

## 1. Requisitos previos

- Python 3.8+
- MinIO servidor corriendo (localmente o en red)
- PostgreSQL accesible desde tu máquina

## 2. Configurar las variables de entorno

Abre `run_scheduler.ps1` y modifica estas líneas con tus datos reales:

```powershell
# Base de Datos PostgreSQL
$env:PG_HOST = "10.202.50.50"       # IP o localhost
$env:PG_USER = "postgres"           # Usuario
$env:PG_PASS = "1234"               # Contraseña
$env:PG_DB = "postgres"             # Base de datos

# MinIO
$env:MINIO_ENDPOINT = "localhost:9000"      # IP:puerto de MinIO
$env:MINIO_ACCESS_KEY = "minioadmin"        # Clave de acceso
$env:MINIO_SECRET_KEY = "minioadmin"        # Clave secreta
$env:MINIO_BUCKET = "meteo-bronze"         # Nombre del bucket
```

## 3. Crear el bucket en MinIO (si no existe)

Si usas MinIO localmente, accede a la consola web:
- URL: `http://localhost:9001`
- Usuario/Contraseña: minioadmin/minioadmin
- Crear bucket llamado `meteo-bronze`

O usa `mc` desde terminal:
```bash
mc alias set myminio http://localhost:9000 minioadmin minioadmin
mc mb myminio/meteo-bronze
```

## 4. Ejecutar el sistema

```powershell
# En PowerShell
.\run_scheduler.ps1
```

## 5. Verificar que funciona

El sistema debería mostrar algo como:

```
════════════════════════════════════════════════════
🚀 Iniciando Sistema ETL Incremental PostgreSQL → MinIO
Presiona Ctrl+C para detener.
════════════════════════════════════════════════════

============================================================
🚀 Iniciando Sistema ETL Incremental
============================================================
📊 Base de datos: postgres@10.202.50.50
🗄️  MinIO Bucket: meteo-bronze
============================================================

Procesando tabla: sensor_readings
   📦 Registros nuevos: 45
   ✅ Subido a MinIO: sensor_readings_20251202091647.parquet
```

## 🐛 Solucionar problemas

### Error: "El sistema no puede encontrar el archivo especificado"
- Verifica que las rutas temporales de Windows sean accesibles
- Los archivos se guardan en: `%TEMP%` (generalmente `C:\Users\...\AppData\Local\Temp`)

### Error: "Connection refused" en MinIO
- Verifica que MinIO está corriendo en `MINIO_ENDPOINT`
- Comprueba las credenciales en `MINIO_ACCESS_KEY` y `MINIO_SECRET_KEY`

### Error: "Table control table not found"
- El sistema crea automáticamente la tabla `etl_control` en PostgreSQL
- Verifica que tienes permisos de CREATE en la base de datos

---

**Más información:** Ver `README.md` para detalles técnicos completos.
