Guía de Uso
===========

Instalación
-----------

Prerrequisitos:
  - Python 3.10+
  - PostgreSQL
  - MinIO (o compatible con S3)
  - PySpark

Instalación del entorno virtual:

.. code-block:: bash

    python -m venv venv_meteo
    .\venv_meteo\Scripts\activate
    pip install -r requirements.txt

Configuración
-------------

Crear archivo `.env` con variables de entorno:

.. code-block:: bash

    # PostgreSQL
    DB_HOST=localhost
    DB_PORT=5432
    DB_USER=user
    DB_PASSWORD=password
    DB_NAME=meteorology

    # MinIO
    MINIO_HOST=localhost:9000
    MINIO_ACCESS_KEY=minioadmin
    MINIO_SECRET_KEY=minioadmin
    MINIO_SECURE=false

Uso
---

**Ejecutar pipeline único:**

.. code-block:: python

    python main.py

**Ejecutar scheduler continuo:**

.. code-block:: powershell

    .\run_scheduler.ps1

**Simular datos:**

.. code-block:: python

    python main.py --simulate

Arquitectura
------------

El sistema implementa la arquitectura medallion de 3 capas:

1. **Bronze**: Datos crudos extraídos de PostgreSQL
   - Almacenados en MinIO bucket: `bronze-layer`
   - Formato CSV con metadata

2. **Silver**: Datos limpios y transformados
   - Almacenados en MinIO bucket: `silver-layer`
   - Aplicadas transformaciones PySpark
   - Ejecutado mediante notebooks en `notebooks/templates/limpieza_template.ipynb`

3. **Gold**: Datos agregados y KPIs
   - Almacenados en MinIO bucket: `gold-layer`
   - Métricas y KPIs calculados
   - Ejecutado mediante notebooks en `notebooks/templates/generacion_KPI.ipynb`

Flujo de Datos
--------------

.. code-block:: text

    PostgreSQL → ETL Pipeline → Bronze Layer (MinIO)
                                    ↓
                            Silver Layer (MinIO)
                            [PySpark Transformations]
                                    ↓
                            Gold Layer (MinIO)
                            [KPI Calculation]
                                    ↓
                            Reporting & Analytics

Estado y Tracking
-----------------

El sistema mantiene un registro de estado en `.etl_state.json`:

.. code-block:: json

    {
      "last_execution_time": "2025-01-01T12:00:00",
      "tables": {
        "tabla_1": {
          "last_extracted_id": 1000,
          "last_extracted_timestamp": "2025-01-01T12:00:00"
        }
      }
    }

Utilidades y Herramientas
-------------------------

**DatabaseUtils**: Conexión y operaciones a PostgreSQL
**MinIOUtils**: Operaciones con almacenamiento MinIO
**TableInspector**: Inspección automática de tablas y detección de columnas de tracking
**ExtractionStateManager**: Gestión del estado de extracción
**NotebookExecutor**: Ejecución de notebooks PySpark con Papermill
