# 📊 Pipeline ETL - Guía de Uso Completa

## Descripción General

El pipeline ETL completo automatiza:
1. **Extracción** desde PostgreSQL → MinIO (Bronze layer)
2. **Limpieza** de datos → MinIO (Silver layer)
3. **Generación de KPIs** → MinIO (Gold layer)
4. **Descarga automática** para Power BI → `file/metricas_kpi_gold.csv`

## Flujo de Ejecución

```
PostgreSQL → main.py → Bronze (MinIO)
                    ↓
            Silver layer script → Silver (MinIO)
                    ↓
            Gold layer script → Gold (MinIO)
                    ↓
            Descarga automática → file/metricas_kpi_gold.csv
```

## Instrucciones de Uso

### 1️⃣ Ejecutar Pipeline Principal (Recomendado)

```bash
cd c:\Users\Alumno_AI\Desktop\Estacion_Meteorologica
venv_meteo\Scripts\Activate.ps1
python main.py
```

**Qué hace:**
- Ciclos continuos cada 5 minutos (configurables)
- Cada ciclo:
  - Extrae datos nuevos de PostgreSQL
  - Limpia datos (Silver)
  - Genera 5 KPIs (Gold)
  - **✨ Descarga automáticamente Gold CSV a `file/` para Power BI**

**Salida esperada:**
```
================================================================================
INICIANDO SISTEMA ETL + LIMPIEZA AUTOMATICA
================================================================================
...
[OK] Intervalo de extracción: 300s

--- CICLO 1: 2025-12-03 13:55:00 ---
[OK] Extracción completada
[OK] Silver layer ejecutado exitosamente
[OK] Gold layer ejecutado exitosamente
[INFO] Descargando Gold CSV para Power BI...
[OK] Gold CSV descargado a: C:\...\Estacion_Meteorologica\file\metricas_kpi_gold.csv

[INFO] Esperando 300s...
```

**Para detener:** Presionar `Ctrl+C`

---

### 2️⃣ Descargar Gold Manualmente

```bash
python descargar_gold.py
```

**Qué hace:**
- Descarga el archivo `metricas_kpi_gold.csv` desde MinIO
- Lo guarda en `file/metricas_kpi_gold.csv`
- Muestra información del archivo y primeras líneas

---

### 3️⃣ Monitorear Cambios en Tiempo Real

```bash
python monitor_powerbi.py
```

**Opciones:**
```bash
# Verificar cada 10 segundos (default)
python monitor_powerbi.py

# Verificar cada 5 segundos
python monitor_powerbi.py --interval 5

# Monitorear durante 300 segundos (5 minutos)
python monitor_powerbi.py --duration 300

# Combinación: cada 5 segundos durante 10 minutos
python monitor_powerbi.py --interval 5 --duration 600
```

**Salida esperada:**
```
================================================================================
🔍 MONITOR DE ACTUALIZACIONES GOLD PARA POWER BI
================================================================================
📍 Archivo: C:\...\Estacion_Meteorologica\file\metricas_kpi_gold.csv
⏱️  Intervalo: 10s
================================================================================

[2025-12-03 13:55:00] Verificación #1... ✅ | Tamaño: 3653 bytes | Registros: 97 | Modificado: 13:55:00
[2025-12-03 13:55:10] Verificación #2... ✅ | Tamaño: 3653 bytes | Registros: 97 | Modificado: 13:55:00
[2025-12-03 14:00:00] Verificación #31... 🔄 ACTUALIZADO | Tamaño: 3720 bytes | Registros: 100 | Modificado: 14:00:00
```

---

## Estructura del Archivo Gold (Power BI)

**Ubicación:** `file/metricas_kpi_gold.csv`

**Columnas:**
| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| `id` | ID del sensor | 1 |
| `lecturas` | Cantidad de lecturas | 97 |
| `temp_avg` | Temperatura promedio (°C) | 25.0 |
| `temp_max` | Temperatura máxima (°C) | 28.5 |
| `temp_min` | Temperatura mínima (°C) | 22.1 |
| `temp_std` | Desviación estándar (temperatura) | 1.23 |
| `hum_avg` | Humedad promedio (%) | 45.2 |
| `hum_max` | Humedad máxima (%) | 65.0 |
| `hum_min` | Humedad mínima (%) | 30.5 |

