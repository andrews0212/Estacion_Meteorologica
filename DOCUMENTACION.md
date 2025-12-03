# 🌤️ Sistema ETL Incremental PostgreSQL → MinIO (Bronce-Silver)

Sistema automatizado de extracción, transformación y carga (ETL) que extrae **solo datos nuevos** de PostgreSQL, los almacena en MinIO (capa Bronce) y automáticamente los **limpia y consolida** en una única capa Silver.

**Características principales:**
- ✅ Extracción incremental desde PostgreSQL
- ✅ Limpieza automática (Bronce → Silver)
- ✅ Consolidación en archivo único por tabla
- ✅ Estrategia REPLACE: mantiene solo la versión más reciente
- ✅ Arquitectura modular OOP
- ✅ Ejecución automática cada 5 minutos

---

## 📋 Contenido

1. [Descripción General](#descripción-general)
2. [Arquitectura y Flujo](#arquitectura-y-flujo)
3. [Instalación y Configuración](#instalación-y-configuración)
4. [Uso y Ejecución](#uso-y-ejecución)
5. [Estructura del Código](#estructura-del-código)
6. [Capa Bronce](#capa-bronce)
7. [Capa Silver](#capa-silver)
8. [Limpieza Automática](#limpieza-automática)
9. [Solución de Problemas](#solución-de-problemas)

---

## 📋 Descripción General

### ¿Qué hace?

```
PostgreSQL
    ↓
[Extracción Incremental]
    ↓
MinIO Bronce (CSV crudos)
    ↓
[Limpieza Automática]
    ↓
MinIO Silver (CSV consolidado + limpio)
```

### Flujo de Datos Automático

**Ciclo completo cada 5 minutos:**

1. **Extracción** (2-3 seg)
   - Detecta columnas de rastreo
   - Extrae solo registros nuevos
   - Guarda en MinIO Bronce (CSV)

2. **Limpieza** (1-2 seg)
   - Descarga todos los CSV de Bronce
   - Los combina en un único DataFrame
   - Aplica reglas de limpieza
   - Guarda en MinIO Silver (CSV único)
   - Elimina versiones antiguas

3. **Espera** (5 minutos)

4. **Repite** indefinidamente

---

## 🏗️ Arquitectura y Flujo

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                      MAIN.PY                                │
│              (Sistema ETL + Limpieza)                       │
└────────────┬────────────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────────┐   ┌──────────────┐
│   Pipeline  │   │  DataCleaner │
│   (Extrae)  │   │  (Limpia)    │
└────────────┬┘   └──────────┬───┘
             │               │
    ┌────────▼────────┐     │
    │  PostgreSQL     │     │
    │  (Origen)       │     │
    └─────────────────┘     │
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    ▼                       │                       ▼
┌──────────────┐           │               ┌──────────────┐
│ MinIO Bronce │           │               │ MinIO Silver │
│ (CSV crudos) │           └──────────────→│ (CSV limpio) │
└──────────────┘                           └──────────────┘
```

### Directorio del Proyecto

```
Estacion_Meteorologica/
├── main.py                          # 🚀 Punto de entrada (orquesta todo)
├── run_scheduler.ps1                # Script PowerShell
├── run_scheduler.sh                 # Script Bash
│
├── config/
│   ├── database_config.py           # Config PostgreSQL
│   └── minio_config.py              # Config MinIO
│
├── etl/
│   ├── pipeline.py                  # Orquestación extracción
│   ├── table_processor.py           # Procesamiento por tabla
│   ├── cleaners/                    # 🆕 MÓDULO DE LIMPIEZA
│   │   ├── __init__.py
│   │   └── data_cleaner.py          # 🆕 Limpieza automática
│   ├── extractors/
│   │   ├── data_extractor.py        # Extracción incremental
│   │   └── table_inspector.py       # Inspección de schema
│   ├── writers/
│   │   ├── csv_writer.py            # Escritura CSV
│   │   └── file_writer.py           # Interfaz base
│   ├── uploaders/
│   │   └── minio_uploader.py        # Carga a MinIO
│   ├── control/
│   │   └── control_manager.py       # Gestión de estado
│   ├── etl_state.py                 # Estado JSON
│   └── utils/
│       └── db_utils.py              # Utilidades BD
│
├── .etl_state.json                  # Estado incremental
│
├── notebooks/
│   └── templates/
│       └── limpieza_template.ipynb   # Notebook alternativa
│
└── venv_meteo/                      # Entorno virtual
```

---

## 🚀 Instalación y Configuración

### Requisitos Previos

- Python 3.8+
- PostgreSQL
- MinIO (servidor local o remoto)
- Windows: PowerShell 5+, Linux/Mac: Bash

### Paso 1: Crear Entorno Virtual

```powershell
# Windows
python -m venv venv_meteo
.\venv_meteo\Scripts\Activate

# Linux/Mac
python3 -m venv venv_meteo
source venv_meteo/bin/activate
```

### Paso 2: Instalar Dependencias

```bash
pip install pandas sqlalchemy psycopg2-binary minio
```

### Paso 3: Configurar Variables de Entorno

**En `run_scheduler.ps1` (Windows):**
```powershell
$env:PG_DB = "postgres"
$env:PG_USER = "postgres"
$env:PG_PASS = "1234"
$env:PG_HOST = "10.202.50.50"

$env:MINIO_ENDPOINT = "localhost:9000"
$env:MINIO_ACCESS_KEY = "minioadmin"
$env:MINIO_SECRET_KEY = "minioadmin"
$env:MINIO_BUCKET = "meteo-bronze"
```

**En `run_scheduler.sh` (Linux/Mac):**
```bash
export PG_HOST="10.202.50.50"
export PG_USER="postgres"
export PG_PASS="1234"
export PG_DB="postgres"
export MINIO_ENDPOINT="localhost:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin"
export MINIO_BUCKET="meteo-bronze"
```

### Paso 4: Crear Buckets en MinIO

```bash
# Configurar alias MinIO
mc alias set myminio http://localhost:9000 minioadmin minioadmin

# Crear buckets
mc mb myminio/meteo-bronze
mc mb myminio/meteo-silver

# Verificar
mc ls myminio
```

---

## ▶️ Uso y Ejecución

### Ejecución Principal (RECOMENDADO)

```powershell
# Activar entorno
.\venv_meteo\Scripts\Activate

# Ejecutar
python main.py

# Salida esperada:
# ════════════════════════════════════════════════════
# 🚀 Iniciando Sistema ETL Incremental PostgreSQL → MinIO
# ════════════════════════════════════════════════════
# 
# --- CICLO 1: 2025-12-03 09:40:12 ---
# Procesando tabla: sensor_readings
#    📊 Incremental (timestamp)
# [INFO] Iniciando limpieza automática...
# ================================================================================
# [PROCESO] Limpiando sensor_readings
# ...
```

**Presionar Ctrl+C para detener.**

### Salida Esperada

```
--- CICLO 1: 2025-12-03 09:40:12 ---

Procesando tabla: sensor_readings
   📊 Incremental (timestamp)
      > 2025-10-23T12:11:04.612475+00:00
   📦 Registros nuevos: 97
   ✅ Subido a MinIO: sensor_readings_bronce_20251203093625.csv

🎯 RESUMEN: 97 registros nuevos en este batch.

[INFO] Iniciando limpieza automática...

================================================================================
[PROCESO] Limpiando sensor_readings
================================================================================
[INFO] Encontrados 1 archivo(s) de sensor_readings
       - sensor_readings/sensor_readings_bronce_20251203093625.csv
[INFO] Combinando 1 archivo(s)...
[OK] Cargado: sensor_readings_bronce_20251203093625.csv (97 filas)
[OK] DataFrames combinados: 97 filas totales
[INFO] Limpiando datos...
[OK] Duplicados eliminados: 97 → 97
[OK] Outliers en temperature: 13 reemplazados con mediana (24.00)
[OK] Columnas innecesarias eliminadas
[OK] Valores inválidos filtrados: 0 eliminadas → 97 filas finales
[INFO] Guardando en Silver (estrategia REPLACE)...
[EXITO] sensor_readings: 97 filas guardadas en Silver
[INFO] Archivo: sensor_readings_silver_20251203094013.csv
[INFO] Eliminando versiones antiguas...
[OK] Eliminado: sensor_readings_silver_20251203093847.csv
[OK] sensor_readings: 1 archivos eliminados (mantiene: sensor_readings_silver_20251203094013.csv)

[INFO] Esperando 300s...
```

---

## 🔧 Estructura del Código

### Configuración

#### **DatabaseConfig**
```python
from config import DatabaseConfig

config = DatabaseConfig()
# Propiedades:
# - user: str (usuario PostgreSQL)
# - password: str (contraseña)
# - host: str (IP/dominio)
# - database: str (nombre BD)
# - connection_url: str (URL formateada)
```

#### **MinIOConfig**
```python
from config import MinIOConfig

config = MinIOConfig()
# Propiedades:
# - endpoint: str (IP:puerto)
# - access_key: str
# - secret_key: str
# - bucket: str (meteo-bronze)
```

### Pipeline Principal

#### **ETLPipeline** (etl/pipeline.py)
Coordina extracción de todas las tablas.

```python
pipeline = ETLPipeline(db_config, minio_config)
total_records = pipeline.process_batch()  # Una ronda
pipeline.run_continuous(interval_seconds=300)  # Bucle infinito
```

#### **TableProcessor** (etl/table_processor.py)
Procesa una tabla individual.

```python
processor = TableProcessor(connection, table_name, state_manager, ...)
records = processor.process()
```

**Flujo:**
1. Detecta columna de rastreo
2. Obtiene último valor procesado
3. Extrae datos nuevos
4. Guarda en Bronce
5. Actualiza estado

### Extracción

#### **DataExtractor** (etl/extractors/data_extractor.py)
Extrae datos incrementales.

```python
extractor = DataExtractor(connection, "sensor_readings", "timestamp", "timestamp")
df = extractor.extract_incremental(last_value="2025-10-23T12:11:04.612475+00:00")
```

#### **TableInspector** (etl/extractors/table_inspector.py)
Inspecciona estructura de tabla.

```python
inspector = TableInspector(connection)
tables = inspector.get_all_tables()
tracking_col, tracking_type = inspector.detect_tracking_column("sensor_readings")
```

### Limpieza Automática 🆕

#### **DataCleaner** (etl/cleaners/data_cleaner.py)
Limpia datos de Bronce y genera Silver.

```python
cleaner = DataCleaner(minio_config)
rows_saved = cleaner.clean_table("sensor_readings")
```

**Proceso automático:**
1. Lista archivos CSV en Bronce
2. Descarga y combina todos
3. Aplica limpieza
4. Guarda en Silver
5. Elimina versiones antiguas (REPLACE)

---

## 💾 Capa Bronce

### Contenido
- Archivos CSV sin procesar
- Datos tal como salen de PostgreSQL
- Uno por cada extracción incremental
- Formato: `tabla_bronce_YYYYMMDDHHMMSS.csv`

### Estructura en MinIO

```
meteo-bronze/
├── sensor_readings/
│   ├── sensor_readings_bronce_20251203093625.csv  (97 filas)
│   └── sensor_readings_bronce_20251203100123.csv  (45 filas)
├── estaciones/
│   └── estaciones_bronce_20251203093625.csv  (50 filas)
└── [otras tablas]/
```

### Características
- ❌ Sin deduplicación
- ❌ Con outliers
- ❌ Columnas redundantes
- ✅ Histórico completo disponible

---

## 🧹 Capa Silver

### Contenido
- Archivos CSV limpios y consolidados
- **Un único archivo por tabla** (estrategia REPLACE)
- Datos combinados de todas las extracciones
- Formato: `tabla_silver_YYYYMMDDHHMMSS.csv`

### Estructura en MinIO

```
meteo-silver/
├── sensor_readings/
│   └── sensor_readings_silver_20251203094013.csv  (97 filas limpias)
├── estaciones/
│   └── estaciones_silver_20251203094013.csv  (50 filas limpias)
└── [otras tablas]/
```

### Características
- ✅ Sin duplicados
- ✅ Outliers reemplazados con mediana
- ✅ Columnas innecesarias eliminadas
- ✅ Valores en rangos válidos
- ✅ **Un único archivo consolidado**

---

## 🧹 Limpieza Automática

### Operaciones de Limpieza

#### 1. Eliminación de Duplicados
```
Antes:  100 filas
Después: 100 filas (ejemplo sin duplicados)
```

#### 2. Reemplazo de Outliers (Método IQR)
```
Temperatura normal: 10°C - 50°C
Cálculo:
  Q1 = Percentil 25
  Q3 = Percentil 75
  IQR = Q3 - Q1
  Límite inferior = Q1 - 1.5 × IQR
  Límite superior = Q3 + 1.5 × IQR
  
Outliers detectados: 13
Acción: Reemplazar con mediana (24.00°C)
```

#### 3. Eliminación de Columnas
```
Columnas eliminadas:
- uv_level
- vibration
- rain_raw
- wind_raw
- pressure
```

#### 4. Filtrado de Rangos
```
Temperatura: 10°C - 50°C
Humedad: 0% - 100%
```

### Estrategia REPLACE

**Problema:** ¿Qué pasa si se ejecuta múltiples veces?

**Solución:** REPLACE automático

```
CICLO 1 (09:00): Extrae 100 registros
  → Bronce: archivo #1 (100 filas)
  → Silver: sensor_readings_silver_20251203_090000.csv (100 limpias)

CICLO 2 (09:05): Extrae 50 nuevos registros
  → Bronce: archivo #2 (50 filas)
  → Combina Bronce #1 + #2 = 150 filas
  → Silver: sensor_readings_silver_20251203_090500.csv (150 limpias)
  → ❌ Elimina versión anterior
  → ✅ Mantiene solo la más reciente

CICLO 3 (09:10): Extrae 30 nuevos registros
  → Bronce: archivo #3 (30 filas)
  → Combina Bronce #1 + #2 + #3 = 180 filas
  → Silver: sensor_readings_silver_20251203_091000.csv (180 limpias)
  → ❌ Elimina versión anterior
  → ✅ Mantiene solo la más reciente
```

**Ventajas:**
- ✅ Dataset actualizado constantemente
- ✅ Archivo no crece indefinidamente
- ✅ Espacio controlado en MinIO
- ✅ Totalmente automático
- ✅ Sin intervención manual

---

## 🔍 Verificación de Datos

### Ver archivos en MinIO
```bash
mc ls myminio/meteo-bronze/sensor_readings/
mc ls myminio/meteo-silver/sensor_readings/
```

### Descargar archivo
```bash
mc cp myminio/meteo-silver/sensor_readings/sensor_readings_silver*.csv ./
```

### Leer con Pandas
```python
import pandas as pd

df = pd.read_csv('sensor_readings_silver_20251203_094013.csv')
print(f"Filas: {len(df)}")
print(f"Columnas: {len(df.columns)}")
print(df.head())
```

### Ver estado de extracciones
```python
from etl.etl_state import StateManager

manager = StateManager()
manager.display_state()
```

---

## 🛠️ Solución de Problemas

### Error: "No connection to PostgreSQL"
```powershell
# Verificar credenciales
$env:PG_HOST = "10.202.50.50"
$env:PG_USER = "postgres"
$env:PG_PASS = "1234"

# Probar conexión
psql -h 10.202.50.50 -U postgres -d postgres -c "SELECT 1"
```

### Error: "MinIO connection refused"
```bash
# Verificar que MinIO está ejecutándose
curl http://localhost:9000

# Configurar alias
mc alias set myminio http://localhost:9000 minioadmin minioadmin
mc ls myminio
```

### Error: "Columna de rastreo no detectada"
Editar en `etl/extractors/table_inspector.py`:
```python
TIMESTAMP_COLUMNS = ['created_at', 'updated_at', 'timestamp', 'fecha', 'tu_columna']
```

### No se generan archivos en Silver
1. Verificar que hay datos en Bronce
2. Revisar logs de `DataCleaner`
3. Ejecutar manualmente: `cleaner.clean_table("sensor_readings")`

### Archivos viejos se acumulan en Silver
- Verificar que `_manage_versions()` se ejecuta
- Ver logs de "Eliminado:"
- El REPLACE debe ocurrir automáticamente

---

## 📊 Estadísticas de Ejemplo

```
Sistema Ejecutado: 3 ciclos
Período: 09:00 - 09:10 (10 minutos)

BRONCE:
  sensor_readings: 3 archivos, 175 filas totales
  estaciones: 1 archivo, 50 filas
  
SILVER:
  sensor_readings: 1 archivo (REPLACE activo), 175 limpias
  estaciones: 1 archivo (REPLACE activo), 50 limpias

Limpieza:
  Duplicados eliminados: 0
  Outliers corregidos: 28
  Columnas eliminadas: 5
  Retención: 99.3%
```

---

## 📖 Documentación Adicional

- **MIGRACION_STATE_MANAGEMENT.md**: Gestión de estado JSON
- **ANALISIS_LIMPIEZA_CODIGO.md**: Código eliminado durante refactorización
- **ESTADO_FINAL_LIMPIEZA.md**: Estado actual del proyecto

---

**Última actualización:** 3 de Diciembre de 2025  
**Versión:** 3.0 (Con Limpieza Automática)  
**Estado:** ✅ Producción


---

## 📋 Descripción General

Este proyecto implementa un **pipeline ETL modular orientado a objetos** que:

✅ Extrae **solo registros nuevos** de todas las tablas de PostgreSQL  
✅ Detecta automáticamente **Primary Keys** o columnas de rastreo  
✅ **Valida datos nuevos** antes de procesar  
✅ Guarda datos en formato **CSV** (Bronce) y **Parquet** (Silver)  
✅ Sube archivos a **MinIO** (almacenamiento objeto compatible S3)  
✅ Mantiene un **control de estado** para evitar duplicados  
✅ Ejecuta automáticamente cada 5 minutos (configurable)  
✅ **Código modular**: cada componente en su propio archivo  
✅ **Fácil mantenimiento**: estructura clara con type hints  

---

## 🏗️ Arquitectura

### Sistema de Capas

```
PostgreSQL (Origen)
    ↓
[ETLPipeline] → Extracción incremental
    ↓
Archivos CSV (/tmp)
    ↓
MinIO Capa BRONCE (Raw Data)
    ↓
[Limpieza & Transformación]
    ↓
MinIO Capa SILVER (Datos Limpios)
```

### Componentes del Sistema

```
pruebaMeteorologica/
├── main.py                          # 🚀 Punto de entrada principal
├── run_scheduler.ps1                # Script PowerShell (Windows)
├── run_scheduler.sh                 # Script Bash (Linux)
├── DOCUMENTACION.md                 # 📖 Documentación completa
│
├── config/                          # 📝 Configuraciones
│   ├── __init__.py
│   ├── database_config.py          # Configuración PostgreSQL
│   └── minio_config.py             # Configuración MinIO
│
├── etl/                             # 🔧 Componentes del pipeline
│   ├── __init__.py
│   ├── db_utils.py                 # Utilidades BD centralizadas (NEW)
│   ├── control_manager.py          # Gestión de tabla de control
│   ├── table_inspector.py          # Inspección de estructura de tablas
│   ├── data_extractor.py           # Extracción incremental
│   ├── parquet_writer.py           # Escritura de archivos Parquet
│   ├── minio_uploader.py           # Subida a MinIO
│   ├── table_processor.py          # Procesamiento de tabla individual
│   ├── limpieza_bronce.py          # Limpieza automática
│   ├── silver_layer.py             # Transformación Silver
│   └── pipeline.py                 # Pipeline completo
│
├── notebooks/                       # 📊 Notebooks Jupyter
│   └── templates/
│       └── limpieza_template.ipynb  # Limpieza manual (alternativa)
│
└── venv_meteo/                      # Entorno virtual Python
```

---

## 🚀 Instalación y Configuración

### 1. Requisitos Previos

- **Python 3.8+**
- **PostgreSQL** corriendo con tablas a procesar
- **MinIO** instalado y configurado (servidor + cliente `mc`)
- **PySpark** (opcional, para silver_layer)

### 2. Instalar Dependencias

```powershell
# Entorno virtual
python -m venv venv_meteo
.\venv_meteo\Scripts\Activate

# Dependencias
pip install pandas sqlalchemy psycopg2-binary pyarrow minio
```

### 3. Configurar Variables de Entorno

**Archivo: `run_scheduler.ps1` (Windows)**
```powershell
# PostgreSQL
$env:PG_HOST = "10.202.50.50"       # IP o localhost
$env:PG_USER = "postgres"           # Usuario
$env:PG_PASS = "1234"               # Contraseña
$env:PG_DB = "postgres"             # Base de datos

# MinIO
$env:MINIO_ENDPOINT = "localhost:9000"      # IP:puerto
$env:MINIO_ACCESS_KEY = "minioadmin"        # Acceso
$env:MINIO_SECRET_KEY = "minioadmin"        # Secreto
$env:MINIO_BUCKET = "meteo-bronze"         # Bucket
```

**Archivo: `run_scheduler.sh` (Linux)**
```bash
export PG_HOST="10.202.50.50"
export PG_USER="postgres"
export PG_PASS="1234"
export PG_DB="postgres"

export MINIO_ENDPOINT="localhost:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin"
export MINIO_BUCKET="meteo-bronze"
```

### 4. Configurar MinIO

```bash
# Configurar alias
mc alias set myminio http://localhost:9000 minioadmin minioadmin

# Crear buckets
mc mb myminio/meteo-bronze
mc mb myminio/meteo-silver

# Verificar
mc ls myminio
```

---

## ▶️ Uso

### Opción 1: Ejecución Manual Completa (RECOMENDADO)

```powershell
# Terminal PowerShell
cd c:\Users\Alumno_AI\Desktop\Estacion_Meteorologica

# Configurar variables
$env:PG_DB='postgres'
$env:PG_USER='postgres'
$env:PG_PASS='1234'
$env:PG_HOST='10.202.50.50'
$env:MINIO_ENDPOINT='localhost:9000'
$env:MINIO_ACCESS_KEY='minioadmin'
$env:MINIO_SECRET_KEY='minioadmin'
$env:MINIO_BUCKET='meteo-bronze'

# Ejecutar (ciclo continuo: extrae + limpia)
.\venv_meteo\Scripts\python.exe main.py

# Presionar Ctrl+C para detener
```

**Ciclo cada 5 minutos:**
```
1. Extrae datos de PostgreSQL → Bronce (CSV)
2. Limpia automáticamente → Silver (Parquet)
3. Espera 5 minutos
4. Repite
```

### Opción 2: Limpieza Manual

```powershell
# Solo limpiar datos existentes en Bronce
.\venv_meteo\Scripts\python.exe limpiar_bronce.py
```

### Opción 3: Notebook Interactivo

```
1. Abrir: notebooks/templates/limpieza_template.ipynb
2. Ejecutar celdas 1-19 (configuración)
3. Ejecutar celda 20 (limpieza)
4. Datos guardados en Silver
```

---

## 🔧 Estructura del Código

### Configuraciones (`config/`)

#### **DatabaseConfig** (database_config.py)
```python
# Encapsula configuración de PostgreSQL
config = DatabaseConfig()
connection_url = config.connection_url  # postgresql://...
```

**Propiedades:**
- `user`: Usuario PostgreSQL
- `password`: Contraseña
- `host`: IP servidor
- `database`: Base de datos
- `connection_url`: URL formateada

#### **MinIOConfig** (minio_config.py)
```python
# Encapsula configuración de MinIO
config = MinIOConfig()
bucket = config.bucket  # meteo-bronze
silver_bucket = config.silver_bucket  # meteo-silver
```

---

### Pipeline ETL (`etl/`)

#### **1. ETLControlManager** (control_manager.py)
Rastrea el estado de extracción de cada tabla.

```python
manager = ETLControlManager(connection)
last_value = manager.get_last_extracted_value("sensor_readings")
manager.update_last_extracted_value("sensor_readings", 100, "id")
```

**Tabla de control:**
```sql
CREATE TABLE etl_control (
    table_name VARCHAR(255) PRIMARY KEY,
    last_extracted_value VARCHAR(255),
    last_extracted_at TIMESTAMP,
    tracking_column VARCHAR(255)
)
```

#### **2. TableInspector** (table_inspector.py)
Inspecciona estructura de tablas.

```python
inspector = TableInspector(connection)
tables = inspector.get_all_tables()
columns = inspector.get_columns("sensor_readings")
tracking_col = inspector.detect_tracking_column("sensor_readings")
```

**Detección de columna de rastreo (orden de prioridad):**
1. Timestamp: `created_at`, `updated_at`, `timestamp`
2. PRIMARY KEY numérico
3. Columna `id` genérica

#### **3. DataExtractor** (data_extractor.py)
Extrae datos incrementales.

```python
extractor = DataExtractor(connection, "sensor_readings")
df = extractor.extract_incremental(last_value=100)
```

**Lógica:**
- Si `last_value` existe: `SELECT * WHERE columna > last_value`
- Si primera carga: `SELECT * FROM tabla`

#### **4. ParquetWriter** (parquet_writer.py)
Escriba archivos Parquet.

```python
writer = ParquetWriter()
writer.write(df, "output.parquet")
```

**Estrategia Pattern:** Fácil agregar CSVWriter, JSONWriter, etc.

#### **5. MinIOUploader** (minio_uploader.py)
Sube archivos a MinIO.

```python
uploader = MinIOUploader(config)
uploader.upload("local_file.parquet", "sensor_readings", "file_name.parquet")
```

#### **6. TableProcessor** (table_processor.py)
Orquesta procesamiento completo de una tabla.

```python
processor = TableProcessor(connection, config)
records_count = processor.process("sensor_readings")  # Retorna cantidad
```

**Flujo:**
1. Detecta columna rastreo
2. Obtiene último valor procesado
3. Extrae datos nuevos
4. Guarda en Parquet
5. Sube a MinIO
6. Actualiza control

#### **7. ETLPipeline** (pipeline.py)
Pipeline principal que coordina todo.

```python
pipeline = ETLPipeline(config)
pipeline.process_batch()  # Procesa una ronda
pipeline.run_continuous(interval_seconds=300)  # Bucle infinito (5 min)
```

#### **8. Limpieza (limpieza_bronce.py)**
Limpieza de datos automática.

```python
cleaner = LimpiezaBronce(config)
cleaner.procesar_tabla("sensor_readings")
```

**Operaciones:**
- Elimina duplicados
- Reemplaza outliers con mediana (IQR)
- Elimina columnas innecesarias
- Filtra valores inválidos

#### **9. SilverLayer** (silver_layer.py)
Transformación de Bronce a Silver.

```python
silver = SilverLayer(config)
exito = silver.process("sensor_readings")  # Booleano
```

**Patrón Strategy para limpieza:**
- `DataCleaner` (clase abstracta)
- `SensorReadingsCleaner` (implementación específica)
- Fácil extender con nuevas limpiadoras

#### **10. DatabaseUtils** (db_utils.py - NUEVO)
Centraliza operaciones de base de datos.

```python
# Queries reutilizables
result = DatabaseUtils.fetch_one(connection, query, params)
rows = DatabaseUtils.fetch_all(connection, query)
DatabaseUtils.execute(connection, query, params)
```

**Clases:**
- `DatabaseUtils`: Métodos estáticos para ejecutar queries
- `TableQueryBuilder`: Constructor de queries

---

## 🎯 Refactorización OOP

### Características de Diseño

✅ **Separación de responsabilidades**: Cada clase, una función  
✅ **Type hints**: 100% cobertura de tipos  
✅ **Patrones de diseño**: Strategy, Factory, Builder  
✅ **SOLID principles**: Todos implementados  
✅ **Abstracción**: Clases base (Config, DataCleaner)  
✅ **Modularidad**: Componentes reutilizables  

### Clases Base (Herencia)

```python
# Base de configuraciones
class Config:
    @staticmethod
    def get_env(key: str, default: Optional[str] = None) -> str:
        value = os.environ.get(key, default)
        if value is None:
            raise ValueError(f"Variable requerida: {key}")
        return value

# DatabaseConfig hereda de Config
class DatabaseConfig(Config):
    def __init__(self, user: Optional[str] = None, ...):
        self.user = user or self.get_env('PG_USER', 'postgres')
```

### Patrón Strategy (Limpieza)

```python
from abc import ABC, abstractmethod

class DataCleaner(ABC):
    @abstractmethod
    def clean(self, df: DataFrame) -> DataFrame:
        pass

class SensorReadingsCleaner(DataCleaner):
    def clean(self, df: DataFrame) -> DataFrame:
        df = self._remove_duplicates(df)
        df = self._replace_outliers(df, "temperature")
        df = self._drop_unnecessary_columns(df)
        return df

# Usar
CLEANERS = {"sensor_readings": SensorReadingsCleaner()}
```

### Type Hints Completos

```python
def process(self, table_name: str) -> bool:
    """Procesa una tabla.
    
    Args:
        table_name: Nombre de la tabla
        
    Returns:
        bool: True si éxito, False si error
    """
    pass
```

---

## 📊 Procesamiento de Datos

### Capa Bronce (Bronze)
- **Tipo**: CSV
- **Contenido**: Datos sin procesar
- **Características**:
  - Contiene duplicados
  - Contiene outliers
  - Columnas redundantes

### Capa Silver (Silver)
- **Tipo**: CSV
- **Contenido**: Datos procesados
- **Características**:
  - Sin duplicados
  - Outliers reemplazados con mediana
  - Solo columnas relevantes
- **Estrategia**: **REPLACE** - Solo mantiene el dataset más reciente

### Operaciones de Limpieza (sensor_readings)

1. **Eliminar duplicados**
   ```python
   df = df.distinct()  # Spark: elimina filas idénticas
   ```

2. **Reemplazar outliers** (IQR method)
   ```
   Q1 = percentil 25
   Q3 = percentil 75
   IQR = Q3 - Q1
   Limites = [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
   Outliers: reemplazar con mediana
   ```

3. **Eliminar columnas**
   ```
   uv_level, vibration, rain_raw, wind_raw, pressure
   ```

4. **Filtrar valores inválidos**
   ```
   temperature: 10°C - 50°C
   humidity: 0% - 100%
   ```

### 🔄 Estrategia REPLACE: Gestión de Versiones

**Problema:** Si extraes múltiples veces, ¿cómo evitar acumular archivos?

**Solución:** Estrategia REPLACE automática

```
CICLO 1 (09:00):
  ✅ Extrae 100 filas → Bronce CSV #1
  ✅ Limpia → Silver: sensor_readings_silver_20251202_090000.csv (100 filas)

CICLO 2 (09:05):
  ✅ Extrae 50 filas → Bronce CSV #2
  ✅ Combina CSV #1 + #2 = 150 filas (sin duplicados)
  ✅ Limpia → Silver: sensor_readings_silver_20251202_090500.csv (150 filas)
  ✅ Elimina automáticamente versión anterior

CICLO 3 (09:10):
  ✅ Extrae 30 filas → Bronce CSV #3
  ✅ Combina todos = 180 filas (sin duplicados)
  ✅ Limpia → Silver: sensor_readings_silver_20251202_091000.csv (180 filas)
  ✅ Elimina automáticamente versión anterior
```

**Ventajas:**
- ✅ Siempre tienes el dataset más reciente
- ✅ El archivo NO crece indefinidamente
- ✅ Espacio en MinIO controlado y predecible
- ✅ Proceso automático, sin intervención manual

**Cómo funciona:**
1. Se guarda nuevo CSV en Silver con timestamp
2. El módulo `SilverManager` detecta versiones antiguas
3. Automáticamente elimina todas EXCEPTO la más reciente
4. Solo un archivo activo por tabla en Silver

---

## 📂 Estructura de Archivos en MinIO

### Bronce (meteo-bronze)
```
meteo-bronze/
├── sensor_readings/
│   ├── sensor_readings_bronce_20251202_091647.csv  (97 filas)
│   └── sensor_readings_bronce_20251202_101823.csv  (30 filas)
├── weather/
│   └── weather_bronce_20251202_091647.csv  (50 filas)
└── [otras tablas]/
    └── ...
```

### Silver (meteo-silver)
```
meteo-silver/
├── sensor_readings/
│   ├── sensor_readings_silver_20251202_130210.csv  (127 filas limpias)
│   └── sensor_readings_silver_20251202_140521.csv  (55 filas limpias)
├── weather/
│   └── weather_silver_20251202_130210.csv  (48 filas limpias)
└── [otras tablas]/
    └── ...
```

---

## 🔍 Verificación de Datos

### Ver archivos en MinIO
```bash
mc ls myminio/meteo-bronze/
mc ls myminio/meteo-bronze/sensor_readings/
```

### Descargar archivo
```bash
mc cp myminio/meteo-bronze/sensor_readings/sensor_readings_bronce_*.csv ./
```

### Leer con Python
```python
import pandas as pd

df = pd.read_csv('sensor_readings_bronce_20251202_091647.csv')
print(f"Filas: {len(df)}")
print(df.head())
```

### Consultar tabla de control
```sql
SELECT * FROM etl_control;
```

**Resultado esperado:**
```
table_name     | last_extracted_value | last_extracted_at  | tracking_column
---------------|----------------------|--------------------|-----------------
sensor_readings| 1000                 | 2025-12-02 13:02   | id
weather        | 500                  | 2025-12-02 13:01   | measurement_id
```

---

## 🛠️ Solución de Problemas

### Error: "El cliente 'mc' no está instalado"
```bash
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/
```

### Error: "Connection refused" en PostgreSQL
```powershell
# Verificar credenciales
psql -h 10.202.50.50 -U postgres -d postgres

# Verificar variables de entorno
echo $env:PG_HOST
echo $env:PG_USER
```

### Error: "Falló la carga a MinIO"
```bash
# Verificar alias
mc alias list
mc alias set myminio http://localhost:9000 minioadmin minioadmin

# Verificar conectividad
mc ls myminio
```

### Error: "Table etl_control not found"
El sistema crea la tabla automáticamente en la primera ejecución. Si no se crea:
```sql
CREATE TABLE etl_control (
    table_name VARCHAR(255) PRIMARY KEY,
    last_extracted_value VARCHAR(255),
    last_extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tracking_column VARCHAR(255)
)
```

### No detecta columna de rastreo
Editar en `etl/table_inspector.py`:
```python
# Agregar candidatos personalizados
timestamp_candidates = ['created_at', 'updated_at', 'fecha', 'date', 'tu_columna']
```

---

## 📈 Ejemplo de Ejecución Completa

```
════════════════════════════════════════════════════
🚀 Iniciando Sistema ETL Incremental
════════════════════════════════════════════════════
📊 Base de datos: postgres@10.202.50.50
🗄️  MinIO Bucket: meteo-bronze
════════════════════════════════════════════════════

--- INICIO DE BATCH: 2025-12-02 09:16:47 ---

Procesando tabla: sensor_readings
   📊 Detectada columna: id (numérica)
   🔍 Último valor: 900
   📦 Registros nuevos: 97
   💾 Guardando: sensor_readings_bronce_20251202_091647.csv
   ✅ Subido a Bronce
   🧹 Limpiando...
   ✅ Duplicados eliminados: 97 → 97
   ✅ Outliers reemplazados: 2
   ✅ Columnas eliminadas: 5
   ✅ Subido a Silver: sensor_readings_silver_20251202_091647.csv

Procesando tabla: weather
   📊 Detectada columna: created_at (timestamp)
   🔍 Último valor: 2025-12-02 08:00:00
   📦 Registros nuevos: 50
   💾 Guardando: weather_bronce_20251202_091647.csv
   ✅ Subido a Bronce
   🧹 Limpiando...
   ✅ Duplicados eliminados: 50 → 50
   ✅ Outliers reemplazados: 1
   ✅ Subido a Silver: weather_silver_20251202_091647.csv

🎯 RESUMEN: 147 registros nuevos en este batch.
⏰ Próxima ejecución: 09:21:47 (en 5 minutos)
```

---

## 📝 Próximos Pasos

- [ ] Agregar pruebas unitarias
- [ ] Implementar logging estructura (logging module)
- [ ] Agregar métricas y monitoreo
- [ ] Crear CLI para administración
- [ ] Implementar re-intentos automáticos
- [ ] Agregar alertas por errores

---

## 👤 Información del Proyecto

- **Tipo**: Data Lake ETL
- **Arquitectura**: Modular, OOP, SOLID
- **Lenguaje**: Python 3.8+
- **Frameworks**: SQLAlchemy, Pandas, PySpark, MinIO
- **Bases de datos**: PostgreSQL, MinIO (Object Storage)

---

## 📖 Documentación Técnica

Este archivo consolida toda la documentación técnica del proyecto. Todos los componentes están documentados con:
- Type hints completos
- Docstrings en métodos
- Ejemplos de uso
- Configuraciones recomendadas

Para preguntas específicas sobre componentes individuales, consultar los archivos en `etl/` y `config/`.

---

**Última actualización:** 2 de Diciembre de 2025  
**Versión:** 2.0 (Refactorización OOP Completa)
