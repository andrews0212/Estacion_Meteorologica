"""Base abstracta para gestores de capas (Silver, Gold) en MinIO.

Proporciona funcionalidad común para administrar archivos en buckets de capas,
eliminando redundancia entre SilverManager y GoldManager.

Funcionalidades:
- Listar versiones históricas de archivos por tabla
- Obtener versión más reciente
- Eliminar versiones antiguas (estrategia REPLACE)
- Calcular estadísticas de almacenamiento
"""

from typing import List, Optional, Dict, Any
from minio import Minio


class LayerManager:
    """Gestor base para capas de datos (Silver, Gold, etc) en MinIO.
    
    Implementa operaciones comunes para gestionar versiones de archivos en buckets:
    - Listar archivos por tabla con rastreo de versiones
    - Limpiar versiones antiguas (mantener solo la más reciente)
    - Calcular estadísticas de uso de almacenamiento
    
    Estrategia de versiones: **REPLACE**
    - Sobrescribe versiones antiguas con nuevas automáticamente
    - Mantiene solo los datos más recientes de cada tabla
    - Optimiza espacio de almacenamiento
    
    Args:
        minio_config: Configuración de MinIO
        bucket_suffix: Sufijo del bucket (ej: '-silver' para 'meteo-silver', '-gold' para 'meteo-gold')
    """
    
    def __init__(self, minio_config, bucket_suffix: str):
        """
        Inicializa el gestor de capa.
        
        Args:
            minio_config: Configuración de MinIO (tipo MinIOConfig)
            bucket_suffix: Sufijo del bucket para esta capa (ej: '-silver', '-gold')
            
        Note:
            El bucket se construye reemplazando '-bronze' por el sufijo en el bucket
            configurado (ej: 'meteo-bronze' → 'meteo-silver')
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
        Obtiene historial de versiones de una tabla (todos los archivos CSV).
        
        Args:
            tabla: Nombre de la tabla (ej: 'sensor_readings')
            
        Returns:
            List[str]: Lista de nombres de archivos ordenados cronológicamente (antiguos → recientes)
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
        Obtiene el archivo más reciente de una tabla (última versión).
        
        Args:
            tabla: Nombre de la tabla
            
        Returns:
            Optional[str]: Nombre del archivo más reciente o None si no existe
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
        """
        Limpia versiones antiguas según estrategia REPLACE.

        Workflow:
        - Si `mantener_actual=True`: Elimina todas menos la más reciente (recomendado)
        - Si `mantener_actual=False`: Elimina todas las versiones

        Args:
            tabla: Nombre de la tabla (ej: 'sensor_readings')
            mantener_actual: Si True, mantiene la versión más reciente

        Returns:
            int: Cantidad de archivos eliminados
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
        Calcula estadísticas de almacenamiento para una tabla.
        
        Args:
            tabla: Nombre de la tabla
            
        Returns:
            Dict con claves:
            - tabla: Nombre de la tabla
            - total_versiones: Cantidad de versiones almacenadas
            - version_antigua: Nombre del archivo más antiguo
            - version_reciente: Nombre del archivo más reciente
            - espacio_total_mb: Tamaño total en megabytes
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
