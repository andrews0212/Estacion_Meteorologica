import os
from typing import Optional


class Config:
    """Clase base para todas las configuraciones."""
    
    @staticmethod
    def get_env(key: str, default: Optional[str] = None) -> str:
        """
        Obtiene variable de entorno con validación.
        
        Args:
            key: Nombre de la variable de entorno
            default: Valor por defecto si no existe
            
        Returns:
            Valor de la variable o default
        """
        value = os.environ.get(key, default)
        if value is None:
            raise ValueError(f"Variable de entorno requerida no encontrada: {key}")
        return value


class DatabaseConfig(Config):
    """Configuración de PostgreSQL con validación."""
    
    def __init__(self, 
                 user: Optional[str] = None,
                 password: Optional[str] = None,
                 host: Optional[str] = None,
                 database: Optional[str] = None):
        """
        Inicializa configuración de BD.
        
        Lee de variables de entorno si no se proporcionan argumentos.
        """
        self.user = user or self.get_env('PG_USER', 'postgres')
        self.password = password or self.get_env('PG_PASS', 'postgres')
        self.host = host or self.get_env('PG_HOST', 'localhost')
        self.database = database or self.get_env('PG_DB', 'postgres')
    
    @property
    def connection_url(self) -> str:
        """
        Retorna URL de conexión SQLAlchemy.
        
        Returns:
            postgresql://usuario:contraseña@host/database
        """
        return f"postgresql://{self.user}:{self.password}@{self.host}/{self.database}"
    
    def __repr__(self) -> str:
        return f"DatabaseConfig({self.user}@{self.host}/{self.database})"
