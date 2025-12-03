# 🚀 GUÍA RÁPIDA - CÓMO EJECUTAR EL SISTEMA ETL

## Inicio Rápido (30 segundos)

```bash
# 1. Abre PowerShell en la carpeta del proyecto
cd "C:\Users\Alumno_AI\Desktop\Estacion_Meteorologica"

# 2. Ejecuta el pipeline interactivo
.\run_pipeline.ps1

# 3. Selecciona opción (1 = pipeline completo)
# Espera a que termine
# ✅ Listo!
```

---

## Opciones Disponibles

### Opción 1️⃣: Pipeline Completo (Recomendado)
```bash
.\run_pipeline.ps1
# Selecciona: 1
```
**Qué hace:**
- Extrae datos de PostgreSQL
- Limpia en Silver layer
- Calcula KPIs en Gold layer
- Se ejecuta cada 300 segundos en loop

---

### Opción 2️⃣: Solo Limpiar Datos (Silver)
```bash
python etl/scripts/silver_layer.py
```
**Qué hace:**
- Lee CSV del bucket meteo-bronze
- Elimina columnas innecesarias
- Remueve duplicados
- Escribe CSV limpio en meteo-silver

---

### Opción 3️⃣: Solo Calcular KPIs (Gold)
```bash
python etl/scripts/gold_layer.py
```
**Qué hace:**
- Lee CSV del bucket meteo-silver
- Agrupa por sensor ID
- Calcula: count, avg, max, min, stddev
- Escribe métricas en meteo-gold

---

## 📊 Verificar Resultados

### Ver archivos en MinIO
```bash
# Opción A: Interfaz web
http://localhost:9000

# Opción B: Script Python
python -c "
from minio import Minio
m = Minio('localhost:9000', 'minioadmin', 'minioadmin', secure=False)
for bucket in ['meteo-bronze', 'meteo-silver', 'meteo-gold']:
    print(f'{bucket}:')
    for obj in m.list_objects(bucket):
        print(f'  - {obj.object_name}')
"
```

---

## ⚙️ Configuración Avanzada

### Cambiar Intervalo de Extracción
Edita `main.py` línea 192:
```python
system = ETLSystem(extraction_interval=300)  # Cambiar a 60 para cada 1 minuto
```

### Agregar Más Métricas a Gold
Edita `etl/scripts/gold_layer.py` línea ~45:
```python
kpi_df = df.groupby('id').agg({
    'temperature': ['mean', 'std', 'min', 'max'],  # Agregar nuevas métricas
    'humidity': ['mean', 'max'],
})
```

### Variables de Entorno (Opcional)
```bash
$env:PG_HOST = "otro-servidor"
$env:PG_DB = "otra_bd"
$env:MINIO_ENDPOINT = "otro-minio:9000"
python main.py
```

---

## 🆘 Solución de Problemas

### Problema: "ModuleNotFoundError: No module named 'minio'"
**Solución:**
```bash
python -m pip install -q minio pandas sqlalchemy psycopg2-binary
```

### Problema: "Cannot connect to localhost:9000"
**Verificar MinIO está corriendo:**
```bash
# Buscar proceso MinIO
tasklist | findstr minio

# Si no está, iniciar MinIO (en otra terminal):
minio.exe server C:\data
```

### Problema: "PostgreSQL encoding error"
**Esperado**: Base de datos tiene UTF-8 inválido
**Solución**: Usar CSV en meteo-bronze en lugar de extraer de PostgreSQL

### Problema: "PowerShell: Archivo no se puede ejecutar"
**Solución:**
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\run_pipeline.ps1
```

---

## 📈 Monitoreo

### Ver logs en tiempo real
```bash
# Terminal 1: Ejecutar pipeline
python main.py

# Terminal 2: Monitorear MinIO
while($true) {
    cls
    python -c "
from minio import Minio
m = Minio('localhost:9000', 'minioadmin', 'minioadmin', secure=False)
for b in ['meteo-bronze', 'meteo-silver', 'meteo-gold']:
    objs = list(m.list_objects(b))
    print(f'{b}: {len(objs)} archivos')
"
    Start-Sleep -Seconds 5
}
```

---

## 📋 Checklist de Instalación

- [ ] Python 3.8+ instalado
- [ ] `pip install pandas minio sqlalchemy psycopg2-binary`
- [ ] PostgreSQL corriendo en localhost (opcional)
- [ ] MinIO corriendo en localhost:9000
- [ ] `venv_meteo` directorio con Python binaries
- [ ] Buckets en MinIO: meteo-bronze, meteo-silver, meteo-gold

---

## 🎯 Uso en Producción

### Ejecutar como servicio Windows
```bash
# Crear archivo: run_etl_service.bat
@echo off
cd "C:\Users\Alumno_AI\Desktop\Estacion_Meteorologica"
python main.py
```

Luego registrar como servicio Windows Scheduler o Task Scheduler.

### Ejecutar en Docker (Próximamente)
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

---

## 📞 Soporte

Para errores, revisar:
1. `SOLUCION_FINAL.md` - Documentación técnica
2. `RESUMEN_TECNICO.md` - Detalles de arquitectura
3. Logs de consola - Mensajes de error específicos

---

**Última actualización**: 2025-12-03
**Versión**: 1.0 (Production Ready)
**Status**: 🟢 OPERATIVO