**Ejemplo de datos:**
```
id,lecturas,temp_avg,temp_max,temp_min,temp_std,hum_avg,hum_max,hum_min
1,97,25.4,28.5,22.1,1.23,45.2,65.0,30.5
2,97,24.8,27.2,21.9,1.15,46.1,64.5,31.2
3,97,25.1,28.0,22.5,1.18,44.9,63.8,32.0
```

---

## Integración con Power BI

### Pasos para importar el CSV en Power BI:

1. **Abrir Power BI Desktop**
2. **Home → Get Data → Text/CSV**
3. **Seleccionar:** `C:\...\Estacion_Meteorologica\file\metricas_kpi_gold.csv`
4. **Load o Transform Data según necesites**
5. **Crear visualizaciones** con las métricas KPI

### ✨ Ventaja: Actualización Automática

Ahora cada vez que el pipeline ejecuta un ciclo:
- Los KPIs se recalculan
- El archivo CSV en `file/` se actualiza automáticamente
- **Power BI puede actualizar el dataset automáticamente** (si configuras refresh programado)

---

## MinIO - Capas de Almacenamiento

### Bronze Layer
**Bucket:** `meteo-bronze`
- Datos RAW sin procesar
- Descargados directamente de PostgreSQL
- Archivos CSV con 12 columnas originales

### Silver Layer
**Bucket:** `meteo-silver`
- Datos limpios y depurados
- 5 columnas principales: `id, temperature, humidity, timestamp, ip`
- Archivo: `sensor_readings_silver.csv`

### Gold Layer
**Bucket:** `meteo-gold`
- **KPIs y métricas agregadas**
- Preparado para análisis en Power BI
- Archivo: `metricas_kpi_gold.csv`
- **Se descarga automáticamente a `file/` en cada ciclo**

---

## Configuración Avanzada

### Cambiar intervalo entre ciclos

Edita `main.py`:
```python
# Por defecto: 300 segundos (5 minutos)
system = ETLSystem(extraction_interval=300)

# Cambiar a 60 segundos (1 minuto)
system = ETLSystem(extraction_interval=60)
```

### Cambiar credenciales MinIO

Edita `config/minio_config.py`:
```python
self.endpoint = "localhost:9000"  # Dirección del servidor
self.access_key = "minioadmin"     # Usuario
self.secret_key = "minioadmin"     # Contraseña
self.secure = False                # SSL/TLS
```

---

## Troubleshooting

### ❌ Error: "No se puede conectar a MinIO"
```
Verificar:
1. MinIO está corriendo en localhost:9000
2. Credenciales correctas en config/minio_config.py
3. Buckets creados: meteo-bronze, meteo-silver, meteo-gold
```

### ❌ Error: "Tabla no existe en PostgreSQL"
```
Verificar:
1. Base de datos contiene tabla 'lecturas_sensor'
2. Credenciales en config/database_config.py
3. Conexión a BD abierta
```

### ❌ Error: "Archivo no se descarga a file/"
```
Verificar:
1. Carpeta file/ existe (se crea automáticamente)
2. Permisos de escritura en el directorio
3. MinIO tiene el archivo metricas_kpi_gold.csv
```

### ❌ Error: "PySpark no encontrado"
```
Solución:
pip install pyspark==3.4.1
```

---

## Resumen de Archivos Principales

| Archivo | Propósito |
|---------|-----------|
| `main.py` | **🚀 Punto de entrada - ejecuta pipeline completo** |
| `descargar_gold.py` | Descarga manual de Gold CSV |
| `monitor_powerbi.py` | Monitorea cambios en tiempo real |
| `etl/scripts/silver_layer.py` | Script de limpieza (Silver) |
| `etl/scripts/gold_layer.py` | Script de generación KPIs (Gold) |
| `notebooks/templates/limpieza_template.ipynb` | Notebook PySpark (Silver) |
| `notebooks/templates/generacion_KPI.ipynb` | Notebook PySpark (Gold) |

---

## 📈 Próximos Pasos

1. ✅ Ejecutar `main.py` para iniciar pipeline continuo
2. ✅ Monitorear con `monitor_powerbi.py` mientras se ejecuta
3. ✅ Abrir Power BI e importar `file/metricas_kpi_gold.csv`
4. ✅ Crear dashboards con los KPIs
5. ✅ (Opcional) Configurar refresh automático en Power BI

---

**Estado:** ✅ Pipeline completo operacional
**Última actualización:** 2025-12-03
