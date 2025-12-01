# 🌤️ Sistema ETL Incremental PostgreSQL → MinIO

Sistema automatizado de extracción, transformación y carga (ETL) que extrae **solo datos nuevos** de PostgreSQL y los almacena en formato Parquet en MinIO (capa Bronce de un Data Lake).

## 📋 Descripción General

Este proyecto implementa un pipeline ETL incremental con **arquitectura modular orientada a objetos** que:
- ✅ Extrae **solo registros nuevos** de todas las tablas de PostgreSQL
- ✅ Detecta automáticamente **Primary Keys** o columnas de rastreo (timestamps o IDs incrementales)
- ✅ **Valida datos nuevos** antes de procesar (compara último valor vs máximo actual)
- ✅ Guarda datos en formato **Parquet comprimido**
- ✅ Sube archivos a **MinIO** (almacenamiento objeto compatible S3)
- ✅ Mantiene un **control de estado** para evitar duplicados
- ✅ Ejecuta automáticamente cada 10 segundos (configurable)
- ✅ **Código modular**: cada componente en su propio archivo
- ✅ **Fácil mantenimiento**: estructura clara y comentada

---

## 🏗️ Arquitectura

```
PostgreSQL (Origen)
    ↓
[ETLPipeline] → Extracción incremental
    ↓
Archivos Parquet (/tmp)
    ↓
MinIO (Capa Bronce)
    ↓
meteo-bronze/tabla_nombre/tabla_TIMESTAMP.parquet
```

---

## 📁 Estructura del Proyecto (Modular OOP)

```
pruebaMeteorologica/
├── main.py                          # 🚀 Punto de entrada principal
├── run_scheduler.sh                 # Script Bash para ejecutar el sistema
├── README.md                        # Documentación completa
├── config/                          # 📝 Configuraciones
│   ├── __init__.py
│   ├── database_config.py          # Configuración de PostgreSQL
│   └── minio_config.py             # Configuración de MinIO
├── etl/                             # 🔧 Componentes del pipeline ETL
│   ├── __init__.py
│   ├── control_manager.py          # Gestión de tabla de control
│   ├── table_inspector.py          # Inspección de estructura de tablas
│   ├── data_extractor.py           # Extracción incremental de datos
│   ├── parquet_writer.py           # Escritura de archivos Parquet
│   ├── minio_uploader.py           # Subida de archivos a MinIO
│   ├── table_processor.py          # Procesamiento de tabla individual
│   └── pipeline.py                 # Pipeline completo del ETL
└── venv_meteo/                      # Entorno virtual Python
```

### **🎯 Ventajas de la estructura modular:**

1. **Separación de responsabilidades**: Cada clase tiene una función específica
2. **Reutilización**: Puedes importar componentes individualmente
3. **Testing**: Facilita pruebas unitarias por componente
4. **Mantenibilidad**: Fácil localizar y modificar funcionalidades
5. **Escalabilidad**: Agregar nuevas features sin tocar código existente
6. **Legibilidad**: Código organizado y bien documentado

---

## 🔧 Componentes del Sistema

### 1️⃣ **Módulo `config/` - Configuraciones**

#### **`DatabaseConfig`** (database_config.py)
Clase que encapsula la configuración de PostgreSQL leyendo variables de entorno.

**Propiedades:**
- `user`: Usuario de PostgreSQL
- `password`: Contraseña
- `host`: IP del servidor
- `database`: Nombre de la base de datos
- `connection_url`: URL de conexión formateada

#### **`MinIOConfig`** (minio_config.py)
Clase que encapsula la configuración de MinIO.

**Propiedades:**
- `alias`: Alias configurado con `mc alias set`
- `bucket`: Nombre del bucket de destino

---

### 2️⃣ **Módulo `etl/` - Pipeline ETL**

#### **`ETLControlManager`** (control_manager.py)
Gestiona la tabla `etl_control` que rastrea el estado de extracción de cada tabla.

**Métodos:**
- `initialize_table()`: Crea la tabla de control si no existe
- `get_last_extracted_value(table_name)`: Obtiene el último valor extraído
- `update_last_extracted_value(table_name, value, column)`: Actualiza usando UPSERT

**Estructura de `etl_control`:**
```sql
CREATE TABLE etl_control (
    table_name VARCHAR(255) PRIMARY KEY,
    last_extracted_value VARCHAR(255),
    last_extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tracking_column VARCHAR(255)
)
```

#### **`TableInspector`** (table_inspector.py)
Inspecciona la estructura de las tablas de PostgreSQL.

