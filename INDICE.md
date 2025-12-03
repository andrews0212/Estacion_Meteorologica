# 📊 INDICE COMPLETO - Pipeline ETL + Power BI

## 🎯 Comienza Aquí

**¿Quieres ejecutar el pipeline ahora?**

### Opción A: Windows Command Prompt (Recomendado)
```cmd
start_pipeline.bat
```
Interfaz interactiva con menú de opciones

### Opción B: PowerShell
```powershell
.\quickstart.ps1 run
```
Pipeline continuo con ciclos cada 5 minutos

### Opción C: Terminal Estándar
```bash
python main.py
```
Ejecución directa del pipeline


---

## 📁 Guía de Archivos

### 🚀 **Scripts Principales** (Ejecutables)

| Archivo | Uso | Comando |
|---------|-----|---------|
| `main.py` | Pipeline principal continuo | `python main.py` |
| `test_pipeline.py` | Validar pipeline con N ciclos | `python test_pipeline.py -c 1` |
| `monitor_powerbi.py` | Monitorear cambios en tiempo real | `python monitor_powerbi.py --interval 5` |
| `descargar_gold.py` | Descargar manualmente Gold CSV | `python descargar_gold.py` |
| `start_pipeline.bat` | Interfaz interactiva (Windows) | `start_pipeline.bat` |
| `quickstart.ps1` | Interface rápida (PowerShell) | `.\quickstart.ps1 run` |

### 📚 **Documentación**

| Archivo | Contenido |
|---------|----------|
| `RESUMEN_IMPLEMENTACION.txt` | **👈 RESUMEN EJECUTIVO (leer primero)** |
| `GUIA_PIPELINE_POWERBI.md` | Instrucciones detalladas completas |
| `CAMBIOS_DESCARGA_POWERBI.md` | Cambios técnicos realizados |
| `README.md` | Documentación general del proyecto |
| `DOCUMENTACION.md` | Documentación técnica extendida |
| Este archivo | Índice y navegación |

### ⚙️ **Configuración**

| Archivo | Propósito |
|---------|----------|
| `config/minio_config.py` | Configuración MinIO (localhost:9000) |
| `config/database_config.py` | Configuración PostgreSQL |
| `.etl_state.json` | Estado de extracciones (generado) |

### 📊 **Datos**

| Carpeta | Contenido |
|---------|----------|
| `file/` | **📥 Archivo Power BI** |
| `file/metricas_kpi_gold.csv` | **CSV que se actualiza en cada ciclo** |

---

## 🔄 Flujo de Ejecución Completo

```
1️⃣  EXTRACCIÓN
    PostgreSQL 
        ↓ (sensor_readings table)
    main.py → etl/pipeline.py
        ↓
    MinIO Bronze Bucket
    (datos RAW sin procesar)

2️⃣  LIMPIEZA
    MinIO Silver (lectura)
        ↓
    etl/scripts/silver_layer.py
        ↓
    MinIO Silver (escritura)
    (datos limpios: 5 columnas)

3️⃣  KPIs
    MinIO Silver (lectura)
        ↓
    etl/scripts/gold_layer.py
        ↓
    MinIO Gold (escritura)
    (KPIs: 9 columnas)

4️⃣  DESCARGA AUTOMÁTICA ✨ (NUEVO)
    MinIO Gold (lectura)
        ↓
    main.py → _download_gold_for_powerbi()
        ↓
    file/metricas_kpi_gold.csv (escritura local)

5️⃣  POWER BI
    file/metricas_kpi_gold.csv (lectura)
        ↓
    Power BI Desktop / Service
        ↓
    Dashboards y reportes
```

---

## 📋 Casos de Uso Comunes

### Caso 1: Iniciar Pipeline Continuamente
```bash
python main.py
```
- Ciclos cada 5 minutos
- Descarga automática a file/
- Ideal para producción

