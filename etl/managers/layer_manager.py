"""Base abstracta para gestores de capas (Silver, Gold, etc).

Elimina redundancia entre SilverManager y GoldManager proporcionando
una clase base con funcionalidades comunes.
"""

from typing import List, Optional, Dict, Any
from minio import Minio


class LayerManager:
    """Clase base para gestores de capas (Silver, Gold, etc).
    
    Implementa funcionalidades comunes para listar, eliminar y gestionar
    versiones de archivos en buckets de MinIO.
    
    Args:
        minio_config: Configuración de MinIO
        bucket_suffix: Sufijo del bucket (ej: '-silver' para bucket 'meteo-silver')
        
    Ejemplo::
    
        from config import MinIOConfig
        cfg = MinIOConfig()
        manager = LayerManager(cfg, '-silver')
        versiones = manager.obtener_versiones_tabla('sensor_readings')
    """
    
    def __init__(self, minio_config, bucket_suffix: str):
        """
        Inicializa el gestor de capa.
        
        Args:
            minio_config: Configuración de MinIO (MinIOConfig)
            bucket_suffix: Sufijo del bucket (ej: '-silver', '-gold')
        """
        self.endpoint = minio_config.endpoint
        self.access_key = minio_config.access_key
        self.secret_key = minio_config.secret_key
        self.bucket_bronze = minio_config.bucket
        self.bucket_layer = self.bucket_bronze.replace('-bronze', bucket_suffix)
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=getattr(minio_config, 'secure', False)
        )
    
    def obtener_versiones_tabla(self, tabla: str) -> List[str]:
        """
        Obtiene TODOS los archivos de una tabla en la capa, ordenados por fecha.
        
        Args:
            tabla (str): Nombre de la tabla (ej: ``sensor_readings``, ``metricas_kpi``).
            
        Returns:
            List[str]: Lista de nombres de archivos ordenados (antiguos → recientes).
        """
        try:
            objects = self.client.list_objects(self.bucket_layer, prefix=tabla, recursive=True)
            
            archivos = []
            for obj in objects:
                if obj.object_name.endswith('.csv'):
                    archivos.append(obj.object_name)
            
            return sorted(archivos)
            
        except Exception as e:
            print(f"[ERROR] Error obteniendo versiones de {tabla}: {e}")
            return []
    
    def obtener_archivo_reciente(self, tabla: str) -> Optional[str]:
        """
        Obtiene el archivo más reciente de una tabla.
        
        Args:
            tabla (str): Nombre de la tabla.
            
        Returns:
            Optional[str]: Nombre del archivo más reciente o None.
        """
        versiones = self.obtener_versiones_tabla(tabla)
        return versiones[-1] if versiones else None
    
    def eliminar_archivo(self, archivo: str) -> bool:
        """
        Elimina un archivo específico de la capa.
        
        Args:
            archivo (str): Nombre del archivo a eliminar.
            
        Returns:
            bool: True si se eliminó correctamente.
        """
        try:
            self.client.remove_object(self.bucket_layer, archivo)
            print(f"[OK] Eliminado: {archivo}")
            return True
        except Exception as e:
            print(f"[ERROR] Error eliminando {archivo}: {e}")
            return False
    
    def limpiar_versiones_antiguas(self, tabla: str, mantener_actual: bool = True) -> int:
        """Elimina archivos antiguos según la estrategia REPLACE.

        Args:
            tabla (str): Nombre de la tabla (p. ej. ``sensor_readings``, ``metricas_kpi``).
            mantener_actual (bool): Si ``True`` mantiene solo la versión más reciente;
                si ``False`` elimina todas las versiones.

        Returns:
            int: Cantidad de archivos eliminados.

        Ejemplo::

            manager = LayerManager(cfg, '-silver')
            removed = manager.limpiar_versiones_antiguas('sensor_readings')
            print(f"Archivos eliminados: {removed}")
        """
        try:
            versiones = self.obtener_versiones_tabla(tabla)
            
            if len(versiones) <= 1:
                print(f"[INFO] {tabla}: Solo 1 versión presente, nada que limpiar")
                return 0
            
            if mantener_actual:
                # Eliminar todos excepto el último
                archivos_a_eliminar = versiones[:-1]
                print(f"[INFO] {tabla}: Eliminando {len(archivos_a_eliminar)} versiones antiguas")
            else:
                # Eliminar todos
                archivos_a_eliminar = versiones
                print(f"[INFO] {tabla}: Eliminando todas las versiones")
            
            eliminados = 0
            for archivo in archivos_a_eliminar:
                if self.eliminar_archivo(archivo):
                    eliminados += 1
            
            if eliminados > 0 and mantener_actual:
                print(f"[OK] {tabla}: {eliminados} archivos eliminados (mantiene: {versiones[-1]})")
            return eliminados
            
        except Exception as e:
            print(f"[ERROR] Error limpiando versiones: {e}")
            return 0
    
    def obtener_estadisticas_tabla(self, tabla: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de versiones de una tabla.
        
        Args:
            tabla (str): Nombre de la tabla.
            
        Returns:
            Dict[str, Any]: Diccionario con estadísticas (tabla, total_versiones, versión_antigua, 
            versión_reciente, espacio_total_mb).
        """
        try:
            versiones = self.obtener_versiones_tabla(tabla)
            
            if not versiones:
                return {
                    'tabla': tabla,
                    'total_versiones': 0,
                    'version_reciente': None,
                    'espacio_total_mb': 0
                }
            
            # Calcular espacio total
            espacio_total = 0
            for archivo in versiones:
                try:
                    stat = self.client.stat_object(self.bucket_layer, archivo)
                    espacio_total += stat.size
                except:
                    pass
            
            return {
                'tabla': tabla,
                'total_versiones': len(versiones),
                'version_antigua': versiones[0],
                'version_reciente': versiones[-1],
                'espacio_total_mb': round(espacio_total / (1024 * 1024), 2)
            }
            
        except Exception as e:
            print(f"[ERROR] Error obteniendo estadísticas: {e}")
            return {}