**Métodos:**
- `get_all_tables()`: Lista todas las tablas (excepto etl_control)
- `get_columns(table_name)`: Obtiene columnas con sus tipos
- `detect_tracking_column(table_name)`: Detecta la mejor columna para rastreo

**Prioridad de detección:**
1. Columnas de timestamp (`created_at`, `updated_at`, etc.)
2. PRIMARY KEY numérica (consulta metadatos PostgreSQL)
3. Columna llamada 'id' genérica

#### **`DataExtractor`** (data_extractor.py)
Extrae datos incrementales de PostgreSQL.

**Métodos:**
- `extract_incremental(last_value)`: Extrae solo datos nuevos

**Lógica:**
- Si `last_value` existe: `SELECT * WHERE columna > last_value`
- Si es primera carga: `SELECT * FROM tabla`

#### **`ParquetWriter`** (parquet_writer.py)
Gestiona la escritura de archivos Parquet.

**Métodos:**
- `write(dataframe)`: Guarda DataFrame en formato Parquet
- `cleanup()`: Elimina archivo temporal

#### **`MinIOUploader`** (minio_uploader.py)
Gestiona la subida de archivos a MinIO.

**Métodos:**
- `upload(local_path, table_name, file_name)`: Sube archivo usando cliente `mc`

#### **`TableProcessor`** (table_processor.py)
Orquesta el procesamiento completo de una tabla.

**Flujo:**
1. Detecta columna de rastreo
2. Obtiene último valor procesado
3. Extrae datos nuevos
4. Guarda en Parquet
5. Sube a MinIO
6. Actualiza control

**Retorna:** Cantidad de registros procesados

#### **`ETLPipeline`** (pipeline.py)
Pipeline principal que coordina todo el ETL.

**Métodos:**
- `process_batch()`: Procesa un batch completo de todas las tablas
- `run_continuous(interval_seconds)`: Ejecuta el ETL en bucle infinito

---

### 3️⃣ **`main.py` - Punto de Entrada**

Script principal que inicializa y ejecuta el sistema ETL.

**Funcionalidad:**
- Carga configuraciones (DB y MinIO)
- Crea instancia del pipeline
- Ejecuta en modo continuo con intervalo de 10 segundos
- Maneja interrupción con Ctrl+C

---

### 4️⃣ **`run_scheduler.sh` - Script de Ejecución**

Script Bash que ejecuta el ETL de forma continua en intervalos regulares.

Script Bash que configura variables de entorno y ejecuta `main.py`.

#### **Configuración:**

```bash
# --- POSTGRESQL ---
export PG_DB="cine"
export PG_USER="postgres"
export PG_PASS="1234"
export PG_HOST="127.0.0.1"

# --- MINIO ---
export MINIO_ALIAS="mi_minio"
export MINIO_BUCKET="meteo-bronze"

# --- EJECUCIÓN ---
PYTHON_SCRIPT="main.py"
PYTHON_VENV="venv_meteo/bin/python"
```

**Características:**
- ✅ Exporta variables de entorno
- ✅ Usa Python del entorno virtual
- ✅ Ejecuta `main.py` que contiene el bucle infinito
- ✅ Detener con `Ctrl+C`

---

## 🚀 Instalación y Configuración

### **Requisitos previos:**

1. **PostgreSQL** corriendo con tablas a procesar
2. **MinIO** instalado y configurado
3. **Cliente MinIO (`mc`)** instalado:
   ```bash
   wget https://dl.min.io/client/mc/release/linux-amd64/mc
   chmod +x mc
   sudo mv mc /usr/local/bin/
   ```

### **Paso 1: Clonar y configurar entorno**

```bash
cd /home/andrews/Documentos/pruebaMeteorologica

# Activar entorno virtual
source venv_meteo/bin/activate

# Instalar dependencias (si no están instaladas)
pip install pandas sqlalchemy psycopg2-binary pyarrow
```

### **Paso 2: Configurar MinIO**

```bash
# Configurar alias de MinIO
mc alias set mi_minio http://localhost:9000 minioadmin minioadmin

# Crear bucket
mc mb mi_minio/meteo-bronze

# Verificar conexión
mc ls mi_minio
```

### **Paso 3: Configurar credenciales**

Editar `run_scheduler.sh` con tus credenciales:

```bash
export PG_DB="tu_base_datos"
export PG_USER="tu_usuario"
export PG_PASS="tu_contraseña"
export PG_HOST="ip_servidor_postgres"

export MINIO_ALIAS="mi_minio"
export MINIO_BUCKET="meteo-bronze"
```

