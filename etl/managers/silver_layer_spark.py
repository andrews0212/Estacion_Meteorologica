"""etl.managers.silver_layer_spark

Implementación alternativa de la capa Silver usando PySpark.

Este módulo proporciona una versión basada en Spark para procesamiento
de datos en escala. Es una alternativa a la implementación con pandas
en :mod:`etl.managers.limpieza_bronce`.

Nota:
    Requiere PySpark instalado. Úsalo si necesitas procesamiento distribuido
    de grandes volúmenes de datos.
"""

import os
import tempfile
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, when
from minio import Minio
from etl.managers.silver_manager import SilverManager


class DataCleaner(ABC):
    """Clase abstracta para estrategias de limpieza de datos.
    
    Define interfaz para implementar lógicas de limpieza específicas
    por tabla usando PySpark.
    """
    
    @abstractmethod
    def clean(self, df: DataFrame) -> DataFrame:
        """Aplica limpieza específica al DataFrame.
        
        Args:
            df (pyspark.sql.DataFrame): DataFrame a limpiar
            
        Returns:
            pyspark.sql.DataFrame: DataFrame limpio
        """
        pass


class SensorReadingsCleaner(DataCleaner):
    """Limpieza especializada para tabla sensor_readings usando Spark.
    
    Implementa limpieza con PySpark para procesamiento distribuido:
    - Elimina duplicados
    - Reemplaza outliers
    - Elimina columnas innecesarias
    - Valida rangos
    """
    
    def __init__(self, outlier_factor: float = 1.5):
        """
        Inicializa limpiador de sensor_readings.
        
        Args:
            outlier_factor (float): Factor para cálculo de IQR (default: 1.5)
        """
        self.outlier_factor = outlier_factor
        self.columns_to_drop = ["uv_level", "vibration", "rain_raw", "wind_raw", "pressure"]
        self.validation_rules = {
            "temperature": (10, 50),
            "humidity": (0, 100)
        }
    
    def clean(self, df: DataFrame) -> DataFrame:
        """Aplica limpieza a sensor_readings.
        
        Args:
            df (pyspark.sql.DataFrame): DataFrame original
            
        Returns:
            pyspark.sql.DataFrame: DataFrame limpio
        """
        df = self._remove_duplicates(df)
        df = self._replace_outliers(df, "temperature")
        df = self._drop_unnecessary_columns(df)
        df = self._validate_values(df)
        return df
    
    def _remove_duplicates(self, df: DataFrame) -> DataFrame:
        """Elimina registros duplicados."""
        return df.distinct()
    
    def _replace_outliers(self, df: DataFrame, column: str) -> DataFrame:
        """Reemplaza outliers con mediana usando IQR.
        
        Args:
            df (pyspark.sql.DataFrame): DataFrame
            column (str): Nombre de la columna
            
        Returns:
            pyspark.sql.DataFrame: DataFrame con outliers reemplazados
        """
        if column not in df.columns:
            return df
        
        q1, q3, median = df.approxQuantile(column, [0.25, 0.75, 0.5], 0.05)
        iqr = q3 - q1
        lower_bound = q1 - (self.outlier_factor * iqr)
        upper_bound = q3 + (self.outlier_factor * iqr)
        
        return df.withColumn(
            column,
            when((col(column) < lower_bound) | (col(column) > upper_bound), median)
            .otherwise(col(column))
        )
    
    def _drop_unnecessary_columns(self, df: DataFrame) -> DataFrame:
        """Elimina columnas innecesarias.
        
        Args:
            df (pyspark.sql.DataFrame): DataFrame
            
        Returns:
            pyspark.sql.DataFrame: DataFrame sin columnas innecesarias
        """
        existing_cols = [c for c in self.columns_to_drop if c in df.columns]
        return df.drop(*existing_cols) if existing_cols else df
    
    def _validate_values(self, df: DataFrame) -> DataFrame:
        """Filtra valores válidos según reglas de validación.
        
        Args:
            df (pyspark.sql.DataFrame): DataFrame
            
        Returns:
            pyspark.sql.DataFrame: DataFrame filtrado
        """
        for column, (min_val, max_val) in self.validation_rules.items():
            if column in df.columns:
                df = df.filter((col(column) >= min_val) & (col(column) <= max_val))
        return df


