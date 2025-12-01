import pandas as pd
from sqlalchemy import create_engine, text
import subprocess
from datetime import datetime
import os
import time

# --- CONFIGURACIÓN ---
# Parametros que coje de nuestro sistema linux
DB_USER = os.environ.get('PG_USER', 'usuario')
DB_PASS = os.environ.get('PG_PASS', 'password')
DB_HOST = os.environ.get('PG_HOST', 'localhost')
DB_NAME = os.environ.get('PG_DB', 'basedatos')
MINIO_ALIAS = os.environ.get('MINIO_ALIAS', 'myminio')
MINIO_BUCKET = os.environ.get('MINIO_BUCKET', 'meteo-bronze')

# Url para hacer la conexión a la base de datos
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

# Crear motor de conexión
engine = create_engine(DATABASE_URL)

# crear tabla de control si no existe para llevar el seguimiento de extracciones
def initialize_control_table(connection):
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS etl_control (
            table_name VARCHAR(255) PRIMARY KEY,
            last_extracted_value VARCHAR(255),
            last_extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tracking_column VARCHAR(255)
        )
    """))
    connection.commit()

# Obtener columnas de una tabla
def get_table_columns(connection, table_name):
    """Devuelve lista de diccionarios con info de columnas."""
    query = text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = :table_name 
        AND table_schema = 'public'
        ORDER BY ordinal_position
    """)
    return connection.execute(query, {"table_name": table_name}).fetchall()

# Detectar columna de rastreo
def detect_tracking_column(connection, table_name):
    """
    Intenta detectar columna incremental en este orden:
    1. Timestamps (created_at, etc)
    2. Primary Key de la base de datos (infalible para IDs)
    3. Columnas que parezcan ID
    """
    columns = get_table_columns(connection, table_name)
    
    # 1. Buscar Timestamps
    timestamp_candidates = ['created_at', 'updated_at', 'timestamp', 'fecha_registro', 'last_update']
    for col_name, col_type in columns:
        if col_name.lower() in timestamp_candidates or 'timestamp' in col_type.lower():
            return col_name, 'timestamp'
    
    # 2. Buscar PRIMARY KEY real en Postgres (La mejor opción para IDs)
    pk_query = text("""
        SELECT ccu.column_name
        FROM information_schema.table_constraints tc 
        JOIN information_schema.constraint_column_usage ccu 
          ON tc.constraint_name = ccu.constraint_name 
        WHERE tc.constraint_type = 'PRIMARY KEY' 
          AND tc.table_name = :table_name
        LIMIT 1
    """)
    pk_result = connection.execute(pk_query, {"table_name": table_name}).fetchone()
    
    if pk_result:
        pk_col = pk_result[0]
        # Verificar que la PK sea numérica (para poder hacer > last_value)
        for col_name, col_type in columns:
            if col_name == pk_col and ('int' in col_type.lower() or 'serial' in col_type.lower() or 'numeric' in col_type.lower()):
                return pk_col, 'id'

    # 3. Último recurso: Buscar por nombre 'id' genérico
    for col_name, col_type in columns:
        if col_name.lower() == 'id' and ('int' in col_type.lower() or 'serial' in col_type.lower()):
            return col_name, 'id'
            
    return None, None


# Obtener último valor extraído de la tabla de control 
def get_last_extracted_value(connection, table_name):
    query = text("SELECT last_extracted_value, tracking_column FROM etl_control WHERE table_name = :table_name")
    result = connection.execute(query, {"table_name": table_name}).fetchone()
    if result:
        return result[0], result[1]
    return None, None

def update_last_extracted_value(connection, table_name, value, tracking_column):
    # Formatear valor
    if isinstance(value, (pd.Timestamp, datetime)):
        value_str = value.isoformat()
    else:
        value_str = str(value)

    upsert_query = text("""
        INSERT INTO etl_control (table_name, last_extracted_value, tracking_column, last_extracted_at)
        VALUES (:table_name, :val, :col, CURRENT_TIMESTAMP)
        ON CONFLICT (table_name) 
        DO UPDATE SET 
            last_extracted_value = :val,
            last_extracted_at = CURRENT_TIMESTAMP,
            tracking_column = :col
    """)
    connection.execute(upsert_query, {"table_name": table_name, "val": value_str, "col": tracking_column})
    connection.commit()

