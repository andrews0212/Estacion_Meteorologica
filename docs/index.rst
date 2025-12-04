Estación Meteorológica
======================

Sistema ETL para monitoreo y análisis de datos de estaciones meteorológicas.

**Descripción del Proyecto:**

La Estación Meteorológica es un pipeline de datos (ETL) que implementa la arquitectura medallion (Bronze, Silver, Gold) para:

- **Extracción**: Obtener datos de temperatura, humedad, velocidad de viento y más desde una base de datos PostgreSQL
- **Transformación**: Limpiar, enriquecer y transformar los datos usando PySpark
- **Carga**: Almacenar datos procesados en MinIO (almacenamiento S3-compatible) y generar KPIs

.. toctree::
   :maxdepth: 2
   :caption: Documentación

   guia_uso
   modules
   etl/pipeline
   etl/table_processor
   etl/extractors
   etl/managers
   etl/writers
   etl/uploaders
   etl/utils
   etl/control
   etl/config