class SilverLayerSpark:
    """Gestor de la capa Silver con PySpark para procesamiento distribuido.
    
    Procesa datos CSV de la capa Bronce, aplica transformaciones distribuidas
    y guarda en formato CSV en MinIO.
    
    Uso::
    
        from config import MinIOConfig
        from etl.managers.silver_layer_spark import SilverLayerSpark
        
        cfg = MinIOConfig()
        silver = SilverLayerSpark(cfg)
        resultado = silver.process('sensor_readings')
    
    Nota:
        Esta es una implementación alternativa basada en PySpark.
        Para la mayoría de casos, use :class:`etl.managers.limpieza_bronce.LimpiezaBronce`
        que usa pandas y es más ligera.
    """
    
    CLEANERS = {"sensor_readings": SensorReadingsCleaner()}
    
    def __init__(self, minio_config):
        """
        Inicializa la capa Silver.
        
        Args:
            minio_config (MinIOConfig): Configuración de MinIO
        """
        self.minio_config = minio_config
        self.minio_client = Minio(
            minio_config.endpoint,
            access_key=minio_config.access_key,
            secret_key=minio_config.secret_key,
            secure=False
        )
        self.silver_manager = SilverManager(minio_config)
        self.spark = self._initialize_spark()
        self._ensure_silver_bucket_exists()
    
    def _initialize_spark(self) -> SparkSession:
        """Inicializa o reutiliza SparkSession existente.
        
        Returns:
            pyspark.sql.SparkSession: Sesión de Spark
        """
        spark = SparkSession.getActiveSession()
        if spark is not None:
            return spark
        
        spark = SparkSession.builder \
            .appName("SilverLayer") \
            .master("local[*]") \
            .config("spark.driver.memory", "2g") \
            .config("spark.executor.memory", "2g") \
            .config("spark.sql.shuffle.partitions", "1") \
            .getOrCreate()
        
        spark.sparkContext.setLogLevel("WARN")
        return spark
    
    def _ensure_silver_bucket_exists(self) -> None:
        """Crea el bucket Silver si no existe."""
        bucket_silver = self._get_silver_bucket_name()
        
        try:
            if not self.minio_client.bucket_exists(bucket_silver):
                self.minio_client.make_bucket(bucket_silver)
                print(f"✅ Bucket Silver creado: {bucket_silver}")
            else:
                print(f"✅ Bucket Silver existe: {bucket_silver}")
        except Exception as e:
            print(f"❌ Error con bucket Silver: {e}")
    
    def _get_silver_bucket_name(self) -> str:
        """Obtiene el nombre del bucket Silver."""
        return self.minio_config.bucket.replace("-bronze", "-silver")
    
    def process(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Procesa una tabla completa: carga, limpia y guarda.
        Estrategia REPLACE: Elimina versiones antiguas automáticamente.
        
        Args:
            table_name (str): Nombre de la tabla
            
        Returns:
            dict | None: Diccionario con resultado o None si falla
        """
        try:
            print(f"\n{'='*80}")
            print(f"🧹 PROCESANDO CAPA SILVER (SPARK): {table_name}")
            print(f"{'='*80}")
            
            df = self._load_bronze_csv(table_name)
            if df is None:
                print(f"⚠️  No hay datos en Bronce: {table_name}")
                return None
            
            print(f"\n📥 Datos cargados desde Bronce:")
            print(f"   Filas: {df.count()}")
            print(f"   Columnas: {len(df.columns)}")
            
            df_clean = self._apply_cleaning(table_name, df)
            
            # Guardar en Silver
            if not self._save_to_silver(table_name, df_clean):
                return None
            
            # Limpiar versiones antiguas (estrategia REPLACE)
            print(f"\n🧹 Eliminando versiones antiguas...")
            self.silver_manager.limpiar_versiones_antiguas(table_name, mantener_actual=True)
            
            # Obtener estadísticas
            stats = self.silver_manager.obtener_estadisticas_tabla(table_name)
            
            resultado = {
                'tabla': table_name,
                'filas_limpias': df_clean.count(),
                'estrategia': 'REPLACE',
                'timestamp': datetime.now().isoformat(),
                'estadisticas': stats
            }
            
            print(f"\n✅ Procesamiento completado - Versiones activas: {stats.get('total_versiones', 1)}")
            return resultado
            
        except Exception as e:
            print(f"❌ Error en capa Silver: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _load_bronze_csv(self, table_name: str) -> Optional[DataFrame]:
        """Carga el CSV más reciente de Bronce.
        
        Args:
            table_name (str): Nombre de la tabla
            
        Returns:
            pyspark.sql.DataFrame | None: DataFrame o None si falla
        """
        try:
            files = self._list_bronze_files(table_name)
            if not files:
                return None
            
            latest_file = sorted(files)[-1]
            print(f"📄 Archivo Bronce: {latest_file}")
            
            temp_file = self._download_from_minio(latest_file)
            return self.spark.read.csv(temp_file, header=True, inferSchema=True)
            
        except Exception as e:
            print(f"❌ Error cargando Bronce: {e}")
            return None
    
    def _list_bronze_files(self, table_name: str) -> list:
        """Lista archivos CSV de una tabla en Bronce.
        
        Args:
            table_name (str): Nombre de la tabla
            
        Returns:
            list: Lista de nombres de objetos en MinIO
        """
        objects = self.minio_client.list_objects(
            self.minio_config.bucket,
            prefix=table_name,
            recursive=True
        )
        return [
            obj.object_name for obj in objects
            if obj.object_name.endswith('.csv') and '_bronce_' in obj.object_name
        ]
    
    def _download_from_minio(self, object_name: str) -> str:
        """Descarga un archivo de MinIO a temporal.
        
        Args:
            object_name (str): Nombre del objeto en MinIO
            
        Returns:
            str: Ruta absoluta al archivo temporal
        """
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, object_name.split('/')[-1])
        
        self.minio_client.fget_object(self.minio_config.bucket, object_name, temp_file)
        return temp_file
    
    def _apply_cleaning(self, table_name: str, df: DataFrame) -> DataFrame:
        """Aplica limpieza usando la estrategia apropiada.
        
        Args:
            table_name (str): Nombre de la tabla
            df (pyspark.sql.DataFrame): DataFrame original
            
        Returns:
            pyspark.sql.DataFrame: DataFrame limpio
        """
        print(f"\n🧹 Aplicando limpieza...")
        
        cleaner = self.CLEANERS.get(table_name)
        if cleaner:
            df = cleaner.clean(df)
        else:
            print(f"⚠️  Sin limpieza específica para {table_name}")
        
        print(f"✅ Datos limpios: {df.count()} filas")
        return df
    
    def _save_to_silver(self, table_name: str, df: DataFrame) -> bool:
        """Guarda el DataFrame en Silver como CSV.
        
        Args:
            table_name (str): Nombre de la tabla
            df (pyspark.sql.DataFrame): DataFrame a guardar
            
        Returns:
            bool: True si se guardó exitosamente
        """
        try:
            bucket_silver = self._get_silver_bucket_name()
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{table_name}_silver_{timestamp}.csv"
            
            temp_file = self._write_csv_to_temp(df, filename)
            self._upload_to_minio(bucket_silver, filename, temp_file, df)
            
            return True
            
        except Exception as e:
            print(f"❌ Error guardando en Silver: {e}")
            return False
    
    def _write_csv_to_temp(self, df: DataFrame, filename: str) -> str:
        """Escribe DataFrame a CSV temporal.
        
        Args:
            df (pyspark.sql.DataFrame): DataFrame
            filename (str): Nombre del archivo
            
        Returns:
            str: Ruta del archivo temporal
        """
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, filename)
        
        df.coalesce(1).write.mode("overwrite").option("header", "true").csv(temp_file)
        print(f"   💾 Archivo CSV creado: {filename}")
        
        return temp_file
    
    def _upload_to_minio(self, bucket: str, filename: str, temp_file: str, df: DataFrame) -> None:
        """Sube archivo a MinIO e imprime estadísticas.
        
        Args:
            bucket (str): Nombre del bucket
            filename (str): Nombre del archivo
            temp_file (str): Ruta del archivo temporal
            df (pyspark.sql.DataFrame): DataFrame (para obtener estadísticas)
        """
        self.minio_client.fput_object(bucket, filename, temp_file)
        
        file_size_mb = os.path.getsize(temp_file) / (1024 * 1024)
        print(f"   ✅ Subido a MinIO: {bucket}/{filename}")
        print(f"      Filas: {df.count()}")
        print(f"      Tamaño: {file_size_mb:.2f} MB")
        
        try:
            os.remove(temp_file)
        except:
            pass
