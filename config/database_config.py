import os
from typing import Optional


class Config:
    """Clase base para toda configuración del sistema ETL.
    
    Proporciona método utilitario para leer variables de entorno con validación.
    """
    
    @staticmethod
    def get_env(key: str, default: Optional[str] = None) -> str:
        """
        Obtiene variable de entorno con fallback a valor por defecto.
        
        Args:
            key: Nombre de la variable de entorno
            default: Valor por defecto si no existe
            
        Returns:
            str: Valor de variable de entorno o default
            
        Raises:
            ValueError: Si variable no existe y no hay default
        """
        value = os.environ.get(key, default)
        if value is None:
            raise ValueError(f"Variable de entorno requerida no encontrada: {key}")
        return value


class DatabaseConfig(Config):
    """Configuración de conexión a PostgreSQL.
    
    Lee credenciales desde variables de entorno o parámetros.
    Proporciona URL de conexión SQLAlchemy lista para usar.
    """
    
    def __init__(self, 
                 user: Optional[str] = None,
                 password: Optional[str] = None,
                 host: Optional[str] = None,
                 database: Optional[str] = None):
        """
        Inicializa la configuración de PostgreSQL.
        
        Si se omiten parámetros, los lee desde variables de entorno:
        - PG_USER (default: postgres)
        - PG_PASS (default: postgres)
        - PG_HOST (default: localhost)
        - PG_DB (default: postgres)
        
        Args:
            user: Usuario de PostgreSQL
            password: Contraseña de PostgreSQL
            host: Host/servidor de PostgreSQL
            database: Nombre de la base de datos
        """
        self.user = user or self.get_env('PG_USER', 'postgres')
        self.password = password or self.get_env('PG_PASS', 'postgres')
        self.host = host or self.get_env('PG_HOST', 'localhost')
        self.database = database or self.get_env('PG_DB', 'postgres')
    
    @property
    def connection_url(self) -> str:
        """
        Retorna URL de conexión SQLAlchemy para PostgreSQL.
        
        Incluye encoding LATIN1 para mayor compatibilidad con caracteres especiales.
        
        Returns:
            str: URL de conexión con formato postgresql://user:pass@host/database
        """
        # Usar LATIN1 que es más permisivo con caracteres problemáticos
        return f"postgresql://{self.user}:{self.password}@{self.host}/{self.database}?client_encoding=LATIN1"
    
    def __repr__(self) -> str:
        """Representación de la configuración."""
        return f"DatabaseConfig({self.user}@{self.host}/{self.database})"
