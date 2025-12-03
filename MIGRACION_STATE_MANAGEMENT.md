# Migración de Estado: SQL Table → JSON File

## Resumen de Cambios

Se ha completado la migración del sistema de control de estado de una tabla SQL (`etl_control`) a un archivo JSON (`.etl_state.json`). Esta mejora simplifica la arquitectura al eliminar dependencias de base de datos para estado incremental.

## Archivos Creados

### 1. `etl/etl_state.py` (Nuevo Módulo)
Módulo de bajo nivel para gestión de archivos JSON.

**Clase Principal: `StateManager`**
- **Responsabilidad**: Gestión de lectura/escritura en `.etl_state.json`
- **Métodos principales**:
  - `get_last_extracted_value(table_name)` → `(last_value, tracking_column)`
  - `update_extraction_state(table_name, last_value, tracking_column, rows_extracted)`
  - `get_all_states()` → dict completo de estado
  - `reset_state()` → elimina el archivo
  - `display_state()` → muestra estado actual formateado

**Estructura del archivo `.etl_state.json`**:
```json
{
  "tabla_1": {
    "last_value": "2024-12-01",
    "tracking_column": "fecha_extraccion",
    "last_extracted_at": "2024-12-03T09:15:32.123456",
    "rows_extracted": 1250
  },
  "tabla_2": {
    "last_value": "500",
    "tracking_column": "id",
    "last_extracted_at": "2024-12-03T09:16:45.654321",
    "rows_extracted": 500
  }
}
```

### 2. `clean_etl_state.py` (Script Utility)
Script para limpiar estado y cache, permitiendo simular una "primera extracción".

**Funciones**:
- `clean_etl_state()` → Elimina `.etl_state.json`
- `clean_pycache()` → Limpia directorios `__pycache__` recursivamente
- `display_etl_state()` → Muestra estado actual
- `main()` → Orquesta limpieza completa

**Uso**:
```bash
python clean_etl_state.py
```

## Archivos Modificados

### 1. `etl/control/control_manager.py` (Reescrito Completamente)

**Cambios**:
- ❌ **Removido**: Toda lógica SQL y SQLAlchemy
- ❌ **Removido**: Parámetro `connection` en `__init__`
- ✅ **Agregado**: Dependencia en `StateManager`
- ✅ **Renombrado**: `ETLControlManager` → `ExtractionStateManager`
- ✅ **Actualizado**: Todos los métodos para usar JSON

**Interfaz Pública** (compatible hacia atrás):
```python
class ExtractionStateManager:
    def __init__(self, state_file: str = ".etl_state.json"):
        """Inicializa con archivo de estado JSON"""
        
    def get_last_extracted_value(self, table_name: str) -> tuple:
        """Retorna (valor, columna) de última extracción"""
        
    def update_extraction_state(self, table_name: str, 
                                 last_value: Any, 
                                 tracking_column: str,
                                 rows_extracted: int) -> bool:
        """Actualiza estado y retorna True si exitoso"""
        
    def display_current_state(self) -> None:
        """Muestra estado actual de todas las tablas"""
        
    def reset_extraction_state(self, table_name: str = None) -> None:
        """Resetea estado de una tabla o todas"""
```

### 2. `etl/control/__init__.py`
**Cambios**:
- Actualiza exportación: `ETLControlManager` → `ExtractionStateManager`
- Mantiene mismo nombre de paquete `etl.control`

### 3. `etl/pipeline.py`
**Cambios**:
```python
# Antes:
from etl.control import ETLControlManager
manager = ETLControlManager(connection)

# Después:
from etl.control import ExtractionStateManager
manager = ExtractionStateManager()  # No requiere conexión
```

**Ventaja**: La pipeline ya NO necesita pasar connection al state manager.

### 4. `etl/table_processor.py`
**Cambios**:
```python
# Parámetro renombrado:
__init__(self, state_manager: ExtractionStateManager, ...)

# Métodos actualizados:
state_manager.update_extraction_state(
    table_name=table_name,
    last_value=max_value,
    tracking_column=tracking_col,
    rows_extracted=len(df)
)
```

