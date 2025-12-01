import os


class DatabaseConfig:
    """
    Configuración de la base de datos PostgreSQL.
    
    Lee las credenciales desde variables de entorno y proporciona
    una URL de conexión formateada para SQLAlchemy.
    
    Variables de entorno requeridas:
        - PG_USER: Usuario de PostgreSQL
        - PG_PASS: Contraseña de PostgreSQL
        - PG_HOST: Host donde está PostgreSQL (ej: localhost, 127.0.0.1)
        - PG_DB: Nombre de la base de datos
    """
    
    def __init__(self):
        """
        Inicializa la configuración leyendo variables de entorno.
        Si alguna variable no existe, usa valores por defecto.
        """
        # Leer credenciales de PostgreSQL desde variables de entorno
        self.user = os.environ.get('PG_USER', 'usuario')
        self.password = os.environ.get('PG_PASS', 'password')
        self.host = os.environ.get('PG_HOST', 'localhost')
        self.database = os.environ.get('PG_DB', 'basedatos')
    
    @property
    def connection_url(self):
        """
        Retorna la URL de conexión a PostgreSQL en formato SQLAlchemy.
        
        Formato: postgresql://usuario:contraseña@host/database
        
        Returns:
            str: URL de conexión completa
            
        Ejemplo:
            postgresql://postgres:1234@127.0.0.1/cine
        """
        return f"postgresql://{self.user}:{self.password}@{self.host}/{self.database}"
