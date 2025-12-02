"""
Gestor de archivos Silver: Elimina versiones antiguas automáticamente.
Estrategia REPLACE: Siempre mantiene solo el dataset más reciente.
"""

from typing import List, Optional
from minio import Minio
import os


class SilverManager:
    """Gestiona archivos en capa Silver - Limpia versiones antiguas."""
    
    def __init__(self, minio_config):
        """
        Inicializa el gestor de Silver.
        
        Args:
            minio_config: Configuración de MinIO (MinIOConfig)
        """
        self.endpoint = minio_config.endpoint
        self.access_key = minio_config.access_key
        self.secret_key = minio_config.secret_key
        self.bucket_bronze = minio_config.bucket
        self.bucket_silver = self.bucket_bronze.replace('-bronze', '-silver')
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=False
        )
    
    def obtener_versiones_tabla(self, tabla: str) -> List[str]:
        """
        Obtiene TODOS los archivos Silver de una tabla, ordenados por fecha.
        
        Args:
            tabla: Nombre de la tabla (ej: 'sensor_readings')
            
        Returns:
            Lista de nombres de archivos ordenados (antiguos → recientes)
        """
        try:
            objects = self.client.list_objects(self.bucket_silver, prefix=tabla, recursive=True)
            
            archivos = []
            for obj in objects:
                if obj.object_name.endswith('.csv') and '_silver_' in obj.object_name:
                    archivos.append(obj.object_name)
            
            return sorted(archivos)
            
        except Exception as e:
            print(f"[ERROR] Error obteniendo versiones: {e}")
            return []
    
    def obtener_archivo_reciente(self, tabla: str) -> Optional[str]:
        """
        Obtiene el archivo Silver más reciente de una tabla.
        
        Args:
            tabla: Nombre de la tabla
            
        Returns:
            Nombre del archivo más reciente o None
        """
        versiones = self.obtener_versiones_tabla(tabla)
        return versiones[-1] if versiones else None
    
    def eliminar_archivo(self, tabla: str, archivo: str) -> bool:
        """
        Elimina un archivo específico de Silver.
        
        Args:
            tabla: Nombre de la tabla
            archivo: Nombre del archivo a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            self.client.remove_object(self.bucket_silver, archivo)
            print(f"[OK] Eliminado: {archivo}")
            return True
        except Exception as e:
            print(f"[ERROR] Error eliminando {archivo}: {e}")
            return False
    
    def limpiar_versiones_antiguas(self, tabla: str, mantener_actual: bool = True) -> int:
        """
        Elimina TODOS los archivos Silver antiguos excepto el más reciente.
        Estrategia REPLACE: Solo mantiene el dataset actual.
        
        Args:
            tabla: Nombre de la tabla
            mantener_actual: Si True, mantiene solo el más reciente (default: True)
            
        Returns:
            Cantidad de archivos eliminados
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
                if self.eliminar_archivo(tabla, archivo):
                    eliminados += 1
            
            print(f"[OK] {tabla}: {eliminados} archivos eliminados (mantiene: {archivo})")
            return eliminados
            
        except Exception as e:
            print(f"[ERROR] Error limpiando versiones: {e}")
            return 0
    
    def obtener_estadisticas_tabla(self, tabla: str) -> dict:
        """
        Obtiene estadísticas de versiones de una tabla.
        
        Args:
            tabla: Nombre de la tabla
            
        Returns:
            Diccionario con estadísticas
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
                    stat = self.client.stat_object(self.bucket_silver, archivo)
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
