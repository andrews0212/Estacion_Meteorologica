# Documentación Sphinx - Estación Meteorológica ETL

## Generación y Visualización

### Generar la documentación

```powershell
# Con Python del venv
C:\Users\Alumno_AI\Desktop\Estacion_Meteorologica\venv_meteo\Scripts\python.exe generate_docs_simple.py
```

Los archivos HTML se generan en:
```
docs/build/html/
```

### Visualizar la documentación (Opción 1: Navegador)

```powershell
# Iniciar servidor HTTP
C:\Users\Alumno_AI\Desktop\Estacion_Meteorologica\venv_meteo\Scripts\python.exe serve_docs.py
```

Se abrirá automáticamente en `http://localhost:8000`

### Visualizar la documentación (Opción 2: Archivo local)

Abre directamente en tu navegador:
```
file:///C:/Users/Alumno_AI/Desktop/Estacion_Meteorologica/docs/build/html/index.html
```

## Contenido de la documentación

- **Introducción**: Vista general del sistema
- **Documentación técnica**: Detalles de arquitectura y componentes
- **API Reference**: Documentación automática de todas las clases y métodos
- **Changelog**: Historial de cambios
- **Estado**: Status actual del proyecto

## Módulos documentados

### ETL
- `etl.pipeline` - Orquestación del pipeline
- `etl.table_processor` - Procesamiento de tablas individuales
- `etl.cleaners.data_cleaner` - Limpieza automática de datos
- `etl.extractors.data_extractor` - Extracción incremental
- `etl.extractors.table_inspector` - Inspección de esquema
- `etl.uploaders.minio_uploader` - Subida a MinIO
- `etl.writers.csv_writer` - Escritura CSV
- `etl.utils.db_utils` - Utilidades de base de datos

### Configuración
- `config.database_config` - Configuración PostgreSQL
- `config.minio_config` - Configuración MinIO

## Requisitos

```powershell
pip install sphinx sphinx-rtd-theme
```

Ya están instalados en el venv_meteo.

## Troubleshooting

**Q: No se ve la documentación en el navegador**
A: Asegúrate de que el servidor está corriendo con `serve_docs.py`

**Q: Quiero que los cambios en el código se reflejen en la documentación**
A: Ejecuta nuevamente `generate_docs_simple.py`

**Q: Hay warnings al generar**
A: Los warnings son normales. Los 4 warnings actuales son sobre referencias duplicadas que no afectan la funcionalidad.
