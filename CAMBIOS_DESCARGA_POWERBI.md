# ✅ Actualización Completada: Descarga Automática Gold para Power BI

## Resumen de Cambios

Se ha actualizado el pipeline ETL para que en **cada ciclo** descargue automáticamente el archivo Gold desde MinIO a la carpeta local `file/` para análisis en tiempo real en Power BI.

---

## 📝 Cambios Realizados

### 1. **main.py** - Pipeline Principal
- ✅ Agregada importación de `Minio` client
- ✅ Agregada importación de `Path` para manejo de directorios
- ✅ Actualizado método `run_cycle()` para incluir descarga
- ✅ Nuevo método `_download_gold_for_powerbi()` que:
  - Conecta a MinIO
  - Crea carpeta `file/` si no existe
  - Descarga `metricas_kpi_gold.csv` desde bucket `meteo-gold`
  - Confirma la descarga con mensaje

### 2. **config/minio_config.py** - Configuración MinIO
- ✅ Agregado atributo `secure` (por defecto: False)
- ✅ Configurable vía variable de entorno `MINIO_SECURE`

### 3. **Nuevos Scripts de Utilidad**

#### `monitor_powerbi.py` - Monitor en Tiempo Real
```bash
python monitor_powerbi.py [--interval 10] [--duration 0]
```
- Verifica cambios en `file/metricas_kpi_gold.csv`
- Muestra: tamaño, cantidad de registros, timestamp de actualización
- Detecta automáticamente cuándo el archivo fue actualizado (🔄 ACTUALIZADO)

**Ejemplo de salida:**
```
[2025-12-03 13:55:00] Verificación #1... ✅ | Tamaño: 3653 bytes | Registros: 97
[2025-12-03 14:00:00] Verificación #31... 🔄 ACTUALIZADO | Tamaño: 3720 bytes | Registros: 100
```

#### `test_pipeline.py` - Test del Pipeline
```bash
python test_pipeline.py [-c 3] [-i 5] [-q]
```
- Ejecuta N ciclos del pipeline
- Valida cada etapa (extracción, limpieza, KPI, descarga)
- Resumen de éxito/fallos
- Instrucciones para importar en Power BI

### 4. **descargar_gold.py** - Descarga Manual
- Script mejorado para descargar archivos Gold manualmente
- Parámetro personalizable `destination` (por defecto: `file`)

### 5. **GUIA_PIPELINE_POWERBI.md** - Documentación Completa
- Instrucciones paso a paso para usar el pipeline
- Estructura del archivo CSV (columnas y tipos)
- Pasos para importar en Power BI
- Troubleshooting y configuración avanzada

---

## 🚀 Cómo Usar

### Opción 1: Pipeline Principal (RECOMENDADO)
```bash
cd c:\Users\Alumno_AI\Desktop\Estacion_Meteorologica
venv_meteo\Scripts\Activate.ps1
python main.py
```
**Resultado:** Ciclos continuos cada 5 minutos con descarga automática

### Opción 2: Test (Para validación)
```bash
python test_pipeline.py -c 3 -i 5
```
**Resultado:** 3 ciclos con 5 segundos entre ellos

### Opción 3: Monitoreo en Tiempo Real
```bash
python monitor_powerbi.py --interval 5 --duration 300
```
**Resultado:** Verifica archivo cada 5 segundos durante 5 minutos

### Opción 4: Descarga Manual
```bash
python descargar_gold.py
```
**Resultado:** Descarga única del archivo Gold

---

## 📊 Flujo Completo Actual

```
┌─────────────────────────────────────────────────────────────┐
│              CICLO ETL (cada 5 minutos)                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
    ┌────────────────────────────────────────────────┐
    │ 1. Extracción: PostgreSQL → Bronze (MinIO)   │
    │    - Tabla: sensor_readings                   │
    │    - Modo: Incremental (timestamp)            │
    └────────────────────────────────────────────────┘
                           ↓
    ┌────────────────────────────────────────────────┐
    │ 2. Limpieza: Bronze → Silver (MinIO)          │
    │    - Elimina columnas innecesarias             │
    │    - Remueve duplicados                        │
    │    - Archivo: sensor_readings_silver.csv       │
    └────────────────────────────────────────────────┘
                           ↓
    ┌────────────────────────────────────────────────┐
    │ 3. KPIs: Silver → Gold (MinIO)                │
    │    - 5 métricas por sensor                     │
    │    - Archivo: metricas_kpi_gold.csv            │
    └────────────────────────────────────────────────┘
                           ↓
    ┌────────────────────────────────────────────────┐
    │ ✨ 4. DESCARGA: Gold → file/ (LOCAL)          │
    │    - Actualiza: file/metricas_kpi_gold.csv     │
    │    - Listo para Power BI en tiempo real        │
    └────────────────────────────────────────────────┘
                           ↓
    ┌────────────────────────────────────────────────┐
    │ 5. Análisis: Power BI (tu dashboard)          │
    │    - Importa file/metricas_kpi_gold.csv        │
    │    - Análisis en tiempo real de KPIs           │
    └────────────────────────────────────────────────┘
```

