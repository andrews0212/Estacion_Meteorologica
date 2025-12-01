# 🌤️ Sistema ETL Incremental PostgreSQL → MinIO

Sistema automatizado de extracción, transformación y carga (ETL) que extrae **solo datos nuevos** de PostgreSQL y los almacena en formato Parquet en MinIO (capa Bronce de un Data Lake).

## 📋 Descripción General

Este proyecto implementa un pipeline ETL incremental que:
- ✅ Extrae **solo registros nuevos** de todas las tablas de PostgreSQL
- ✅ Detecta automáticamente **Primary Keys** o columnas de rastreo (timestamps o IDs incrementales)
- ✅ **Valida datos nuevos** antes de procesar (compara último valor vs máximo actual)
- ✅ Guarda datos en formato **Parquet comprimido**
- ✅ Sube archivos a **MinIO** (almacenamiento objeto compatible S3)
- ✅ Mantiene un **control de estado** para evitar duplicados
- ✅ Ejecuta automáticamente cada 10 segundos (configurable)

---

## 🏗️ Arquitectura

```
PostgreSQL (Origen)
    ↓
[procces_data.py] → Extracción incremental
    ↓
Archivos Parquet (/tmp)
    ↓
MinIO (Capa Bronce)
    ↓
meteo-bronze/tabla_nombre/tabla_TIMESTAMP.parquet
```

---

## 📁 Estructura del Proyecto

```
pruebaMeteorologica/
├── procces_data.py        # Script principal de ETL
├── run_scheduler.sh       # Scheduler para ejecución automática
├── venv_meteo/            # Entorno virtual Python
└── README.md              # Este archivo
```

---

## 🔧 Componentes

### 1️⃣ `procces_data.py` - Script ETL Principal

#### **Funcionalidades principales:**

##### 📌 `initialize_control_table(connection)`
Crea la tabla `etl_control` en PostgreSQL para rastrear el estado de cada tabla procesada.

**Estructura de `etl_control`:**
```sql
CREATE TABLE etl_control (
    table_name VARCHAR(255) PRIMARY KEY,     -- Nombre de la tabla
    last_extracted_value VARCHAR(255),       -- Último valor procesado (timestamp o ID)
    last_extracted_at TIMESTAMP,             -- Fecha de última extracción
    tracking_column VARCHAR(255)             -- Columna usada para rastreo
)
```

##### 📌 `detect_tracking_column(connection, table_name)`
Detecta automáticamente la mejor columna para rastrear cambios incrementales.

**Prioridad de detección:**
1. **Columnas de timestamp:** `created_at`, `updated_at`, `timestamp`, `fecha_registro`, `last_update`, `release_date`
2. **Primary Key real de la base de datos** (consulta metadatos de PostgreSQL - método más confiable)
3. **Columnas con nombre 'id'** (de tipo INTEGER, SERIAL o NUMERIC)

**Retorna:** `(nombre_columna, tipo)` donde tipo es `'timestamp'` o `'id'`

**Ventaja:** Al usar la PRIMARY KEY real, garantiza que se detecten correctamente IDs como `movie_id`, `person_id`, etc.

##### 📌 `get_last_extracted_value(connection, table_name)`
Consulta el último valor extraído de una tabla desde `etl_control`.

**Retorna:** `(último_valor, columna_rastreo)` o `(None, None)` si es la primera extracción.

##### 📌 `update_last_extracted_value(connection, table_name, value, tracking_column)`
Actualiza o inserta el último valor procesado en `etl_control` usando `UPSERT` (INSERT ... ON CONFLICT).

##### 📌 `get_max_value_in_table(connection, table_name, tracking_column)`
Obtiene el valor máximo actual en la tabla para la columna de rastreo.

**Uso:** Compara el último valor procesado con el máximo actual para evitar extracciones innecesarias.

##### 📌 `process_batch()`
Función principal que orquesta todo el proceso ETL.

**Flujo de ejecución mejorado:**

1. **Inicialización:**
   - Crea tabla `etl_control` si no existe
   - Obtiene lista de todas las tablas de PostgreSQL (excluyendo `etl_control`)