### Caso 2: Validar que Todo Funciona
```bash
python test_pipeline.py -c 3 -i 5
```
- 3 ciclos con 5 segundos entre ellos
- Resumen de éxito/fallos
- Ideal para verificación inicial

### Caso 3: Monitorear Actualizaciones
**Terminal 1:**
```bash
python main.py
```
**Terminal 2:**
```bash
python monitor_powerbi.py --interval 5
```
- Terminal 1: Ejecuta ciclos
- Terminal 2: Muestra cuándo se actualiza el archivo
- Ideal para debugging y seguimiento

### Caso 4: Descarga Manual Rápida
```bash
python descargar_gold.py
```
- Descarga el CSV sin ejecutar ciclo
- Ideal para actualización puntual

---

## 🎯 Integración con Power BI

### Pasos Rápidos

1. **Ejecutar Pipeline:**
   ```bash
   python main.py
   ```

2. **Abrir Power BI Desktop**

3. **Importar CSV:**
   - Home → Get Data → Text/CSV
   - Ruta: `C:\...\Estacion_Meteorologica\file\metricas_kpi_gold.csv`
   - Load

4. **Crear Visualizaciones:**
   - Usa columnas: `temp_avg`, `temp_max`, `hum_avg`, `hum_max`
   - Crea gráficos de tendencias, alertas, KPIs

5. **(Opcional) Refresh Automático:**
   - En Power BI: File → Options
   - Data Load → Auto-refresh (ajusta intervalo)


---

## 📊 Estructura del CSV Gold

**Ubicación:** `file/metricas_kpi_gold.csv`

**Columnas:**
```
id            INTEGER  - ID del sensor (1-5)
lecturas      INTEGER  - Cantidad total de registros
temp_avg      FLOAT    - Temperatura promedio (°C)
temp_max      FLOAT    - Temperatura máxima (°C)
temp_min      FLOAT    - Temperatura mínima (°C)
temp_std      FLOAT    - Desviación estándar temp
hum_avg       FLOAT    - Humedad promedio (%)
hum_max       FLOAT    - Humedad máxima (%)
hum_min       FLOAT    - Humedad mínima (%)
```

**Ejemplo:**
```csv
id,lecturas,temp_avg,temp_max,temp_min,temp_std,hum_avg,hum_max,hum_min
1,97,25.4,28.5,22.1,1.23,45.2,65.0,30.5
2,97,24.8,27.2,21.9,1.15,46.1,64.5,31.2
3,97,25.1,28.0,22.5,1.18,44.9,63.8,32.0
```

---

## ⚙️ Configuración

### Cambiar Intervalo entre Ciclos
**Archivo:** `main.py` (línea ~220)
```python
system = ETLSystem(extraction_interval=300)  # segundos (default: 300 = 5 min)
```

### Cambiar Credenciales MinIO
**Archivo:** `config/minio_config.py`
```python
self.endpoint = "localhost:9000"
self.access_key = "minioadmin"
self.secret_key = "minioadmin"
self.secure = False
```

### Cambiar Credenciales PostgreSQL
**Archivo:** `config/database_config.py`
```python
self.host = "10.202.50.50"
self.user = "postgres"
self.password = "tu_contraseña"
```

---

## 🔍 Troubleshooting

### ❌ "Error: No se puede conectar a MinIO"
```
→ Verificar: MinIO está corriendo en localhost:9000
→ Comprobar: Buckets existentes (meteo-bronze, meteo-silver, meteo-gold)
→ Verificar: Credenciales en config/minio_config.py
```

### ❌ "Error: Table 'sensor_readings' not found"
```
→ Verificar: PostgreSQL está accesible
→ Comprobar: Tabla 'sensor_readings' existe
→ Verificar: Credenciales en config/database_config.py
```

### ❌ "Error: File not found in file/ folder"
```
→ Verificar: Al menos 1 ciclo completó exitosamente
→ Comprobar: Permisos de escritura en carpeta file/
→ Intentar: python descargar_gold.py manualmente
```