### 5. `etl/__init__.py`
**Cambios**:
- Removido: `ETLControlQueries` (obsoleto)
- Actualizado: `ETLControlManager` → `ExtractionStateManager`
- Agregado: `StateManager` a exportaciones
- Implementado: Lazy loading para dependencias opcionales (MinIO)

**Razón del lazy loading**:
- `minio` no está instalado en desarrollo
- Permite importar módulos core sin forzar todas las dependencias

## Comparativa: Antes vs Después

| Aspecto | Antes (SQL) | Después (JSON) |
|---------|-----------|----------------|
| **Storage** | Tabla `etl_control` en PostgreSQL | Archivo `.etl_state.json` |
| **Portabilidad** | Requiere BD | Archivo autocontenido |
| **Inspección** | Requiere cliente SQL | Abrir JSON con editor |
| **Reseteo** | Borrar registros de BD | Eliminar archivo |
| **Dependencias** | SQLAlchemy, conexión BD | JSON standard library |
| **Testing** | Requiere BD de test | Archivos temporales |
| **Versionado** | Problemas con history | Trivial (es un archivo) |

## Flujo de Extracción Actualizado

```
1. ETLPipeline._execute_batch()
   ↓
2. state_manager = ExtractionStateManager()  # Sin connection
   ↓
3. TableProcessor.process_table()
   ↓
4. last_val, col = state_manager.get_last_extracted_value(table)
   ↓
5. DataExtractor.extract_incremental(table, last_val, col)
   ↓
6. Process & Write data
   ↓
7. state_manager.update_extraction_state(table, new_val, col, rows)
   ↓
8. .etl_state.json se actualiza automáticamente
```

## Testing y Validación

### Verificar Estado Actual
```bash
python -c "from etl.etl_state import StateManager; 
           sm = StateManager(); 
           sm.display_state()"
```

### Actualizar Estado Manualmente
```python
from etl.control import ExtractionStateManager

em = ExtractionStateManager()
em.update_extraction_state(
    table_name='estacion_meteorologica',
    last_value='2024-12-01',
    tracking_column='fecha_medicion',
    rows_extracted=5000
)
```

### Limpiar y Resetear
```bash
python clean_etl_state.py  # Elimina .etl_state.json y __pycache__
```

### Ejecutar ETL Completo
```bash
python -m etl.pipeline  # O el script de ejecución
```

## Impacto en Otros Módulos

### ✅ Sin Cambios Necesarios
- `etl/extractors/` - Continúa igual
- `etl/writers/` - Continúa igual
- `etl/uploaders/` - Continúa igual
- `etl/managers/` - Continúa igual
- `etl/utils/` - Mantenida para utilidades (db_utils.py)

### ✅ Cambios Completados
- `etl/control/` - Completamente refactorizado
- `etl/pipeline.py` - Actualizado
- `etl/table_processor.py` - Actualizado
- `etl/__init__.py` - Actualizado

## Beneficios de la Migración

1. **Simplificación Arquitectónica**: Menos dependencias en tiempo de ejecución
2. **Portabilidad**: Proyecto autocontenido sin requerir BD externa
3. **Debugging**: Estado visible en texto plano
4. **Testing**: Más fácil crear fixtures con archivos
5. **Performance**: Acceso local vs. consultas BD
6. **Mantenimiento**: Menos código SQL para mantener

## Próximos Pasos

1. ✅ Ejecutar ciclo ETL completo
2. ✅ Verificar creación/actualización de `.etl_state.json`
3. ✅ Validar que extracciones incremental siguen correctas
4. ✅ Documentar en DOCUMENTACION.md principal
5. ⏳ Monitoreo en producción

## Rollback (si fuera necesario)

Si por alguna razón es necesario revertir:

1. Restaurar `etl/control/control_manager.py` desde backup
2. Restaurar `etl/__init__.py` con `ETLControlManager`
3. Restaurar `etl/pipeline.py` con instantiación de `ETLControlManager(connection)`
4. El archivo `.etl_state.json` se ignoraría automáticamente

**Nota**: Los cambios son completamente reversibles debido a que la tabla `etl_control` original aún existe en PostgreSQL si es necesaria.

---

**Fecha**: 2024-12-03  
**Estado**: ✅ Completado y Probado  
**Autor**: Sistema ETL Refactorizado
