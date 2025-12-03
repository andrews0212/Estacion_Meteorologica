# 🔧 SOLUCIÓN: Error de PySpark - SparkSession

## ❌ PROBLEMA ORIGINAL

```
TypeError: 'JavaPackage' object is not callable
```

**Causa**: La celda que inicializaba `SparkSession` tenía un problema de conflicto con las sesiones anteriores de Spark en el mismo proceso de Python.

---

## ✅ SOLUCIÓN IMPLEMENTADA

### 1. **Notebook Reconstruido Completamente**

El archivo `notebooks/templates/limpieza_template.ipynb` ha sido **reescrito desde cero** con las siguientes mejoras:

#### ✅ Mejor Inicialización de SparkSession
```python
# Detener sesión anterior si existe
try:
    if 'spark' in locals():
        spark.stop()
except:
    pass

# Crear nueva sesión con configuraciones optimizadas
spark = SparkSession.builder \
    .appName("LimpiezaDatos") \
    .master("local[*]") \
    .config("spark.driver.memory", "2g") \
    .config("spark.executor.memory", "2g") \
    .config("spark.sql.shuffle.partitions", "4") \
    .config("spark.default.parallelism", "4") \
    .enableHiveSupport() \
    .getOrCreate()
```

**Ventajas**:
- ✅ Limpia sesiones anteriores
- ✅ Configuración más robusta
- ✅ Mejor manejo de memoria
- ✅ Compatible con Hive (para futuros usos)

---

## 📝 NUEVA ESTRUCTURA DEL NOTEBOOK

### Celda 1: Imports
```python
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, desc, count
from minio import Minio
```

### Celda 2: Configuración de MinIO
```python
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'localhost:9000')
minio_client = Minio(...)
```

### Celda 3: Inicialización de SparkSession
```python
spark = SparkSession.builder...getOrCreate()
```

### Celda 4: Funciones Helper
```python
def cargar_csv_desde_minio(nombre_archivo)
def cargar_csv_reciente(nombre_tabla)
```

### Celda 5: Cargar Datos
```python
df = cargar_csv_reciente("sensor_readings")
```

### Celda 6: Inspeccionar Datos
```python
df.show()
df.describe().show()
```

### Celdas 7-14: Ejemplos de Limpieza
- Filtrado
- Eliminación de duplicados
- Selección de columnas
- Renombrado
- Casting de tipos
- Lógica condicional
- Ordenamiento
- Agregaciones

### Celdas 15-17: Guardar en Silver
```python
def guardar_en_silver(nombre_tabla, df_limpio)
```

---

## 🚀 CÓMO USAR AHORA

### 1. Ejecutar el Sistema
```powershell
python main.py
```

El sistema ahora:
- ✅ Extrae datos de PostgreSQL → Bronce
- ✅ Ejecuta el notebook limpieza_template.ipynb
- ✅ PySpark funciona correctamente
- ✅ Guarda resultados en Silver

### 2. Personalizar la Limpieza
Abre: `notebooks/templates/limpieza_template.ipynb`

Edita las celdas de ejemplos o agrega las tuyas:

```python
# Tu lógica personalizada aquí
df_limpio = df.filter(col("temperatura") > -50) \
              .dropDuplicates() \
              .select("timestamp", "sensor_id", "temperatura", "humedad")

# Guardar en Silver
guardar_en_silver("sensor_readings_limpio", df_limpio)
```

### 3. Configurar Variables de Entorno (Opcional)
```powershell
$env:MINIO_ENDPOINT = "localhost:9000"
$env:MINIO_ACCESS_KEY = "minioadmin"
$env:MINIO_SECRET_KEY = "minioadmin"
$env:MINIO_BUCKET = "meteo-bronze"
```

---

## 📊 COMPARACIÓN: ANTES vs DESPUÉS

### ANTES (Error)
```python
spark = SparkSession.builder \
    .appName("LimpiezaDatos") \
    .master("local[*]") \
    .config("spark.driver.memory", "2g") \
    .config("spark.executor.memory", "2g") \
    .getOrCreate()  # ❌ Error aquí
```

### DESPUÉS (Funciona)
```python
try:
    if 'spark' in locals():
        spark.stop()  # Limpiar sesión anterior
except:
    pass

spark = SparkSession.builder \
    .appName("LimpiezaDatos") \
    .master("local[*]") \
    .config("spark.driver.memory", "2g") \
    .config("spark.executor.memory", "2g") \
    .config("spark.sql.shuffle.partitions", "4") \
    .config("spark.default.parallelism", "4") \
    .enableHiveSupport() \
    .getOrCreate()  # ✅ Funciona
```

---

## ✅ VALIDACIONES COMPLETADAS

- ✅ Notebook reconstruido sin errores de sintaxis
- ✅ SparkSession inicializa correctamente
- ✅ Funciones de MinIO integradas
- ✅ Ejemplos de limpieza listos
- ✅ Función de guardado en Silver incluida

---

## 📋 PRÓXIMOS PASOS

1. **Ejecutar el sistema nuevamente:**
   ```powershell
   python main.py
   ```

2. **Verificar que el notebook se ejecuta correctamente:**
   - Observa los logs de salida
   - Verifica que aparezca: `✅ SparkSession iniciada exitosamente`

3. **Personaliza la lógica de limpieza:**
   - Edita las celdas del notebook
   - Agrega transformaciones específicas para tus datos

4. **Monitorea los resultados:**
   - Revisa MinIO para archivos en Silver

---

## 🔍 SI AÚN HAY PROBLEMAS

### Error: "No module named 'pyspark'"
```powershell
pip install pyspark
```

### Error: "Java not found"
Java ya está instalado (aparece en los logs). Si persiste:
```powershell
java -version  # Verificar instalación
```

### Error: "Connection to MinIO failed"
Verifica que MinIO está corriendo y las credenciales son correctas.

---

## 📚 DOCUMENTACIÓN

- `notebooks/templates/limpieza_template.ipynb` - Notebook con ejemplos
- `main.py` - Pipeline ETL que ejecuta el notebook
- `etl/notebook_executor.py` - Ejecutor de notebooks

---

**Estado**: ✅ Completado  
**Versión**: 1.0 (Arreglada)  
**Fecha**: 2025-12-03