2. **Por cada tabla:**
   ```python
   # 1. Detectar columna de rastreo (prioriza PRIMARY KEY)
   tracking_column, tracking_type = detect_tracking_column(connection, table_name)
   
   # 2. Si no hay columna de rastreo, SALTAMOS la tabla (evita cargas completas repetidas)
   if not tracking_column:
       print("⚠️ SKIPPING: No se detectó columna incremental")
       continue
   
   # 3. Obtener último valor procesado
   last_value, stored_column = get_last_extracted_value(connection, table_name)
   
   # 4. Verificar si hay datos nuevos (optimización clave)
   max_value_in_table = get_max_value_in_table(connection, table_name, tracking_column)
   if last_value >= max_value_in_table:
       print("✓ No hay datos nuevos")
       continue
   
   # 5. Construir query incremental
   if last_value:
       query = f"SELECT * FROM {table_name} WHERE {tracking_column} > :val"
   else:
       query = f"SELECT * FROM {table_name}"  # Primera carga
   ```

3. **Procesamiento:**
   - Si `df.empty`: No hay datos nuevos → **no crea archivo, no gasta recursos**
   - Si hay datos: Guarda en Parquet y sube a MinIO

4. **Actualización de control:**
   - Calcula el valor máximo de la columna de rastreo: `df[tracking_column].max()`
   - Actualiza `etl_control` **solo si la carga a MinIO fue exitosa**

5. **Resumen final:**
   - Muestra total de registros nuevos procesados en el batch

---

### 2️⃣ `run_scheduler.sh` - Scheduler de Ejecución

Script Bash que ejecuta el ETL de forma continua en intervalos regulares.

#### **Configuración:**

```bash
# --- POSTGRESQL ---
export PG_DB="cine"                    # Nombre de la base de datos
export PG_USER="postgres"              # Usuario PostgreSQL
export PG_PASS="1234"                  # Contraseña
export PG_HOST="127.0.0.1"             # IP del servidor

# --- MINIO ---
export MINIO_ALIAS="mi_minio"          # Alias configurado con 'mc alias set'
export MINIO_BUCKET="meteo-bronze"     # Bucket de destino

# --- EJECUCIÓN ---
PYTHON_SCRIPT="procces_data.py"
PYTHON_VENV="venv_meteo/bin/python"
SLEEP_INTERVAL=10                      # 10 segundos (ajustable según necesidad)
```

#### **Flujo de ejecución:**

**Nota:** El script `procces_data.py` ahora incluye el bucle interno, por lo que puede ejecutarse directamente:

```python
# Dentro de procces_data.py
if __name__ == "__main__":
    while True:
        process_batch()
        print("Esperando 10 segundos...")
        time.sleep(10)
```

O mediante el script bash tradicional:

```bash
while true; do
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    echo "--- INICIO DE BATCH: $TIMESTAMP ---"
    
    # Ejecutar ETL con Python del entorno virtual
    $PYTHON_VENV $PYTHON_SCRIPT
    
    echo "--- FIN DE BATCH ---"
    echo "Esperando $SLEEP_INTERVAL segundos..."
    sleep $SLEEP_INTERVAL
done
```

**Características:**
- ✅ Bucle infinito con intervalo configurable (10 segundos por defecto)
- ✅ Usa el Python del entorno virtual
- ✅ Variables de entorno exportadas para `procces_data.py`
- ✅ Timestamps en cada ejecución
- ✅ Detener con `Ctrl+C`
- ✅ **Validación previa:** Verifica si hay datos nuevos antes de procesarlos

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

### **Ejecución manual única:**

```bash
source venv_meteo/bin/activate
python procces_data.py
```

### **Ejecución automática continua:**

```bash
./run_scheduler.sh
```

Esto ejecutará el ETL cada **5 minutos** indefinidamente. Para detener, presiona `Ctrl+C`.

### **Cambiar frecuencia de ejecución:**

Editar en `run_scheduler.sh`:

```bash
SLEEP_INTERVAL=60    # 1 minuto
SLEEP_INTERVAL=300   # 5 minutos (actual)
SLEEP_INTERVAL=900   # 15 minutos
SLEEP_INTERVAL=3600  # 1 hora
```

---

## 📊 Ejemplo de Ejecución

