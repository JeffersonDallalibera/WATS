"""
Connection Pool Optimization for WATS Database
Reutiliza conexões do banco de dados para melhor performance
"""

import logging
import threading
from contextlib import contextmanager
from queue import Queue, Empty
from typing import Optional
import pyodbc


class ConnectionPool:
    """
    Pool de conexões para otimizar acesso ao banco de dados.
    
    Mantém conexões abertas e reutiliza, evitando overhead de criar/fechar
    conexões repetidamente.
    """

    def __init__(self, connection_string: str, pool_size: int = 5, max_overflow: int = 10):
        """
        Inicializa o connection pool.
        
        Args:
            connection_string: String de conexão do banco
            pool_size: Número de conexões mantidas no pool
            max_overflow: Máximo de conexões extras permitidas
        """
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool = Queue(maxsize=pool_size + max_overflow)
        self.current_size = 0
        self.lock = threading.Lock()
        self._initialize_pool()

    def _initialize_pool(self):
        """Inicializa o pool com conexões."""
        try:
            for _ in range(self.pool_size):
                conn = self._create_connection()
                if conn:
                    self.pool.put(conn)
                    self.current_size += 1
            logging.info(f"Connection pool initialized with {self.current_size} connections")
        except Exception as e:
            logging.error(f"Error initializing connection pool: {e}")

    def _create_connection(self) -> Optional[pyodbc.Connection]:
        """Cria uma nova conexão."""
        try:
            conn = pyodbc.connect(
                self.connection_string,
                timeout=10,
                autocommit=False
            )
            return conn
        except Exception as e:
            logging.error(f"Error creating database connection: {e}")
            return None

    @contextmanager
    def get_connection(self):
        """
        Context manager para obter conexão do pool.
        
        Usage:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        conn = None
        try:
            # Tenta pegar conexão do pool
            try:
                conn = self.pool.get(block=True, timeout=5)
            except Empty:
                # Pool vazio, cria nova se não ultrapassar max_overflow
                with self.lock:
                    if self.current_size < (self.pool_size + self.max_overflow):
                        conn = self._create_connection()
                        self.current_size += 1
                    else:
                        # Aguarda conexão ficar disponível
                        conn = self.pool.get(block=True, timeout=10)

            # Verifica se conexão ainda está válida
            if conn and not self._is_connection_valid(conn):
                conn.close()
                conn = self._create_connection()

            yield conn

        except Exception as e:
            logging.error(f"Error getting connection from pool: {e}")
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise
        finally:
            # Retorna conexão ao pool
            if conn:
                try:
                    # Limpa transação pendente
                    conn.rollback()
                    self.pool.put(conn, block=False)
                except:
                    # Se falhou ao retornar, cria nova conexão
                    try:
                        conn.close()
                    except:
                        pass
                    with self.lock:
                        self.current_size -= 1

    def _is_connection_valid(self, conn: pyodbc.Connection) -> bool:
        """Verifica se a conexão ainda está válida."""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except:
            return False

    def close_all(self):
        """Fecha todas as conexões do pool."""
        while not self.pool.empty():
            try:
                conn = self.pool.get(block=False)
                conn.close()
                self.current_size -= 1
            except Empty:
                break
            except Exception as e:
                logging.error(f"Error closing connection: {e}")
        
        logging.info(f"Connection pool closed. {self.current_size} connections remaining")

    def __del__(self):
        """Destrutor para garantir que conexões sejam fechadas."""
        try:
            self.close_all()
        except:
            pass


# Singleton para o connection pool global
_connection_pool: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()


def get_connection_pool(connection_string: str = None, 
                       pool_size: int = 5, 
                       max_overflow: int = 10) -> ConnectionPool:
    """
    Obtém ou cria o connection pool singleton.
    
    Args:
        connection_string: String de conexão (obrigatório na primeira chamada)
        pool_size: Tamanho do pool
        max_overflow: Overflow máximo
    
    Returns:
        ConnectionPool instance
    """
    global _connection_pool
    
    with _pool_lock:
        if _connection_pool is None:
            if connection_string is None:
                raise ValueError("connection_string required for first pool initialization")
            _connection_pool = ConnectionPool(connection_string, pool_size, max_overflow)
        
        return _connection_pool


def close_connection_pool():
    """Fecha o connection pool global."""
    global _connection_pool
    
    with _pool_lock:
        if _connection_pool:
            _connection_pool.close_all()
            _connection_pool = None