---

## 🎯 Ventajas de la Nueva Arquitectura

✅ **Automatización Completa**
- No necesitas descargar manualmente el archivo cada vez
- Se actualiza automáticamente en cada ciclo

✅ **Análisis en Tiempo Real**
- Power BI siempre tiene los últimos KPIs
- Puedes configurar refresh automático

✅ **Monitoreo Integrado**
- Script `monitor_powerbi.py` detecta cambios
- Sabrás exactamente cuándo se actualizó el archivo

✅ **Testing y Validación**
- Script `test_pipeline.py` valida todo el pipeline
- Resumen claro de éxitos/fallos

---

## 📁 Estructura de Archivos

```
Estacion_Meteorologica/
├── main.py                          ← 🚀 EJECUTA AQUÍ
├── test_pipeline.py                 ← Validar pipeline
├── monitor_powerbi.py               ← Monitorear cambios
├── descargar_gold.py                ← Descarga manual
├── GUIA_PIPELINE_POWERBI.md         ← Documentación completa
│
├── file/                            ← 📊 POWER BI AQUÍ
│   └── metricas_kpi_gold.csv        ← Se actualiza cada ciclo
│
├── config/
│   ├── database_config.py
│   └── minio_config.py              ← Agregado: .secure
│
└── etl/
    ├── scripts/
    │   ├── silver_layer.py
    │   └── gold_layer.py
    └── notebooks/
        └── templates/
            ├── limpieza_template.ipynb
            └── generacion_KPI.ipynb
```

---

## ⚙️ Configuración

### Intervalo entre ciclos
Editar `main.py` línea ~220:
```python
system = ETLSystem(extraction_interval=300)  # 300 segundos = 5 minutos
```

### Credenciales MinIO
Editar `config/minio_config.py`:
```python
self.endpoint = "localhost:9000"
self.access_key = "minioadmin"
self.secret_key = "minioadmin"
self.secure = False  # NUEVO
```

---

## ✨ Validación Rápida

```bash
# 1. Ejecutar un ciclo de prueba
python -c "from main import ETLSystem; system = ETLSystem(); system.run_cycle(1)"

# 2. Verificar que el archivo se descargó
Get-ChildItem file/metricas_kpi_gold.csv

# 3. Ver contenido
Get-Content file/metricas_kpi_gold.csv -First 6

# 4. Monitorear cambios
python monitor_powerbi.py --interval 5 --duration 60
```

---

## 🔍 Troubleshooting

**Error: MinIOConfig has no attribute 'secure'**
→ Actualiza `config/minio_config.py` con la línea: `self.secure = False`

**Error: No se descarga el archivo**
→ Verifica que MinIO está corriendo: `localhost:9000`
→ Verifica permisos de escritura en carpeta `file/`

**Error: Power BI no ve actualizaciones**
→ Usa `monitor_powerbi.py` para verificar que se descarga
→ Configura refresh automático en Power BI

---

## 📋 Próximos Pasos

1. ✅ **Ejecutar pipeline:** `python main.py`
2. ✅ **Monitorear:** Abre otra terminal y ejecuta `python monitor_powerbi.py`
3. ✅ **Verificar archivo:** Verifica que aparece en `file/metricas_kpi_gold.csv`
4. ✅ **Importar en Power BI:** Sigue el paso 2 de GUIA_PIPELINE_POWERBI.md
5. ✅ **Crear dashboard:** Usa los KPIs para tus visualizaciones

---

**Estado:** ✅ Completado y Validado
**Fecha:** 2025-12-03
**Cambios Totales:** 5 archivos modificados / creados