### ❌ "Error: PySpark module not found"
```
→ Instalar: pip install pyspark==3.4.1
→ Verificar: pip list | grep pyspark
```

### ❌ "Error: 'MinIOConfig' object has no attribute 'secure'"
```
→ Actualizar: config/minio_config.py con:
   self.secure = False
→ O usar main.py actual (ya está corregido)
```

---

## 📈 Comandos Avanzados

### Ejecutar 5 Ciclos de Prueba (25 segundos total)
```bash
python test_pipeline.py -c 5 -i 5
```

### Monitorear Cambios cada 3 Segundos durante 5 Minutos
```bash
python monitor_powerbi.py --interval 3 --duration 300
```

### Descargar y Ver Primeras Líneas
```bash
python descargar_gold.py && Get-Content file/metricas_kpi_gold.csv -First 6
```

### Ver Estado de Extracciones
```bash
python -c "from etl.etl_state import StateManager; StateManager().display_state()"
```

### Limpiar Estado de Extracciones (fuerza re-extracción)
```bash
python -c "from etl.etl_state import reset_etl_state; reset_etl_state()"
```

---

## 🚀 Comandos de Inicio Rápido

**Windows CMD (Recomendado):**
```cmd
start_pipeline.bat
```

**PowerShell:**
```powershell
.\quickstart.ps1 run
```

**Terminal (Cualquier SO):**
```bash
python main.py
```

---

## 📞 Soporte Rápido

| Pregunta | Respuesta |
|----------|----------|
| ¿Cómo inicio? | `python main.py` |
| ¿Cómo valido? | `python test_pipeline.py -c 1` |
| ¿Cómo monitoreo? | `python monitor_powerbi.py` |
| ¿Dónde está el CSV? | `file/metricas_kpi_gold.csv` |
| ¿Qué contiene el CSV? | 97 filas con KPIs de 5 sensores |
| ¿Cómo importo en Power BI? | Get Data → Text/CSV → file/metricas_kpi_gold.csv |
| ¿Se actualiza automáticamente? | SÍ, en cada ciclo (cada 5 minutos) |
| ¿Puedo cambiar el intervalo? | SÍ, en main.py línea ~220 |
| ¿Hay que hacer algo manualmente? | NO, todo es automático |

---

## 📚 Lecturas Recomendadas

1. **Para empezar ahora:**
   - RESUMEN_IMPLEMENTACION.txt (este proyecto)

2. **Para entender el pipeline:**
   - GUIA_PIPELINE_POWERBI.md

3. **Para cambios técnicos:**
   - CAMBIOS_DESCARGA_POWERBI.md

4. **Para arquitectura general:**
   - DOCUMENTACION.md
   - README.md

5. **Para código:**
   - main.py (orquestación)
   - etl/scripts/silver_layer.py (limpieza)
   - etl/scripts/gold_layer.py (KPIs)

---

## ✅ Checklist de Implementación

- ✅ Pipeline principal (`main.py`) actualizado
- ✅ Descarga automática en cada ciclo
- ✅ Configuración MinIO corregida (`.secure`)
- ✅ Scripts de prueba y monitoreo creados
- ✅ Interfaz interactiva (batch + PowerShell)
- ✅ Documentación completa
- ✅ Validación exitosa con test
- ✅ CSV en `file/metricas_kpi_gold.csv`
- ✅ Listo para Power BI

---

## 🎉 Estado Final

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   Pipeline ETL + Power BI Integration               │
│   ✅ COMPLETADO Y VALIDADO                         │
│   ✅ LISTO PARA PRODUCCIÓN                         │
│                                                     │
│   Comando para empezar:                             │
│   > python main.py                                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

**Última actualización:** 2025-12-03
**Estado:** ✅ Operacional
**Versión:** 1.0
