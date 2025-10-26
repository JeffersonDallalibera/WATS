# WATS_Project/wats_app/db/database_manager.py
import logging
from typing import Optional, Any
from wats_app.config import Settings
from wats_app.db.exceptions import DatabaseConfigError, DatabaseConnectionError

# NOTE: DB drivers are intentionally imported lazily inside the
# specific configuration methods below. Importing heavy DB drivers
# (pyodbc/psycopg2) at module import time slows application startup
# even if the driver won't be used. Moving imports reduces initial
# import latency.

class DatabaseManager:
    """Gerencia a conexão e a sintaxe (dialeto) para múltiplos bancos."""
    
    def __init__(self, settings: Settings):
        self.db_type = settings.DB_TYPE
        self.driver_module: Any = None
        self.connection_string = ""
        
        # Propriedades de Dialeto SQL
        self.NOW: str = ""
        self.PARAM: str = "" # Placeholder (e.g., ? ou %s)
        self.ISNULL: str = ""
        self.IDENTITY_QUERY: str = ""

        try:
            if self.db_type == 'sqlserver':
                self._configure_sqlserver(settings)
            elif self.db_type == 'postgresql':
                self._configure_postgresql(settings)
            else:
                raise DatabaseConfigError(f"DB_TYPE '{self.db_type}' não suportado.")
        except Exception as e:
            logging.error(f"Erro fatal ao configurar DatabaseManager: {e}")
            raise DatabaseConfigError(f"Erro ao ler as configurações do banco: {e}")

        self.conn: Optional[Any] = None

    def _configure_sqlserver(self, s: Settings):
        try:
            import pyodbc
        except ImportError:
            raise DatabaseConfigError("Driver 'pyodbc' não instalado. Execute 'pip install pyodbc'.")

        # Assign the imported module only when SQL Server is configured
        self.driver_module = pyodbc
        self.connection_string = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={s.DB_SERVER};"
            f"DATABASE={s.DB_DATABASE};"
            f"UID={s.DB_UID};"
            f"PWD={s.DB_PWD};"
            "TrustServerCertificate=yes;"
        )
        # Dialeto
        self.NOW = "GETDATE()"
        self.PARAM = "?"
        self.ISNULL = "ISNULL"
        self.IDENTITY_QUERY = "SELECT @@IDENTITY AS ID;"

    def _configure_postgresql(self, s: Settings):
        try:
            import psycopg2
        except ImportError:
            raise DatabaseConfigError("Driver 'psycopg2' não instalado. Execute 'pip install psycopg2-binary'.")

        # Assign the imported module only when PostgreSQL is configured
        self.driver_module = psycopg2
        port = s.DB_PORT or 5432
        self.connection_string = (
            f"host='{s.DB_SERVER}' dbname='{s.DB_DATABASE}' "
            f"user='{s.DB_UID}' password='{s.DB_PWD}' port='{port}'"
        )
        # Dialeto
        self.NOW = "NOW()"
        self.PARAM = "%s"
        self.ISNULL = "COALESCE"
        # O 'IDENTITY' do Postgres é tratado com "RETURNING <id_col>" na própria query.
        self.IDENTITY_QUERY = "RETURNING {id_col}" 

    def _get_connection(self) -> Any:
        """Retorna um objeto de conexão (para transações)."""
        try:
            if self.conn is None or self.conn.closed:
                 self.conn = self.driver_module.connect(self.connection_string)
            
            # psycopg2 usa .autocommit, pyodbc usa .autocommit
            if self.conn.autocommit:
                self.conn.autocommit = False # Garante modo transacional
                
            return self.conn
        except (self.driver_module.Error, Exception) as e:
            logging.error(f"Não foi possível conectar (transação): {e}")
            try:
                # Tenta reconectar
                self.conn = self.driver_module.connect(self.connection_string)
                self.conn.autocommit = False
                return self.conn
            except self.driver_module.Error as e_inner:
                logging.error(f"Falha na reconexão: {e_inner}")
                raise DatabaseConnectionError(f"Não foi possível conectar: {e_inner}")

    def _connect_autocommit(self) -> Any:
        """Retorna uma *nova* conexão com autocommit=True."""
        try:
            # Para selects simples, é mais seguro usar uma conexão nova
            # do que gerenciar o estado (autocommit=T/F) de uma conexão compartilhada.
            conn = self.driver_module.connect(self.connection_string)
            conn.autocommit = True
            return conn
        except self.driver_module.Error as e:
            logging.error(f"Não foi possível conectar (autocommit): {e}")
            raise DatabaseConnectionError(f"Não foi possível conectar: {e}")

    def get_cursor(self) -> Any:
        """Retorna um cursor com autocommit=True."""
        try:
            return self._connect_autocommit().cursor()
        except Exception as e:
            logging.error(f"Falha ao obter cursor com autocommit: {e}")
            return None # Repositórios devem checar

    def get_transactional_connection(self) -> Any:
        """Retorna a conexão compartilhada para transações."""
        try:
            return self._get_connection()
        except Exception as e:
            logging.error(f"Falha ao obter conexão transacional: {e}")
            return None # Repositórios devem checar