# 🌡️ Sistema de Monitoreo Meteorológico - Estación Meteorológica

Sistema automatizado de **ETL (Extract-Transform-Load)** que recopila datos de sensores meteorológicos, los procesa en capas (Bronze → Silver → Gold) y genera KPIs automáticos para análisis en tiempo real con Power BI.

---

## 📋 Tabla de Contenidos

- [Arquitectura General](#-arquitectura-general)
- [Componentes Principales](#-componentes-principales)
- [Flujo de Datos](#-flujo-de-datos)
- [Instalación](#-instalación)
- [Ejecución](#-ejecución)
- [Descripción de Módulos](#-descripción-de-módulos)
- [Estructura de Archivos](#-estructura-de-archivos)

---

## 🏗️ Arquitectura General

El sistema implementa una **arquitectura medallion** (3 capas):

```
PostgreSQL (BD Principal)
         ↓
    BRONCE (MinIO)
    [Datos extraídos crudos]
         ↓
    SILVER (MinIO)
    [Datos limpios y validados]
         ↓
    GOLD (MinIO)
    [KPIs y métricas agregadas]
         ↓
    FILE (Carpeta local)
    [Archivos para Power BI]
```

---

## 🎯 Componentes Principales

### 1. **`main.py`** - Sistema de Orquestación
**Qué hace**: Núcleo del sistema que coordina todo el pipeline ETL.

**Funcionalidades**:
- Inicializa el sistema con configuración de BD y MinIO
- Ejecuta **ciclos continuos** de extracción de datos
- Ejecuta **notebooks PySpark** automáticamente:
  - `limpieza_template.ipynb` → Genera capa Silver
  - `generacion_KPI.ipynb` → Genera capa Gold
- **Descarga automáticamente** archivos finales a carpeta `file/` para Power BI
- Reintentos automáticos si fallan descargas

**Parámetros principales**:
```python
extraction_interval = 300  # Segundos entre ciclos (5 minutos)
notebook_path = "notebooks/templates/limpieza_template.ipynb"
notebook_kpi_path = "notebooks/templates/generacion_KPI.ipynb"
```

**Métodos clave**:
- `run_cycle(cycle_num)`: Ejecuta un ciclo completo
- `_run_notebooks()`: Ejecuta limpieza (Silver) y KPIs (Gold)
- `_download_gold_for_powerbi()`: Descarga archivos a `file/`

---

### 2. **`etl/pipeline.py`** - Pipeline de Extracción
**Qué hace**: Coordina la extracción incremental de datos desde PostgreSQL.

**Funcionalidades**:
- **Inspecciona** tabla `sensor_readings` en PostgreSQL
- Realiza **extracción incremental** (solo datos nuevos desde última ejecución)
- Utiliza `.etl_state.json` para rastrear posición de lectura
- Usa **pool de conexiones** para mejor rendimiento
- Serializa datos a CSV temporales
- Sube archivos a bucket **meteo-bronze** en MinIO

**Método principal**:
- `process_batch()`: Procesa todos los registros nuevos

---

### 3. **`etl/table_processor.py`** - Procesador de Tablas
**Qué hace**: Procesa cada tabla individual durante la extracción.

**Funcionalidades**:
- Detecta automáticamente **esquema de tabla** (columnas y tipos)
- Calcula **fingerprint de datos** para detectar cambios
- Realiza **selección incremental** (registros con `id` mayor al último procesado)
- Soporta múltiples formatos: CSV, Parquet
- Genera estadísticas de procesamiento (registros nuevos, duplicados, errores)

---

### 4. **`etl/extractors/`** - Módulo de Extracción
**Componentes**:

#### `data_extractor.py`
- Extrae datos de PostgreSQL con filtros incrementales
- Maneja tipos de datos especiales (timestamps, arrays)

#### `table_inspector.py`
- Inspecciona estructura de tablas
- Obtiene lista de columnas y tipos de datos
- Detecta claves primarias

---

### 5. **`etl/control/control_manager.py`** - Gestor de Estado
**Qué hace**: Mantiene seguimiento del estado de extracciones.

**Funcionalidades**:
- Lee/escribe `.etl_state.json` con posición de lectura por tabla
- Permite **retomar desde donde se paró** si falla el sistema
- Estructura:
```json
{
  "sensor_readings": {
    "last_extracted_id": 12450,
    "last_timestamp": "2024-12-04T10:30:45",
    "total_records": 50000
  }
}
```

---

### 6. **`notebooks/templates/limpieza_template.ipynb`** - Procesamiento Silver
**Qué hace**: Limpia y prepara datos para análisis (capa Silver).

**Pasos ejecutados**:
1. **Inicializa SparkSession** local con 4 threads
2. **Lee archivo más reciente** de `meteo-bronze` desde MinIO
3. **Elimina columnas innecesarias**: presión, UV, PM2.5, lluvia, viento, vibración
4. **Elimina duplicados**: `dropDuplicates()`
5. **Descompone timestamps** en:
   - año, mes, día, hora, minuto, segundo
6. **Convierte timestamps a string** para evitar problemas con pandas
7. **Genera dos archivos CSV** en `meteo-silver`:
   - `{tabla_nombre}_silver.csv` → Específico por tabla
   - `datos_principales_silver.csv` → Estándar para Power BI

**Archivos generados**:
```
meteo-silver/
├── sensor_readings_silver.csv      (datos específicos)
└── datos_principales_silver.csv    (estándar Power BI)
```

---

### 7. **`notebooks/templates/generacion_KPI.ipynb`** - Generación de KPIs (Gold)
**Qué hace**: Calcula métricas agregadas y KPIs para análisis (capa Gold).

**KPIs Generados**:

#### **KPI 1: Disponibilidad y Calidad de Datos**
- Disponibilidad de sensores: % de registros con temperatura válida
- Calidad de datos: % de registros con humedad válida
- Total de registros: Cantidad de observaciones

#### **KPI 2: Estabilidad Climática**
- **Temperatura**:
  - Promedio: Media de todas las lecturas
  - Máxima: Valor más alto
  - Mínima: Valor más bajo
  - Rango: Diferencia máx-mín
- **Humedad**:
  - Promedio, máxima, mínima, rango
  - Desviación estándar (variabilidad)

#### **KPI 3: Detección de Anomalías**
- Temperaturas fuera de rango (0-50°C)
- Humedades inválidas (0-100%)
- Riesgo de condensación (T<5°C + H>85%)

#### **KPI 4: Condiciones Operativas**
- **Óptimas**: 15-28°C y 40-70% humedad
- **Alerta**: Rangos intermedios
- **Crítica**: Valores extremos
- Porcentaje de registros en cada categoría

**Archivos generados**:
```
meteo-gold/
└── metricas_kpi_gold.csv
    (tabla con todas las métricas calculadas)
```

---

### 8. **`etl/managers/`** - Gestores de Capas
**`gold_manager.py`**: Gestiona versiones en capa Gold
- Hereda de `LayerManager`
- Limpia versiones antiguas automáticamente
- Mantiene solo la versión más reciente

**`silver_manager.py`**: Gestiona versiones en capa Silver
- Limpia versiones antiguas automáticamente

**`layer_manager.py`**: Gestor base
- Listar objetos por tabla
- Obtener versión más reciente
- Eliminar versiones antiguas
- Calcular estadísticas (tamaño total, número de versiones)

---

### 9. **`config/`** - Configuración
**`database_config.py`**: Conexión a PostgreSQL
- Host, puerto, BD, usuario, contraseña
- Construye URL de conexión SQLAlchemy
- Lee variables de entorno

**`minio_config.py`**: Conexión a MinIO
- Endpoint, access key, secret key
- Configuración de buckets
- Lee variables de entorno

---

### 10. **`etl/uploaders/minio_uploader.py`** - Carga a MinIO
**Qué hace**: Sube archivos a MinIO de forma segura.

**Funcionalidades**:
- Crea buckets si no existen
- Sube archivos CSV con metadatos
- Maneja errores de conectividad
- Registra cada operación

---

### 11. **`etl/writers/`** - Escritores de Archivos
**`csv_writer.py`**: Escribe DataFrames a CSV
- Maneja encoding UTF-8
- Preserva tipos de datos
- Gestiona rutas temporales

**`file_writer.py`**: Clase base abstracta para escritores

---

## 📊 Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────┐
│                         CICLO COMPLETO                          │
└─────────────────────────────────────────────────────────────────┘

1. EXTRACCIÓN (main.py → pipeline.py)
   ├─ Lee .etl_state.json (última posición)
   ├─ Conecta a PostgreSQL
   ├─ Inspecciona tabla sensor_readings
   ├─ Extrae registros con id > last_id
   ├─ Genera sensor_readings_bronce_{timestamp}.csv
   └─ Sube a meteo-bronze en MinIO

2. LIMPIEZA (limpieza_template.ipynb)
   ├─ Inicia SparkSession
   ├─ Lee archivo más reciente de meteo-bronze
   ├─ Elimina columnas innecesarias
   ├─ Elimina duplicados
   ├─ Descompone timestamps
   ├─ Genera datos_principales_silver.csv
   └─ Sube a meteo-silver en MinIO

3. KPIs (generacion_KPI.ipynb)
   ├─ Inicia SparkSession
   ├─ Lee datos_principales_silver.csv
   ├─ Calcula 4 grupos de KPIs
   ├─ Genera metricas_kpi_gold.csv
   └─ Sube a meteo-gold en MinIO

4. DESCARGA (main.py)
   ├─ Conecta a MinIO
   ├─ Descarga datos_principales_silver.csv → file/
   ├─ Descarga metricas_kpi_gold.csv → file/
   └─ Archivos listos para Power BI

5. ESPERA
   └─ Pausa 300 segundos (5 minutos)
   └─ Repite desde paso 1

```

---

## 💾 Archivos Generados

### En **MinIO**:
```
meteo-bronze/
└── sensor_readings_bronce_2024-12-04_10-30-45.csv

meteo-silver/
├── sensor_readings_silver.csv
└── datos_principales_silver.csv

meteo-gold/
└── metricas_kpi_gold.csv
```

### En **Carpeta `file/`** (para Power BI):
```
file/
├── datos_principales_silver.csv    (datos limpios)
└── metricas_kpi_gold.csv           (KPIs)
```

---

## 🚀 Instalación

### Requisitos
- Python 3.8+
- PostgreSQL (con tabla `sensor_readings`)
- MinIO (S3-compatible storage)
- Java 11+ (para PySpark)
- PySpark 3.3+

### Pasos

1. **Clonar repositorio**
```bash
git clone https://github.com/andrews0212/Estacion_Meteorologica.git
cd Estacion_Meteorologica
```

2. **Crear entorno virtual**
```bash
python -m venv venv_meteo
# En Windows:
.\venv_meteo\Scripts\Activate.ps1
# En Linux/Mac:
source venv_meteo/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno** (`.env` o en el sistema):
```bash
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=meteorologia
DB_USER=postgres
DB_PASSWORD=tu_contraseña

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

5. **Crear tabla en PostgreSQL** (si no existe):
```sql
CREATE TABLE sensor_readings (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    temperatura NUMERIC(5,2),
    humedad NUMERIC(5,2),
    velocidad_viento NUMERIC(5,2),
    presion NUMERIC(7,2),
    nivel_uv INTEGER,
    pm25 NUMERIC(7,2),
    lluvia NUMERIC(7,2),
    vibracion NUMERIC(5,2)
);
```

6. **Crear buckets en MinIO**:
```bash
mc mb minio/meteo-bronze
mc mb minio/meteo-silver
mc mb minio/meteo-gold
```

---

## ▶️ Ejecución

### Modo Normal (Pipeline Continuo)
```bash
python main.py
```
Ejecuta ciclos cada 5 minutos indefinidamente.

### Modo Simulación (Insertar Datos de Prueba)
```bash
# 1000 registros aleatorios
python main.py simulate

# N registros personalizados
python main.py simulate 5000
```

### Ejecutar con PowerShell (Windows)
```powershell
.\run_scheduler.ps1
```

### Con Scheduler (Windows Task Scheduler)
Se incluye `scriptDB.py` que puede programarse como tarea.

---

## 📁 Estructura de Archivos

```
Estacion_Meteorologica/
├── main.py                          [Orquestador principal]
├── scriptDB.py                      [Script para BD]
├── run_scheduler.ps1                [Script PowerShell]
├── README.md                        [Este archivo]
├── requirements-docs.txt            [Dependencias]
├── requirements.txt                 [Dependencias Python]
│
├── config/                          [Configuración]
│   ├── __init__.py
│   ├── database_config.py          [PostgreSQL]
│   └── minio_config.py             [MinIO]
│
├── etl/                             [Pipeline ETL]
│   ├── __init__.py
│   ├── pipeline.py                 [Coordina extracción]
│   ├── table_processor.py           [Procesa tablas]
│   ├── notebook_executor.py         [Ejecuta notebooks]
│   ├── etl_state.py               [Gestiona estado]
│   │
│   ├── control/                    [Gestión de estado]
│   │   ├── __init__.py
│   │   └── control_manager.py      [Persiste posición]
│   │
│   ├── extractors/                 [Extracción de datos]
│   │   ├── __init__.py
│   │   ├── data_extractor.py      [Extrae de PostgreSQL]
│   │   └── table_inspector.py     [Inspecciona tablas]
│   │
│   ├── managers/                   [Gestión de capas]
│   │   ├── __init__.py
│   │   ├── layer_manager.py       [Gestor base]
│   │   ├── gold_manager.py        [Capa Gold]
│   │   └── silver_manager.py      [Capa Silver]
│   │
│   ├── uploaders/                  [Carga a MinIO]
│   │   ├── __init__.py
│   │   └── minio_uploader.py      [Sube archivos]
│   │
│   ├── utils/                      [Funciones auxiliares]
│   │   ├── __init__.py
│   │   ├── db_utils.py            [Utilidades BD]
│   │   └── minio_utils.py         [Utilidades MinIO]
│   │
│   └── writers/                    [Escritura de archivos]
│       ├── __init__.py
│       ├── csv_writer.py          [Escribe CSV]
│       └── file_writer.py         [Clase base]
│
├── notebooks/                       [Notebooks PySpark]
│   └── templates/
│       ├── limpieza_template.ipynb     [→ Capa Silver]
│       └── generacion_KPI.ipynb        [→ Capa Gold]
│
├── file/                            [Archivos para Power BI]
│   ├── datos_principales_silver.csv
│   └── metricas_kpi_gold.csv
│
├── venv_meteo/                      [Entorno virtual]
│   └── ...
│
└── .etl_state.json                  [Estado de extracciones]
    (se crea automáticamente)
```

---

## 🔧 Configuración Detallada

### Variables de Entorno Soportadas

```bash
# PostgreSQL
DB_HOST                # Host de BD (default: localhost)
DB_PORT                # Puerto (default: 5432)
DB_NAME                # Nombre de BD
DB_USER                # Usuario
DB_PASSWORD            # Contraseña

# MinIO
MINIO_ENDPOINT         # IP:puerto (default: localhost:9000)
MINIO_ACCESS_KEY       # Access key (default: minioadmin)
MINIO_SECRET_KEY       # Secret key (default: minioadmin)
MINIO_BUCKET           # Bucket de bronce (default: meteo-bronze)
```

### Parámetros en `main.py`

```python
# Intervalo de extracción (segundos)
extraction_interval = 300

# Rutas a notebooks
notebook_path = "notebooks/templates/limpieza_template.ipynb"
notebook_kpi_path = "notebooks/templates/generacion_KPI.ipynb"

# Timeout para ejecución de notebooks (segundos)
timeout = 600
```

---

## 📊 Monitoreo y Logs

El sistema imprime información en tiempo real:

```
[INFO] Conectando a PostgreSQL: postgresql://user:***@localhost/meteo
[OK] Tabla 'sensor_readings' encontrada
[INFO] Extrayendo desde id 100...
[OK] 1250 registros nuevos
[OK] sensor_readings_bronce_2024-12-04_10-30-45.csv subido
[INFO] Descargando archivos para Power BI...
[OK] datos_principales_silver.csv descargado
[OK] metricas_kpi_gold.csv descargado
[INFO] Esperando 300s...
```

---

## 🐛 Solución de Problemas

| Problema | Causa | Solución |
|----------|-------|----------|
| Connection refused PostgreSQL | BD no corre | `service postgresql start` o verificar variables de entorno |
| Connection refused MinIO | MinIO no corre | `minio server /minio/data` |
| Java not found | PySpark sin Java | Instalar Java 11+, agregar JAVA_HOME |
| Encoding error UTF-8 | Windows encoding | `set PYTHONIOENCODING=utf-8` o ejecutar como admin |
| Archivo no encontrado en minIO | Bucket no existe | `mc mb minio/meteo-bronze` |
| Notebook timeout | Datos muy grandes | Aumentar `timeout=600` en main.py |

---

## 📈 Casos de Uso

### 1. **Monitoreo en Tiempo Real**
- Dashboards Power BI actualizados cada 5 minutos
- KPIs de temperatura y humedad
- Alertas de anomalías

### 2. **Análisis Histórico**
- Datos limpios en capa Silver
- Acceso a histórico completo en MinIO
- Queries con PySpark/SQL

### 3. **Detección de Patrones**
- Tendencias de temperatura/humedad
- Ciclos diarios/semanales
- Correlaciones entre variables

### 4. **Alertas Automáticas**
- Detecta temperaturas críticas (< 5°C o > 35°C)
- Detecta humedades críticas (< 30% o > 80%)
- Detecta riesgo de condensación

---

## 📝 Licencia

MIT License - Ver archivo LICENSE para detalles.

---

## 👤 Autor

**Andrews0212**
- GitHub: https://github.com/andrews0212
- Repositorio: https://github.com/andrews0212/Estacion_Meteorologica

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/mi-mejora`)
3. Commit cambios (`git commit -m "Agregué..."`)
4. Push a la rama (`git push origin feature/mi-mejora`)
5. Abre un Pull Request

---

**Última actualización**: Diciembre 4, 2024
