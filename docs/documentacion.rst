===============================
Documentación Técnica Completa
===============================

Sistema ETL Incremental
========================

El sistema ETL está diseñado para extraer datos de PostgreSQL de forma incremental,
limpiarlos automáticamente y almacenarlos en MinIO.

**Componentes principales:**

1. **Extractor** - Extrae datos de PostgreSQL
2. **Limpiador** - Aplica reglas de limpieza automática
3. **Uploader** - Sube archivos a MinIO
4. **State Manager** - Gestiona el estado del proceso

Flujo de datos
==============

.. code-block:: text

    PostgreSQL (Fuente)
        ↓
    Extracción (incremental)
        ↓
    Archivos CSV (Bronce en MinIO)
        ↓
    Limpieza (duplicados, outliers)
        ↓
    Archivos consolidados (Silver en MinIO)


Ver referencia de API en :doc:`modules`.