### **Paso 4: Dar permisos de ejecución**

```bash
chmod +x run_scheduler.sh
```

---

## ▶️ Uso

### **Ejecución recomendada (con script bash):**

```bash
./run_scheduler.sh
```

### **Ejecución manual con Python:**

```bash
# Exportar variables de entorno
export PG_DB="cine" PG_USER="postgres" PG_PASS="1234" PG_HOST="127.0.0.1"
export MINIO_ALIAS="mi_minio" MINIO_BUCKET="meteo-bronze"

# Activar entorno virtual y ejecutar
source venv_meteo/bin/activate
python main.py
```

El sistema ejecutará el ETL cada **10 segundos** indefinidamente. Para detener, presiona `Ctrl+C`.

### **Cambiar frecuencia de ejecución:**

Editar en `main.py` la función `main()`:

```python
# Cambiar el intervalo (en segundos)
pipeline.run_continuous(interval_seconds=10)   # 10 segundos (actual)
pipeline.run_continuous(interval_seconds=60)   # 1 minuto
pipeline.run_continuous(interval_seconds=300)  # 5 minutos
```

---

## 📊 Ejemplo de Ejecución

### **Primera ejecución:**

```
🚀 Iniciando Sistema ETL Incremental
============================================================
📊 Base de datos: cine@127.0.0.1
🗄️  MinIO Bucket: meteo-bronze
============================================================

--- INICIO DE BATCH: 2025-12-01 23:10:15 ---

Procesando tabla: movie
   🆕 Carga Inicial (movie_id)
   📦 Registros nuevos: 3
   ✅ Subido a MinIO: movie_20251201231015.parquet

Procesando tabla: person
   🆕 Carga Inicial (person_id)
   📦 Registros nuevos: 9
   ✅ Subido a MinIO: person_20251201231015.parquet

🎯 RESUMEN: 12 registros nuevos en este batch.
Esperando 10 segundos...
```

### **Segunda ejecución (10 segundos después - sin cambios):**

```
--- INICIO DE BATCH: 2025-12-01 23:10:25 ---

Procesando tabla: movie
   ✓ No hay datos nuevos.

Procesando tabla: person
   ✓ No hay datos nuevos.

🎯 RESUMEN: 0 registros nuevos en este batch.
Esperando 10 segundos...
```

### **Tercera ejecución (después de insertar 2 películas nuevas):**

```
--- INICIO DE BATCH: 2025-12-01 23:10:35 ---

Procesando tabla: movie
   📊 Incremental (movie_id) > 3
   📦 Registros nuevos: 2
   ✅ Subido a MinIO: movie_20251201231035.parquet

Procesando tabla: person
   ✓ No hay datos nuevos.

🎯 RESUMEN: 2 registros nuevos en este batch.
Esperando 10 segundos...
```

---

## 📂 Estructura de Archivos en MinIO

```
meteo-bronze/
├── movie/
│   ├── movie_20251201231015.parquet  (3 registros - primera carga)
│   ├── movie_20251201231035.parquet  (2 registros - solo nuevos)
│   └── movie_20251202081525.parquet  (1 registro - solo nuevo)
├── person/
│   ├── person_20251201231015.parquet  (9 registros - primera carga)
│   └── person_20251202091035.parquet  (4 registros - solo nuevos)
├── genre/
│   └── genre_20251201231015.parquet  (5 registros - primera carga)
└── keyword/
    └── keyword_20251201231015.parquet  (120 registros - primera carga)
```

**Cada archivo Parquet contiene SOLO los registros nuevos** desde la última extracción. La estructura de carpetas replica los nombres de las tablas de PostgreSQL.

---

## 🔍 Verificación de Datos

### **Ver archivos en MinIO:**

```bash
mc ls mi_minio/meteo-bronze/
mc ls mi_minio/meteo-bronze/movie/
```

### **Descargar archivo Parquet:**

```bash
mc cp mi_minio/meteo-bronze/movie/movie_20251201231015.parquet ./
```

### **Leer Parquet con Python:**

```python
import pandas as pd

df = pd.read_parquet('movie_20251201231015.parquet')
print(df.head())
print(f"Total registros: {len(df)}")
print(df.columns.tolist())  # Ver columnas
```

### **Consultar tabla de control en PostgreSQL:**

```sql
SELECT * FROM etl_control;
```

