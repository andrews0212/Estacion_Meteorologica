# 🌤️ Estación Meteorológica - Sistema ETL + Notebooks

[![Python 3.13+](https://img.shields.io/badge/Python-3.13-blue)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-darkblue)](https://www.postgresql.org/)
[![MinIO](https://img.shields.io/badge/MinIO-S3%20compatible-orange)](https://min.io/)
[![Status](https://img.shields.io/badge/Status-Production-green)]()

Sistema ETL automatizado con **notebooks Jupyter** para limpieza de datos:
- ✅ Extrae datos de PostgreSQL → MinIO (Bronce)
- ✅ Ejecuta notebook de limpieza automáticamente
- ✅ Publica datos limpios → MinIO (Silver)
- ✅ Ciclos cada 5 minutos sin intervención

---

## ⚡ Inicio Rápido (3 comandos)

```powershell
cd C:\Users\Alumno_AI\Desktop\Estacion_Meteorologica
.\venv_meteo\Scripts\python.exe main.py
# Presiona Ctrl+C para detener
```

---

## 📝 Editar Lógica de Limpieza

Abre el notebook y agrega tu lógica:
```
notebooks/templates/limpieza_template.ipynb
```

El sistema ejecutará tu notebook automáticamente en cada ciclo.

---

## 🏗️ Arquitectura

```
PostgreSQL 
  ↓ [pipeline.process_batch()]
MinIO Bronce (CSV crudos)
  ↓ [NotebookExecutor.execute()]
notebooks/templates/limpieza_template.ipynb
  ↓ [Spark/Pandas transformaciones]
MinIO Silver (Parquet limpio)
```

### Componentes Principales

| Archivo | Responsabilidad |
|---------|-----------------|
| `main.py` | Orquestación del sistema |
| `etl/pipeline.py` | Extracción incremental PostgreSQL |
| `etl/notebook_executor.py` | Ejecución de notebooks con papermill |
| `notebooks/templates/limpieza_template.ipynb` | Lógica de limpieza (editable) |
| `config/` | Configuración BD y MinIO |

---

## 📦 Estructura del Proyecto

```
Estacion_Meteorologica/
├── main.py                          ← PUNTO DE ENTRADA
├── config/
│   ├── database_config.py
│   └── minio_config.py
├── etl/
│   ├── pipeline.py                  ← Extracción
│   ├── notebook_executor.py         ← Ejecutor notebooks NEW
│   ├── extractors/
│   ├── writers/
│   ├── uploaders/
│   └── utils/
├── notebooks/templates/
│   └── limpieza_template.ipynb      ← EDITAR AQUÍ
├── docs/                             ← Sphinx docs
└── venv_meteo/                       ← Python 3.13.9
```

---

## 🔧 Configuración

Variables de entorno (en `config/minio_config.py` y `config/database_config.py`):

```python
# PostgreSQL
PG_HOST = "10.202.50.50"
PG_USER = "postgres"
PG_PASS = "1234"
PG_DB = "postgres"

# MinIO
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
```

---

## 📊 Monitoreo

### Ver buckets en MinIO
```bash
# Datos crudos
mc ls myminio/meteo-bronze/

# Datos limpios
mc ls myminio/meteo-silver/
```

### Ver logs del sistema
```powershell
# En la consola donde corre main.py aparecen los logs de cada ciclo
```

---

## 🎯 Personalizar Limpieza

Abre `notebooks/templates/limpieza_template.ipynb` y en las últimas celdas agrega:

```python
# Cargar datos desde Bronce
df = cargar_csv_reciente("nombre_tabla")

# Aplicar transformaciones
df_limpio = df \
    .filter(col("temperatura") > -50) \
    .dropDuplicates(["id"]) \
    .select("fecha", "temperatura", "humedad")

# Guardar en Silver
guardar_en_silver("tabla_limpia", df_limpio)
```

---

## 🧪 Validar Sistema

```powershell
# Test imports
.\venv_meteo\Scripts\python.exe -c "from main import ETLSystem; print('✅ OK')"

# Ver configuración
.\venv_meteo\Scripts\python.exe -c "from config import DatabaseConfig, MinIOConfig; print(DatabaseConfig()); print(MinIOConfig())"
```

---

## 📚 Documentación Sphinx

```powershell
# Generar
.\docs.ps1 all

# Ver en navegador
.\docs.ps1 open
```

---

## 🛠️ Solución de Problemas

### PostgreSQL: Connection refused
```powershell
# Verificar conexión
psql -h 10.202.50.50 -U postgres -c "SELECT 1"
```

### MinIO: Connection refused
```powershell
# Verificar que MinIO corre
curl http://localhost:9000
```

### Notebook falla
1. Abre `notebooks/templates/limpieza_template.ipynb` en VS Code
2. Ejecuta celdas una por una
3. Revisa los outputs para ver el error
4. Corrige la lógica
5. Vuelve a ejecutar `python main.py`

---

## 📋 Cambios Recientes (Refactorización)

### ✅ Eliminado
- ❌ Clase `DataCleaner` (código acoplado)
- ❌ Directorio `etl/cleaners/` completo

### ✅ Agregado
- ✅ Módulo `etl/notebook_executor.py`
- ✅ Integración con Papermill
- ✅ Ejecución de notebooks en pipeline

### ✅ Actualizado
- ✅ `main.py` - Refactorizado para usar notebooks
- ✅ `etl/pipeline.py` - Integración con NotebookExecutor

---

## 🤝 Contribuir

1. Fork el repositorio
2. Crea rama (`git checkout -b feature/mejora`)
3. Commit cambios (`git commit -am 'Agrega mejora'`)
4. Push (`git push origin feature/mejora`)
5. Abre Pull Request

---

## 📄 Licencia

MIT - Ver [LICENSE](LICENSE)

---

## 👤 Autor

**Andrews0212** - Sistema ETL Incremental  
GitHub: [@andrews0212](https://github.com/andrews0212)

---

**Última actualización**: 3 de Diciembre de 2025  
**Versión**: 4.0 (Refactorizado con Notebooks)  
**Estado**: ✅ Producción