def process_batch():
    """Procesa un lote de todas las tablas."""
    print(f"\n--- INICIO DE BATCH: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    try:
        with engine.connect() as connection:
            initialize_control_table(connection)
            
            # Obtener tablas (excluyendo la de control)
            tables = connection.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            )).fetchall()
            tables = [t[0] for t in tables if t[0] != 'etl_control']
            
            total_records_batch = 0
            
            for table_name in tables:
                print(f"\nProcesando tabla: {table_name}")
                
                tracking_column, tracking_type = detect_tracking_column(connection, table_name)
                
                # --- CORRECCIÓN CRÍTICA ---
                # Si no hay columna de rastreo, SALTAMOS la tabla.
                # No descargamos todo ("SELECT *") porque eso causa el bucle infinito.
                if not tracking_column:
                    print(f"⚠️  SKIPPING: No se detectó columna incremental (ID numérico o Timestamp).")
                    
                    # DEBUG: Mostrar qué columnas tiene la tabla para entender por qué falla
                    cols = get_table_columns(connection, table_name)
                    col_names = [f"{c[0]}({c[1]})" for c in cols]
                    print(f"   🔎 Columnas disponibles: {', '.join(col_names)}")
                    continue
                
                # Lógica Incremental
                last_value, stored_column = get_last_extracted_value(connection, table_name)
                
                # Si cambió la columna de rastreo en la BD vs código, resetear
                if stored_column and stored_column != tracking_column:
                    last_value = None

                df = pd.DataFrame()
                
                if last_value:
                    print(f"   📊 Incremental ({tracking_column}) > {last_value}")
                    query = text(f"SELECT * FROM {table_name} WHERE {tracking_column} > :val ORDER BY {tracking_column} ASC LIMIT 10000")
                    df = pd.read_sql(query, connection, params={"val": last_value})
                else:
                    print(f"   🆕 Carga Inicial ({tracking_column})")
                    query = text(f"SELECT * FROM {table_name} ORDER BY {tracking_column} ASC LIMIT 10000")
                    df = pd.read_sql(query, connection)

                if df.empty:
                    print("   ✓ No hay datos nuevos.")
                    continue

                count = len(df)
                total_records_batch += count
                print(f"   📦 Registros nuevos: {count}")

                # Guardar Parquet
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                file_name = f"{table_name}_{timestamp}.parquet"
                local_path = f"/tmp/{file_name}"
                df.to_parquet(local_path, index=False)

                # Subir MinIO
                minio_path = f"{MINIO_ALIAS}/{MINIO_BUCKET}/{table_name}/{file_name}"
                try:
                    subprocess.run(["mc", "cp", local_path, minio_path], check=True, capture_output=True)
                    print(f"   ✅ Subido a MinIO: {file_name}")
                    
                    # Actualizar control
                    max_val = df[tracking_column].max()
                    update_last_extracted_value(connection, table_name, max_val, tracking_column)
                    
                except Exception as e:
                    print(f"   ❌ Error subiendo a MinIO: {e}")
                
                if os.path.exists(local_path):
                    os.remove(local_path)

            print(f"\n🎯 RESUMEN: {total_records_batch} registros nuevos en este batch.")

    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN CONEXIÓN: {e}")

if __name__ == "__main__":
    while True:
        process_batch()
        print("Esperando 10 segundos...")
        time.sleep(10)DB_USER = os.environ.get('PG_USER', 'usuario')
DB_PASS = os.environ.get('PG_PASS', 'password')
DB_HOST = os.environ.get('PG_HOST', 'localhost')
DB_NAME = os.environ.get('PG_DB', 'basedatos')
MINIO_ALIAS = os.environ.get('MINIO_ALIAS', 'myminio')
MINIO_BUCKET = os.environ.get('MINIO_BUCKET', 'meteo-bronze')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DATABASE_URL)