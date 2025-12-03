# Changelog - Estación Meteorológica

Todos los cambios notables en este proyecto se documentan en este archivo.

---

## [3.0] - 2025-12-03

### ✨ Agregado

#### 1. Módulo de Limpieza Automática (🆕 Característica Principal)
- **Nuevo módulo**: `etl/cleaners/` con `DataCleaner`
- Limpieza automática ejecutada después de cada batch de extracción
- Combina **todos** los archivos de Bronce en un único DataFrame
- Aplica reglas de limpieza:
  - Eliminación de duplicados
  - Reemplazo de outliers (método IQR)
  - Eliminación de columnas innecesarias
  - Filtrado de valores en rangos válidos
- Guarda resultado en MinIO Silver

#### 2. Estrategia REPLACE Implementada
- Gestión automática de versiones
- Mantiene solo el archivo más reciente en Silver
- Elimina automáticamente versiones antiguas
- Sin intervención manual requerida

#### 3. Integración con Pipeline
- `main.py` ahora ejecuta:
  1. Extracción Bronce
  2. Limpieza Silver
  3. En ciclo continuo cada 5 minutos

#### 4. Documentación Completa
- `README.md`: Guía rápida de inicio
- `DOCUMENTACION.md`: Documentación técnica completa
- `ESTADO_FINAL_LIMPIEZA.md`: Estado actual del proyecto
- `CHANGELOG.md`: Este archivo

### 🐛 Reparado

- Problema: No se generaban archivos en Silver
  - **Solución**: Implementar limpieza automática integrada

- Problema: Archivos de Bronce se acumulaban
  - **Solución**: Combinarlos en Silver único

- Problema: Acumulación de versiones en Silver
  - **Solución**: Estrategia REPLACE automática

### 🔄 Cambios

#### main.py
```python
# ANTES:
class ETLSystem:
    def run_cycle(self, cycle_num: int) -> bool:
        self.pipeline.process_batch()
        return True

# DESPUÉS:
class ETLSystem:
    def run_cycle(self, cycle_num: int) -> bool:
        self.pipeline.process_batch()
        self._run_cleaning()  # 🆕 Limpieza automática
        return True
```

#### control_manager.py → control/control_manager.py
- Movido a subdirectorio `control/` para mejor organización

### 📝 Documentación

- ✅ DOCUMENTACION.md: +500 líneas con nueva arquitectura
- ✅ ESTADO_FINAL_LIMPIEZA.md: Completamente reescrito
- ✅ README.md: Creado nuevo con guía rápida
- ✅ CHANGELOG.md: Creado (este archivo)

### 📊 Estadísticas de Cambios

| Métrica | Valor |
|---------|-------|
| Archivos nuevos | 3 |
| Líneas de código añadidas | ~400 |
| Módulos nuevos | 1 (`cleaners/`) |
| Clases nuevas | 1 (`DataCleaner`) |
| Métodos nuevos | 5 en `DataCleaner` |
| Documentación añadida | ~1000 líneas |

---

## [2.0] - 2025-12-02

### ✨ Agregado

#### Refactorización OOP Completa
- Eliminación de código muerto
- Aplicación de principios SOLID
- Patrones de diseño modernos
- Type hints 100%

#### Migración SQL → JSON
- Sistema de estado basado en archivo `.etl_state.json`
- Eliminación de tabla `etl_control` en PostgreSQL
- `StateManager` para gestión centralizada

### 🗑️ Eliminado

- `limpiar_cache.py` - Script obsoleto
- `clear_cache.py` - Script obsoleto
- `silver_layer_spark.py` - Implementación alternativa no usada
- `ETLControlQueries` - Clase SQL obsoleta
- Método `get_incremental_extract_query()` - No invocado
- Método `initialize_table()` - No necesario

### 🔄 Cambios

- Arquitectura modular completa
- Separación clara de responsabilidades
- Mejor mantenibilidad del código

---

## [1.0] - 2025-11-30

### ✨ Agregado

#### Pipeline Base
- Extracción incremental de PostgreSQL
- Detección automática de columnas de rastreo
- Almacenamiento en MinIO (Bronce)
- Control de estado de extracciones

#### Componentes Core
- `DatabaseConfig` - Configuración PostgreSQL
- `MinIOConfig` - Configuración MinIO
- `TableInspector` - Inspección de schema
- `DataExtractor` - Extracción incremental
- `ETLPipeline` - Orquestación
- `TableProcessor` - Procesamiento por tabla

#### Funcionalidades
- Ejecución en ciclos continuos
- Intervalo configurable
- Detección automática de nuevos datos
- Logs informativos

---

## Planificación Futura

### [3.1] - Próximo Release
- [ ] Logging estructurado (logging module)
- [ ] Retry automático en errores
- [ ] Métricas y monitoreo

### [3.2] - Mejoras de Operaciones
- [ ] API REST para monitoreo
- [ ] Interfaz web de administración
- [ ] Alertas por errores
- [ ] Dashboard de estadísticas

### [4.0] - Arquitectura Avanzada
- [ ] Async/Await para mejor performance
- [ ] Tests unitarios e integración
- [ ] Soporte para múltiples bases de datos
- [ ] Cache distribuido

---

## Notas de Versión

### v3.0 - Cambios Significativos

**Punto de quiebre**: La estructura de directorios cambió. Asegurar que:
- Los imports se actualicen si hay código personalizado
- Las rutas apunten al nuevo `etl/cleaners/`

**Migración desde v2.0 a v3.0**:
```python
# ANTES (v2.0):
# Limpieza manual o via notebook

# AHORA (v3.0):
# Limpieza automática integrada en pipeline
python main.py  # Hace todo automáticamente
```

---

## Cómo Contribuir

Si encuentras bugs o tienes ideas de mejora:

1. **Reportar bugs**: Crear un issue con detalles
2. **Sugerir mejoras**: Describir la funcionalidad deseada
3. **Contribuir código**: Fork + Pull Request

---

## Historial de Cambios por Componente

### ETL Pipeline
- v1.0: Implementación base
- v2.0: Refactorización OOP
- v3.0: Integración de limpieza automática

### State Management
- v1.0: Tabla `etl_control` en PostgreSQL
- v2.0: Migración a JSON (`.etl_state.json`)
- v3.0: Sin cambios (estable)

### Data Cleaner
- v1.0: No existe
- v2.0: No existe
- v3.0: Implementación completa

### MinIO Storage
- v1.0: Bronce solamente
- v2.0: Bronce + Silver manual
- v3.0: Bronce + Silver automático con REPLACE

---

**Última actualización**: 3 de Diciembre de 2025  
**Versión actual**: 3.0  
**Mantenedor**: Andrews0212