Resultado:
```
table_name  | last_extracted_value    | last_extracted_at       | tracking_column
------------|-------------------------|-------------------------|----------------
movie       | 5                       | 2025-12-01 23:10:35     | movie_id
person      | 9                       | 2025-12-01 23:10:15     | person_id
genre       | 5                       | 2025-12-01 23:10:15     | genre_id
keyword     | 120                     | 2025-12-01 23:10:15     | keyword_id
```

---

## 🛠️ Solución de Problemas

### **Error: "El cliente 'mc' no está instalado"**

```bash
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/
mc --version
```

### **Error: "Falló la carga a MinIO"**

Verificar configuración del alias:

```bash
mc alias list
mc alias set mi_minio http://localhost:9000 minioadmin minioadmin
```

### **Error de conexión a PostgreSQL**

Verificar credenciales en `run_scheduler.sh`:

```bash
psql -h 127.0.0.1 -U postgres -d cine
```

### **No detecta columna de rastreo**

El sistema automáticamente detecta columnas de rastreo en este orden:
1. **Columnas timestamp:** `created_at`, `updated_at`, `timestamp`, `fecha`
2. **PRIMARY KEY numérico:** Detectado desde metadatos de PostgreSQL
3. **Columna 'id':** Si existe y es numérica

Si tus tablas usan nombres personalizados, edita `detect_tracking_column()` en `etl/table_inspector.py`:

```python
timestamp_candidates = ['created_at', 'updated_at', 'timestamp', 'fecha', 'date', 'datetime', 'tu_columna_custom']
```

---

## 📈 Optimizaciones Futuras

- [ ] Paralelización de tablas con `multiprocessing`
- [ ] Soporte para particionamiento por fecha en MinIO
- [ ] Compresión adicional con Snappy/GZIP
- [ ] Integración con Apache Airflow
- [ ] Métricas y alertas con Prometheus/Grafana
- [ ] Soporte para CDC (Change Data Capture) con Debezium

---

## 📝 Notas Importantes

1. **Límite de seguridad:** Por defecto extrae máximo 10,000 filas por tabla por ejecución (ajustable en `etl/data_extractor.py`).

2. **Archivos incrementales:** Cada Parquet contiene SOLO datos nuevos. Para análisis, deberás unir todos los archivos de una tabla.

3. **Primera ejecución lenta:** La primera vez extrae todos los datos. Las siguientes solo incrementales.

4. **Tablas sin rastreo:** Si una tabla no tiene timestamp ni PRIMARY KEY numérico, será **OMITIDA** (no se procesará).

5. **Validación automática:** El sistema compara el último valor procesado con el máximo actual en la tabla antes de extraer datos. Si no hay cambios, omite la extracción.

6. **Arquitectura OOP:** El código está organizado en módulos (`config/` y `etl/`) siguiendo principios de programación orientada a objetos para facilitar mantenimiento y extensión.

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────┐
│ PostgreSQL  │  (Base de datos cine)
│   (cine)    │  ← Tablas: movie, person, genre, keyword...
└──────┬──────┘
       │
       │ 1. SQLAlchemy extrae datos incrementales
       ↓
┌─────────────────────────────────────────────────┐
│          Sistema ETL (Python OOP)               │
│ ┌─────────────────────────────────────────────┐ │
│ │ ETLControlManager: Rastrea último valor    │ │
│ │ TableInspector: Detecta PRIMARY KEYs       │ │
│ │ DataExtractor: Extrae solo datos nuevos    │ │
│ │ ParquetWriter: Genera archivos .parquet    │ │
│ │ MinIOUploader: Sube a object storage       │ │
│ └─────────────────────────────────────────────┘ │
└──────┬──────────────────────────────────────────┘
       │
       │ 2. Archivos Parquet comprimidos
       ↓
┌─────────────┐
│   MinIO     │  (Object Storage - Capa Bronze)
│   Bucket:   │  ← Estructura: meteo-bronze/tabla/archivo.parquet
│ meteo-bronze│
└─────────────┘
```

**Flujo completo:**
1. El sistema consulta PostgreSQL cada 10 segundos
2. Detecta PRIMARY KEY o timestamp de cada tabla
3. Compara último valor procesado vs máximo actual
4. Si hay datos nuevos: extrae → convierte a Parquet → sube a MinIO
5. Si no hay cambios: omite procesamiento
6. Actualiza tabla de control con nuevo último valor

---

## 👤 Autor

Sistema desarrollado para procesamiento ETL incremental de base de datos de cine con arquitectura Data Lake.

---

## 📄 Licencia

Este proyecto es de uso interno para procesamiento de datos.
