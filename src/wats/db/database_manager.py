# WATS_Project/wats_app/db/database_manager.py
import logging
from typing import Any, Optional

from src.wats.config import Settings, is_demo_mode
from src.wats.db.exceptions import DatabaseConfigError, DatabaseConnectionError

# NOTE: DB drivers are intentionally imported lazily inside the
# specific configuration methods below. Importing heavy DB drivers
# (pyodbc/psycopg2) at module import time slows application startup
# even if the driver won't be used. Moving imports reduces initial
# import latency.


class DatabaseManager:
    """Gerencia a conexão e a sintaxe (dialeto) para múltiplos bancos."""

    def __init__(self, settings: Settings, use_connection_pool: bool = True):
        self.db_type = settings.DB_TYPE
        self.driver_module: Any = None
        self.connection_string = ""
        self.is_demo = is_demo_mode()
        self.use_connection_pool = use_connection_pool
        self.connection_pool = None

        # Propriedades de Dialeto SQL
        self.NOW: str = ""
        self.CURRENT_TIMESTAMP: str = "getdate()"  # Alias para NOW
        self.PARAM: str = ""  # Placeholder (e.g., ? ou %s)
        self.ISNULL: str = ""
        self.IDENTITY_QUERY: str = ""

        # Se está em modo demo, não configura banco de dados real
        if self.is_demo:
            logging.info("DatabaseManager iniciado em MODO DEMO - não conectará ao banco de dados")
            self._configure_demo_mode()
            return

        try:
            if self.db_type == "sqlserver":
                self._configure_sqlserver(settings)
            elif self.db_type == "sqlite":
                self._configure_sqlite(settings)
            else:
                raise DatabaseConfigError(
                    f"DB_TYPE '{self.db_type}' não suportado. Use 'sqlserver' ou 'sqlite'."
                )
        except Exception as e:
            logging.error(f"Erro fatal ao configurar DatabaseManager: {e}")
            raise DatabaseConfigError(f"Erro ao ler as configurações do banco: {e}")

        # Inicializa Connection Pool se habilitado
        if self.use_connection_pool and not self.is_demo:
            self._initialize_connection_pool()

        self.conn: Optional[Any] = None

    def _configure_demo_mode(self):
        """Configura valores padrão para modo demo."""
        self.NOW = "NOW()"
        self.CURRENT_TIMESTAMP = "NOW()"
        self.PARAM = "?"
        self.ISNULL = "ISNULL"
        self.IDENTITY_QUERY = "SELECT 1 AS ID;"

    def _initialize_connection_pool(self):
        """Inicializa o Connection Pool para melhor performance."""
        try:
            from src.wats.db.connection_pool import get_connection_pool
            
            # Configura tamanho do pool baseado no tipo de aplicação
            pool_size = 5  # Conexões base
            max_overflow = 10  # Conexões extras sob demanda
            
            self.connection_pool = get_connection_pool(
                connection_string=self.connection_string,
                pool_size=pool_size,
                max_overflow=max_overflow
            )
            
            logging.info(
                f"Connection Pool initialized (size={pool_size}, overflow={max_overflow})"
            )
        except Exception as e:
            logging.warning(
                f"Failed to initialize connection pool: {e}. Falling back to direct connections."
            )
            self.use_connection_pool = False
            self.connection_pool = None

    def _configure_sqlserver(self, s: Settings):
        try:
            import pyodbc
        except ImportError:
            raise DatabaseConfigError(
                "Driver 'pyodbc' não instalado. Execute 'pip install pyodbc'."
            )

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
        # Dialeto SQL Server
        self.NOW = "GETDATE()"
        self.CURRENT_TIMESTAMP = "GETDATE()"
        self.PARAM = "?"
        self.ISNULL = "ISNULL"
        self.IDENTITY_QUERY = "SELECT @@IDENTITY AS ID;"

    def _configure_sqlite(self, s: Settings):
        """Configura SQLite para desenvolvimento/testes locais."""
        try:
            import sqlite3
        except ImportError:
            raise DatabaseConfigError("Driver 'sqlite3' não disponível.")

        self.driver_module = sqlite3
        db_path = s.DB_DATABASE or "wats.db"
        self.connection_string = db_path

        # Dialeto SQLite
        self.NOW = "datetime('now')"
        self.CURRENT_TIMESTAMP = "datetime('now')"
        self.PARAM = "?"
        self.ISNULL = "IFNULL"
        self.IDENTITY_QUERY = "SELECT last_insert_rowid() AS ID;"

    def _get_connection(self) -> Any:
        """Retorna um objeto de conexão (para transações)."""
        try:
            if self.conn is None or (hasattr(self.conn, "closed") and self.conn.closed):
                self.conn = self.driver_module.connect(self.connection_string)

            # Configura modo transacional se disponível
            if hasattr(self.conn, "autocommit"):
                self.conn.autocommit = False

            return self.conn
        except Exception as e:
            logging.error(f"Não foi possível conectar (transação): {e}")
            try:
                # Tenta reconectar
                self.conn = self.driver_module.connect(self.connection_string)
                if hasattr(self.conn, "autocommit"):
                    self.conn.autocommit = False
                return self.conn
            except Exception as e_inner:
                logging.error(f"Falha na reconexão: {e_inner}")
                raise DatabaseConnectionError(f"Não foi possível conectar: {e_inner}")

    def _connect_autocommit(self) -> Any:
        """Retorna uma *nova* conexão com autocommit=True."""
        try:
            # Para selects simples, é mais seguro usar uma conexão nova
            conn = self.driver_module.connect(self.connection_string)
            conn.autocommit = True
            return conn
        except self.driver_module.Error as e:
            logging.error(f"Não foi possível conectar (autocommit): {e}")
            raise DatabaseConnectionError(f"Não foi possível conectar: {e}")

    def get_cursor(self) -> Any:
        """Retorna um cursor com autocommit=True."""
        # Em modo demo, retorna None para forçar uso do mock service
        if self.is_demo:
            logging.debug("[DEMO] get_cursor() retornando None - usando mock service")
            return None

        try:
            # Para cursores simples com autocommit, não usamos o pool
            # O pool é melhor para transações longas
            return self._connect_autocommit().cursor()
        except Exception as e:
            logging.error(f"Falha ao obter cursor com autocommit: {e}")
            return None  # Repositórios devem checar

    def get_pooled_connection(self):
        """
        Retorna um context manager de conexão do pool.
        
        Usage:
            with db.get_pooled_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("...")
                cursor.fetchall()
        """
        if self.is_demo:
            logging.debug("[DEMO] get_pooled_connection() retornando None")
            return None
        
        if self.use_connection_pool and self.connection_pool:
            return self.connection_pool.get_connection()
        else:
            # Fallback: retorna conexão direta
            from contextlib import contextmanager
            
            @contextmanager
            def _direct_connection():
                conn = self._connect_autocommit()
                try:
                    yield conn
                finally:
                    conn.close()
            
            return _direct_connection()

    def get_transactional_connection(self) -> Any:
        """
        Retorna a conexão compartilhada para transações.
        NOTA: Para usar o pool, prefira get_pooled_connection() com context manager.
        """
        # Em modo demo, retorna None para forçar uso do mock service
        if self.is_demo:
            logging.debug(
                "[DEMO] get_transactional_connection() retornando None - usando mock service"
            )
            return None

        try:
            # Mantém comportamento original (conexão compartilhada)
            # O pool deve ser usado via get_pooled_connection()
            return self._get_connection()
        except Exception as e:
            logging.error(f"Falha ao obter conexão transacional: {e}")
            return None  # Repositórios devem checar
    
    def close(self):
        """Fecha conexões e libera recursos."""
        if self.conn:
            try:
                self.conn.close()
                logging.debug("Conexão principal fechada")
            except Exception as e:
                logging.error(f"Erro ao fechar conexão: {e}")
        
        # Não fecha o pool aqui - ele é singleton e será fechado no shutdown da aplicação
        if self.connection_pool:
            logging.debug("Connection pool será fechado no shutdown da aplicação")
