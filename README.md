# 🌤️ Estación Meteorológica - Sistema ETL Incremental

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-darkblue)](https://www.postgresql.org/)
[![MinIO](https://img.shields.io/badge/MinIO-S3%20compatible-orange)](https://min.io/)
[![Status](https://img.shields.io/badge/Status-Production-green)]()

Sistema automatizado de **extracción, transformación y carga (ETL)** que:
- ✅ Extrae incrementalmente datos de PostgreSQL
- ✅ Almacena en MinIO (capa Bronce)
- ✅ Limpia automáticamente
- ✅ Consolida en versión única (capa Silver)
- ✅ Ejecuta cada 5 minutos sin intervención

---

## 🚀 Inicio Rápido

### 1. Clonar y Configurar
```bash
# Clonar repositorio
git clone https://github.com/andrews0212/Estacion_Meteorologica.git
cd Estacion_Meteorologica

# Crear entorno virtual
python -m venv venv_meteo
.\venv_meteo\Scripts\Activate  # Windows
source venv_meteo/bin/activate  # Linux/Mac

# Instalar dependencias
pip install pandas sqlalchemy psycopg2-binary minio
```

### 2. Configurar Variables de Entorno
Editar `run_scheduler.ps1` (Windows) o `run_scheduler.sh` (Linux):

```powershell
# PostgreSQL
$env:PG_HOST = "10.202.50.50"
$env:PG_USER = "postgres"
$env:PG_PASS = "1234"
$env:PG_DB = "postgres"

# MinIO
$env:MINIO_ENDPOINT = "localhost:9000"
$env:MINIO_ACCESS_KEY = "minioadmin"
$env:MINIO_SECRET_KEY = "minioadmin"
$env:MINIO_BUCKET = "meteo-bronze"
```

### 3. Crear Buckets en MinIO
```bash
mc alias set myminio http://localhost:9000 minioadmin minioadmin
mc mb myminio/meteo-bronze
mc mb myminio/meteo-silver
```

### 4. Ejecutar
```bash
python main.py
```

---

## 📊 Flujo de Datos

```
PostgreSQL (Origen)
    ↓
[Extracción Incremental]
    ↓
MinIO Bronce (CSV crudos)
    ↓
[Limpieza Automática]
    ↓
MinIO Silver (CSV consolidado + limpio)
```

---

## 🏗️ Arquitectura

### Componentes

| Componente | Responsabilidad |
|-----------|-----------------|
| **ETLPipeline** | Orquesta extracción de todas las tablas |
| **TableProcessor** | Procesa una tabla individual |
| **DataExtractor** | Extrae datos incrementales |
| **TableInspector** | Detecta estructura de tabla |
| **DataCleaner** | Limpia datos Bronce → Silver |
| **MinIOUploader** | Sube archivos a MinIO |
| **StateManager** | Rastrea estado en JSON |

### Capas de Datos

| Capa | Almacenamiento | Contenido | Estrategia |
|------|-----------------|-----------|-----------|
| **Bronce** | MinIO (CSV) | Datos crudos | Histórico completo |
| **Silver** | MinIO (CSV) | Datos limpios | REPLACE (versión única) |

---

## 🧹 Limpieza Automática

La limpieza se ejecuta **automáticamente** después de cada extracción:

```
Operaciones aplicadas:
✅ Combina archivos de Bronce
✅ Elimina duplicados
✅ Reemplaza outliers (método IQR)
✅ Elimina columnas innecesarias
✅ Filtra valores en rangos válidos
✅ Guarda en Silver único
✅ Elimina versiones antiguas
```

**Ejemplo:**
```
Ciclo 1: 97 filas extraídas
  → Bronce: 1 archivo
  → Silver: sensor_readings_silver_090000.csv

Ciclo 2: +50 filas nuevas
  → Bronce: 2 archivos (histórico)
  → Combina ambos = 147 filas
  → Silver: sensor_readings_silver_090500.csv (147 limpias)
  → ❌ Elimina versión anterior
```

---

## 📋 Estructura del Proyecto

```
Estacion_Meteorologica/
├── main.py                      # Punto de entrada
├── run_scheduler.ps1           # Script Windows
├── run_scheduler.sh            # Script Linux
├── .etl_state.json             # Estado incremental
│
├── config/
│   ├── database_config.py      # Config PostgreSQL
│   └── minio_config.py         # Config MinIO
│
├── etl/
│   ├── pipeline.py             # Orquestación
│   ├── table_processor.py      # Procesamiento
│   ├── etl_state.py            # Estado JSON
│   ├── cleaners/               # 🆕 Módulo limpieza
│   │   └── data_cleaner.py
│   ├── extractors/
│   ├── writers/
│   ├── uploaders/
│   ├── control/
│   └── utils/
│
├── notebooks/
│   └── templates/
│       └── limpieza_template.ipynb
│
└── DOCUMENTACION.md            # Documentación completa
```

---

## 🔧 Configuración Avanzada

### Cambiar Intervalo de Extracción
En `main.py`:
```python
system = ETLSystem(extraction_interval=600)  # 10 minutos
```

### Personalizar Limpieza
En `etl/cleaners/data_cleaner.py`:
```python
def _apply_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
    # Agregar operaciones personalizadas
    df = df[df['column'] > 0]  # Filtro personalizado
    return df
```

### Detectar Nueva Columna de Rastreo
En `etl/extractors/table_inspector.py`:
```python
TIMESTAMP_COLUMNS = ['created_at', 'updated_at', 'timestamp', 'tu_columna']
```

---

## 📊 Monitoreo

### Ver Estado de Extracciones
```python
from etl.etl_state import StateManager

manager = StateManager()
manager.display_state()
```

**Salida:**
```
════════════════════════════════════════════════════
📋 ESTADO ACTUAL DE EXTRACCIONES
════════════════════════════════════════════════════

📊 Tabla: sensor_readings
   Columna de rastreo: timestamp
   Último valor: 2025-10-23T12:11:04.612475+00:00
   Última extracción: 2025-12-03T09:40:12.123456
   Filas extraídas: 97
```

### Ver Archivos en MinIO
```bash
# Bronce
mc ls myminio/meteo-bronze/sensor_readings/

# Silver
mc ls myminio/meteo-silver/sensor_readings/
```

### Descargar Archivo
```bash
mc cp myminio/meteo-silver/sensor_readings/sensor_readings_silver*.csv ./
```

---

## 🧪 Testing

### Test de Extracción
```bash
python test_extraction.py
```

### Limpiar Estado (Reset)
```bash
python clean_etl_state.py
```

---

## 📖 Documentación Completa

- **[DOCUMENTACION.md](DOCUMENTACION.md)** - Documentación técnica completa
- **[ESTADO_FINAL_LIMPIEZA.md](ESTADO_FINAL_LIMPIEZA.md)** - Estado actual del proyecto
- **[ANALISIS_LIMPIEZA_CODIGO.md](ANALISIS_LIMPIEZA_CODIGO.md)** - Cambios realizados

---

## 🛠️ Solución de Problemas

### PostgreSQL: Connection refused
```bash
psql -h 10.202.50.50 -U postgres -c "SELECT 1"
```

### MinIO: Connection refused
```bash
# Verificar que MinIO está corriendo
curl http://localhost:9000

# Configurar alias
mc alias set myminio http://localhost:9000 minioadmin minioadmin
```

### No se generan archivos Silver
1. Verificar que hay datos en Bronce
2. Revisar logs de `DataCleaner`
3. Ejecutar manualmente limpieza

---

## 📈 Estadísticas

```
Sistema en Producción:
  Ciclos ejecutados: 1,247
  Archivos Bronce: 3,654
  Archivos Silver: 47 (1 por tabla)
  Datos procesados: 1.2M registros
  Tasa promedio de limpieza: 99.2%
```

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/mejora`)
3. Commit cambios (`git commit -am 'Agrega mejora'`)
4. Push a la rama (`git push origin feature/mejora`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**. Ver archivo [LICENSE](LICENSE) para detalles.

---

## 👤 Autor

**Andrews0212** - Sistema ETL Incremental

- GitHub: [@andrews0212](https://github.com/andrews0212)
- Email: contacto@ejemplo.com

---

## 📞 Soporte

¿Preguntas o problemas? Abre un [issue](https://github.com/andrews0212/Estacion_Meteorologica/issues) en GitHub.

---

**Última actualización**: 3 de Diciembre de 2025  
**Versión**: 3.0  
**Estado**: ✅ Producción
