import psycopg2
import random
from datetime import datetime, timedelta
import math

# --- CONFIGURACIÓN DE CONEXIÓN ---
DB_HOST = "10.202.50.50"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "1234"
DB_PORT = "5432"

# AUMENTAMOS LOS REGISTROS: 1000 es muy poco para un año. 
# 5000 registros aseguran unos ~13 datos por día.
TOTAL_RECORDS = 5000 
IP_SENSOR = '192.168.1.50'

# --- CAMBIO 1: RANGO DE FECHAS DE 1 AÑO ---
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=365) # Últimos 365 días

def create_table_if_not_exists(cursor):
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensor_readings (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP,
        ip VARCHAR(20),
        temperature DOUBLE PRECISION,
        humidity DOUBLE PRECISION,
        pm25 INTEGER,
        light INTEGER,
        uv_level INTEGER,
        pressure DOUBLE PRECISION,
        rain_raw INTEGER,
        wind_raw INTEGER,
        vibration BOOLEAN
    );
    ''')

def generate_random_timestamp(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + timedelta(seconds=random_second)

def generate_sensor_data():
    ts = generate_random_timestamp(START_DATE, END_DATE)
    hour = ts.hour
    month = ts.month # Obtenemos el mes para simular clima
    
    # Lógica Día/Noche
    is_day = 7 <= hour <= 19
    is_raining = random.random() < 0.10
    
    # --- CAMBIO 2: SIMULACIÓN DE ESTACIONES (Para que el gráfico no sea plano) ---
    # Hemisferio Norte aprox: Ene/Feb frío, Jul/Ago calor
    seasonal_offset = 0
    if month in [12, 1, 2]: # Invierno
        seasonal_offset = -5
    elif month in [3, 4, 5]: # Primavera
        seasonal_offset = 2
    elif month in [6, 7, 8]: # Verano
        seasonal_offset = 8
    elif month in [9, 10, 11]: # Otoño
        seasonal_offset = 1

    base_temp = (15 + seasonal_offset) if is_day else (8 + seasonal_offset)
    
    if is_raining: base_temp -= 3
    
    # Generar temperatura con la variación estacional
    temperature = round(random.uniform(base_temp - 5, base_temp + 10), 2)
    
    # Humedad (Suele ser más baja en verano si es clima seco, o alta si es tropical)
    # Aquí lo dejamos aleatorio pero influenciado por la lluvia
    if is_raining:
        humidity = round(random.uniform(85.0, 99.9), 1)
    else:
        # En verano un poco más seco, en invierno más húmedo (ejemplo)
        hum_offset = -10 if month in [6,7,8] else 0
        humidity = round(random.uniform(30.0, 80.0 + hum_offset), 1)
        # Asegurar límites
        humidity = max(0, min(100, humidity))

    if is_day:
        light = random.randint(1000, 65000) if not is_raining else random.randint(500, 5000)
        # UV más alto en verano
        max_uv = 11 if month in [5,6,7,8] else 5
        uv_level = random.randint(1, max_uv) if not is_raining else random.randint(0, 2)
    else:
        light = 0
        uv_level = 0
        
    pressure = random.randint(990, 1005) if is_raining else random.randint(1010, 1030)
    
    rain_raw = random.randint(100, 800) if is_raining else 0
    wind_raw = random.randint(0, 300)
    if is_raining: wind_raw += random.randint(50, 200)
    
    pm25 = random.randint(5, 150)
    if is_raining: pm25 = int(pm25 * 0.2)
    
    vibration = True

    return (ts, IP_SENSOR, temperature, humidity, pm25, light, uv_level, pressure, rain_raw, wind_raw, vibration)

def main():
    print(f"--- Conectando a PostgreSQL en {DB_HOST}... ---")
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cursor = conn.cursor()
        
        create_table_if_not_exists(cursor)
        conn.commit() 
        
        print(f"Generando {TOTAL_RECORDS} registros distribuidos en el último AÑO...")
        data_batch = []
        for _ in range(TOTAL_RECORDS):
            data_batch.append(generate_sensor_data())
            
        query = """
        INSERT INTO sensor_readings 
        (timestamp, ip, temperature, humidity, pm25, light, uv_level, pressure, rain_raw, wind_raw, vibration) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.executemany(query, data_batch)
        conn.commit()
        
        print(f"¡Éxito! {TOTAL_RECORDS} registros insertados cubriendo 12 meses.")
        
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()