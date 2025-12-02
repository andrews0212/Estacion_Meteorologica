# 🌤️ Sistema ETL Incremental PostgreSQL → MinIO

Sistema automatizado de extracción, transformación y carga (ETL) que extrae **solo datos nuevos** de PostgreSQL y los almacena en MinIO con arquitectura Data Lake de capas (Bronce → Silver).

---

## 📋 Contenido

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Instalación y Configuración](#instalación-y-configuración)
4. [Uso](#uso)
5. [Estructura del Código](#estructura-del-código)
6. [Refactorización OOP](#refactorización-oop)
7. [Procesamiento de Datos](#procesamiento-de-datos)
8. [Solución de Problemas](#solución-de-problemas)

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
- `ETLControlQueries`: Queries de tabla de control

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