### **Primera ejecución:**

```
============================================================
Procesando tabla: peliculas
============================================================
🆕 Primera extracción de peliculas. Extrayendo todos los datos.
📦 Registros nuevos encontrados: 150
💾 Datos guardados localmente: /tmp/peliculas_20251201143025.parquet
✅ Cargado exitosamente a MinIO Bronce: mi_minio/meteo-bronze/peliculas/peliculas_20251201143025.parquet
🔄 Control actualizado. Nuevo último valor: 2025-12-01 14:30:25

============================================================
🎯 RESUMEN: 150 registros nuevos procesados en total
============================================================
```

### **Segunda ejecución (5 minutos después):**

```
============================================================
Procesando tabla: peliculas
============================================================
📊 Columna de rastreo: created_at
📅 Último valor procesado: 2025-12-01 14:30:25
📦 Registros nuevos encontrados: 12
💾 Datos guardados localmente: /tmp/peliculas_20251201143525.parquet
✅ Cargado exitosamente a MinIO Bronce: mi_minio/meteo-bronze/peliculas/peliculas_20251201143525.parquet
🔄 Control actualizado. Nuevo último valor: 2025-12-01 14:35:20

============================================================
🎯 RESUMEN: 12 registros nuevos procesados en total
============================================================
```

### **Tercera ejecución (sin datos nuevos):**

```
============================================================
Procesando tabla: peliculas
============================================================
📊 Columna de rastreo: created_at
📅 Último valor procesado: 2025-12-01 14:35:20
✓ No hay datos nuevos en peliculas.

============================================================
🎯 RESUMEN: 0 registros nuevos procesados en total
============================================================
```

---

## 📂 Estructura de Archivos en MinIO

```
meteo-bronze/
├── peliculas/
│   ├── peliculas_20251201143025.parquet  (150 registros - primera carga)
│   ├── peliculas_20251201143525.parquet  (12 registros - solo nuevos)
│   └── peliculas_20251201144025.parquet  (8 registros - solo nuevos)
├── actores/
│   ├── actores_20251201143025.parquet
│   └── actores_20251201143525.parquet
└── directores/
    └── directores_20251201143025.parquet
```

**Cada archivo Parquet contiene SOLO los registros nuevos** desde la última extracción.

---

## 🔍 Verificación de Datos

### **Ver archivos en MinIO:**

```bash
mc ls mi_minio/meteo-bronze/
mc ls mi_minio/meteo-bronze/peliculas/
```

### **Descargar archivo Parquet:**

```bash
mc cp mi_minio/meteo-bronze/peliculas/peliculas_20251201143025.parquet ./
```

### **Leer Parquet con Python:**

```python
import pandas as pd

df = pd.read_parquet('peliculas_20251201143025.parquet')
print(df.head())
print(f"Total registros: {len(df)}")
```

### **Consultar tabla de control en PostgreSQL:**

```sql
SELECT * FROM etl_control;
```

Resultado:
```
table_name  | last_extracted_value    | last_extracted_at       | tracking_column
------------|-------------------------|-------------------------|----------------
peliculas   | 2025-12-01 14:35:20     | 2025-12-01 14:35:30     | created_at
actores     | 2025-12-01 14:35:18     | 2025-12-01 14:35:30     | updated_at
directores  | 523                     | 2025-12-01 14:30:30     | id
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

Si tus tablas usan nombres personalizados, edita `detect_tracking_column()` en `procces_data.py`:

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

1. **Límite de seguridad:** Por defecto extrae máximo 10,000 filas por tabla por ejecución (ajustable en el código).

2. **Archivos incrementales:** Cada Parquet contiene SOLO datos nuevos. Para análisis, deberás unir todos los archivos de una tabla.

3. **Primera ejecución lenta:** La primera vez extrae todos los datos. Las siguientes solo incrementales.

4. **Tablas sin rastreo:** Si una tabla no tiene timestamp ni ID incremental, se extraen todos los datos en cada ejecución.

---

## 👤 Autor

Sistema desarrollado para procesamiento ETL incremental de datos meteorológicos con arquitectura Data Lake.

---

## 📄 Licencia

Este proyecto es de uso interno para procesamiento de datos.
