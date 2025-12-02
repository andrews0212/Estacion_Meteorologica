"""etl.managers.limpieza_bronce
=================================

Herramientas para procesar los CSV almacenados en la capa *Bronce* y
publicar resultados limpios en la capa *Silver*.

Principales responsabilidades:
- Buscar todos los CSV de una tabla en el bucket Bronce
- Descargar y combinar múltiples extracciones
- Aplicar limpieza específica por tabla (ej: `sensor_readings`)
- Guardar el resultado en Silver utilizando estrategia REPLACE
- Invocar a :class:`etl.managers.silver_manager.SilverManager` para gestionar versiones

El módulo está diseñado para trabajar con MinIO (S3 compatible) y pandas
para la fase de limpieza. Las funciones devuelven rutas temporales o
estructuras Python simples (dict) pensadas para registro/telemetría.
"""

import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List
from minio import Minio
import pandas as pd
from etl.managers.silver_manager import SilverManager


class LimpiezaBronce:
    """Limpia datos de la capa Bronce y los guarda en Silver.

    Uso básico:

    >>> from config import MinIOConfig
    >>> from etl.managers.limpieza_bronce import LimpiezaBronce
    >>> cfg = MinIOConfig()
    >>> cleaner = LimpiezaBronce(cfg)
    >>> resultado = cleaner.procesar_tabla('sensor_readings')

    Métodos principales
    - :meth:`obtener_archivos_tabla` : lista objetos Bronce
    - :meth:`combinar_csvs` : concatena múltiples CSV en un DataFrame
    - :meth:`limpiar_sensor_readings` : lógica de limpieza por tabla
    - :meth:`guardar_csv_como_parquet` : guarda y sube el CSV limpio
    - :meth:`procesar_tabla` : flujo completo (lista → combinar → limpiar → guardar)
    """
    
    def __init__(self, minio_config=None):
        """
        Inicializa la limpieza.
        
        Args:
            minio_config (MinIOConfig | None): Configuración de MinIO. Si es None,
                se carga la configuración por defecto desde config.MinIOConfig
        """
        if minio_config is None:
            from config import MinIOConfig
            minio_config = MinIOConfig()
        
        self.minio_config = minio_config
        self.minio_endpoint = minio_config.endpoint
        self.minio_access = minio_config.access_key
        self.minio_secret = minio_config.secret_key
        self.bucket_bronce = minio_config.bucket
        self.bucket_silver = self.bucket_bronce.replace('-bronze', '-silver')
        
        # Crear cliente MinIO
        self.client = Minio(
            self.minio_endpoint,
            access_key=self.minio_access,
            secret_key=self.minio_secret,
            secure=False
        )
        
        # Gestor de Silver (para limpiar versiones antiguas)
        self.silver_manager = SilverManager(minio_config)
    
    def obtener_archivos_tabla(self, tabla: str) -> Optional[List[str]]:
        """Obtiene TODOS los archivos CSV de una tabla (puede haber múltiples extracciones).
        
        Args:
            tabla (str): Nombre de la tabla a procesar
            
        Returns:
            list | None: Lista de nombres de objetos en MinIO o None si hay error
        """
        try:
            objects = self.client.list_objects(self.bucket_bronce, prefix=tabla, recursive=True)
            
            archivos = []
            for obj in objects:
                if obj.object_name.endswith('.csv') and '_bronce_' in obj.object_name:
                    archivos.append(obj.object_name)
            
            if not archivos:
                return None
            
            # Ordenar por timestamp (están en el nombre)
            archivos_ordenados = sorted(archivos)
            print(f"[INFO] Encontrados {len(archivos_ordenados)} archivo(s) de {tabla}")
            for archivo in archivos_ordenados:
                print(f"       - {archivo}")
            
            return archivos_ordenados
            
        except Exception as e:
            print(f"[ERROR] Error listando archivos: {e}")
            return None
    
    def descargar_csv(self, archivo: str) -> Optional[str]:
        """Descarga el CSV de MinIO a un fichero temporal.

        Args:
            archivo (str): Ruta/objeto en el bucket (ej: 'sensor_readings/sensor_readings_bronce_...csv')

        Returns:
            str | None: Ruta absoluta al fichero temporal descargado, o ``None`` en caso de error.
        """
        try:
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, archivo.split('/')[-1])
            
            self.client.fget_object(self.bucket_bronce, archivo, temp_file)
            return temp_file
            
        except Exception as e:
            print(f"[ERROR] Error descargando: {e}")
            return None
    
    def combinar_csvs(self, archivos: List[str]) -> Optional[pd.DataFrame]:
        """Combina múltiples CSVs (lista de objetos en MinIO) en un único pandas.DataFrame.

        El método descarga cada CSV a un fichero temporal, lo lee con
        ``pandas.read_csv`` y concatena todos los frames respetando
        el orden ascendente de archivos (se asume que el timestamp está
        presente en el nombre del archivo).

        Args:
            archivos (list): Lista de nombres de objetos en MinIO (strings)

        Returns:
            pd.DataFrame | None: DataFrame combinado o ``None`` si no se encontraron datos.
        """
        try:
            dataframes = []
            
            for archivo in archivos:
                temp_file = self.descargar_csv(archivo)
                if temp_file:
                    df = pd.read_csv(temp_file)
                    dataframes.append(df)
                    print(f"[OK] Cargado: {archivo.split('/')[-1]} ({len(df)} filas)")
            
            if not dataframes:
                return None
            
            # Combinar todos los DataFrames
            df_combinado = pd.concat(dataframes, ignore_index=True)
            print(f"[OK] DataFrames combinados: {len(df_combinado)} filas totales")
            
            return df_combinado
            
        except Exception as e:
            print(f"[ERROR] Error combinando CSVs: {e}")
            return None
    
    def limpiar_sensor_readings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica limpieza específica para la tabla ``sensor_readings``.

        Reglas implementadas:
        - Eliminar duplicados exactos
        - Reemplazar outliers en ``temperature`` por la mediana (IQR)
        - Eliminar columnas irrelevantes
        - Filtrar rangos válidos para ``temperature`` y ``humidity``

        Args:
            df (pd.DataFrame): DataFrame original con columnas típicas de sensores
                como ``temperature``, ``humidity``, etc.

        Returns:
            pd.DataFrame: DataFrame limpio.

        Ejemplo::

            from etl.managers.limpieza_bronce import LimpiezaBronce
            cleaner = LimpiezaBronce()
            df_clean = cleaner.limpiar_sensor_readings(df_raw)

        Notas:
            - Se asume que ``temperature`` y ``humidity`` están en unidades esperadas.
            - Los outliers en ``temperature`` se reemplazan por la mediana calculada
              sobre los valores no nulos.
        """
        filas_orig = len(df)
        
        # 1. Eliminar duplicados
        df = df.drop_duplicates()
        filas_sin_dup = len(df)
        print(f"[OK] Duplicados eliminados: {filas_orig} → {filas_sin_dup}")
        
        # 2. Reemplazar outliers en temperatura con mediana
        if 'temperature' in df.columns:
            temp = df['temperature'].dropna()
            q1 = temp.quantile(0.25)
            q3 = temp.quantile(0.75)
            mediana = temp.quantile(0.50)
            iqr = q3 - q1
            
            limite_inf = q1 - (1.5 * iqr)
            limite_sup = q3 + (1.5 * iqr)
            
            outliers = ((df['temperature'] < limite_inf) | (df['temperature'] > limite_sup)).sum()
            df.loc[(df['temperature'] < limite_inf) | (df['temperature'] > limite_sup), 'temperature'] = mediana
            print(f"[OK] Outliers en temperature: {outliers} reemplazados con mediana ({mediana:.2f})")
        
        # 3. Eliminar columnas innecesarias
        cols_eliminar = ['uv_level', 'vibration', 'rain_raw', 'wind_raw', 'pressure']
        for col in cols_eliminar:
            if col in df.columns:
                df = df.drop(col, axis=1)
        print(f"[OK] Columnas innecesarias eliminadas")
        
        # 4. Filtrar valores válidos
        filas_antes_filtrado = len(df)
        if 'temperature' in df.columns:
            df = df[(df['temperature'] >= 10) & (df['temperature'] <= 50)]
        
        if 'humidity' in df.columns:
            df = df[(df['humidity'] >= 0) & (df['humidity'] <= 100)]
        
        filas_filtradas = filas_antes_filtrado - len(df)
        print(f"[OK] Valores inválidos filtrados: {filas_filtradas} eliminadas → {len(df)} filas finales")
        
        return df
    
    def guardar_csv_como_parquet(self, df: pd.DataFrame, tabla: str) -> Optional[str]:
        """Guarda el DataFrame como CSV en el bucket Silver.

        Nombre generado: ``{tabla}_silver_{YYYYmmddHHMMSS}.csv``.

        Args:
            df (pd.DataFrame): DataFrame a guardar en Silver.
            tabla (str): Nombre lógico de la tabla.

        Returns:
            str | None: Nombre del archivo subido en Silver (p. ej. ``sensor_readings_silver_20250101120000.csv``)
                o ``None`` en caso de error.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            archivo_silver = f"{tabla}_silver_{timestamp}.csv"
            
            # Guardar temporalmente
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, archivo_silver)
            
            df.to_csv(temp_file, index=False)
            
            # Subir a MinIO
            self.client.fput_object(self.bucket_silver, archivo_silver, temp_file)
            
            # Limpiar temporal
            try:
                os.remove(temp_file)
            except:
                pass
            
            return archivo_silver
            
        except Exception as e:
            print(f"[ERROR] Error guardando CSV: {e}")
            return None
    
    def procesar_tabla(self, tabla: str) -> Optional[Dict[str, Any]]:
        """
        Procesa una tabla: obtiene CSVs de Bronce, limpia y guarda en Silver.
        Estrategia REPLACE: Elimina versiones antiguas automáticamente.
        
        Args:
            tabla (str): Nombre de la tabla a procesar
            
        Returns:
            dict | None: Diccionario con resultado del procesamiento o None si hay error
            
        Ejemplo::
        
            from etl.managers.limpieza_bronce import LimpiezaBronce
            cleaner = LimpiezaBronce()
            resultado = cleaner.procesar_tabla('sensor_readings')
            if resultado:
                print(f"Procesadas {resultado['filas_limpias']} filas")
        """
        try:
            print(f"\n{'='*80}")
            print(f"[PROCESO] Limpiando {tabla}")
            print(f"{'='*80}")
            
            # 1. Obtener TODOS los archivos de la tabla
            archivos = self.obtener_archivos_tabla(tabla)
            if not archivos:
                print(f"[AVISO] No hay archivos para procesar de {tabla}")
                return None
            
            # 2. Combinar todos los CSVs
            print(f"\n[INFO] Combinando {len(archivos)} archivo(s)...")
            df = self.combinar_csvs(archivos)
            if df is None or len(df) == 0:
                print(f"[ERROR] No se pudo combinar los datos")
                return None
            
            filas_limpias = len(df)
            
            # 3. Limpiar según tabla
            print(f"\n[INFO] Limpiando datos...")
            if tabla == 'sensor_readings':
                df = self.limpiar_sensor_readings(df)
            else:
                print(f"[AVISO] No hay limpieza específica para {tabla}")
            
            # 4. Guardar como CSV
            print(f"\n[INFO] Guardando en Silver (estrategia REPLACE)...")
            archivo_nuevo = self.guardar_csv_como_parquet(df, tabla)
            
            if not archivo_nuevo:
                return None
            
            # 5. Limpiar versiones antiguas (estrategia REPLACE)
            print(f"\n[INFO] Eliminando versiones antiguas...")
            self.silver_manager.limpiar_versiones_antiguas(tabla, mantener_actual=True)
            
            # 6. Obtener estadísticas
            stats = self.silver_manager.obtener_estadisticas_tabla(tabla)
            
            resultado = {
                'tabla': tabla,
                'filas_limpias': len(df),
                'archivo_silver': archivo_nuevo,
                'estrategia': 'REPLACE',
                'timestamp': datetime.now().isoformat(),
                'estadisticas': stats
            }
            
            print(f"\n[EXITO] {tabla}: {len(df)} filas guardadas en Silver")
            print(f"[INFO] Archivo: {archivo_nuevo}")
            print(f"[INFO] Versiones activas: {stats.get('total_versiones', 1)}")
            
            return resultado
            
        except Exception as e:
            print(f"[ERROR] Error procesando {tabla}: {e}")
            import traceback
            traceback.print_exc()
            return None
