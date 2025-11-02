"""
Performance Optimizations Integration Module
Facilita a integração de Connection Pool e Cache no WATS
"""

import logging
from typing import Optional
from src.wats.db.connection_pool import get_connection_pool, close_connection_pool
from src.wats.util_cache.cache import get_cache, cached, invalidate_cache_pattern
from src.wats.config import Settings


def initialize_performance_optimizations(config: Settings):
    """
    Inicializa otimizações de performance (Pool + Cache).
    
    Deve ser chamado no início da aplicação, após carregar config.
    
    Args:
        config: Instância de Settings com configurações do banco
    """
    try:
        # 1. Inicializa Connection Pool
        connection_string = _build_connection_string(config)
        pool_size = 5  # Valor padrão
        max_overflow = 10  # Valor padrão
        
        pool = get_connection_pool(
            connection_string=connection_string,
            pool_size=pool_size,
            max_overflow=max_overflow
        )
        
        logging.info(f"Connection Pool initialized (size={pool_size}, overflow={max_overflow})")
        
        # 2. Inicializa Cache
        cache_ttl = 300  # 5 minutos default
        cache = get_cache(default_ttl=cache_ttl)
        
        logging.info(f"Cache system initialized (default TTL={cache_ttl}s)")
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to initialize performance optimizations: {e}")
        return False


def _build_connection_string(config: Settings) -> str:
    """Constrói connection string a partir do config."""
    db_type = config.DB_TYPE
    
    if db_type == "sqlserver":
        driver = "ODBC Driver 17 for SQL Server"  # Valor padrão
        server = config.DB_SERVER
        database = config.DB_DATABASE
        uid = config.DB_UID
        pwd = config.DB_PWD
        
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={uid};"
            f"PWD={pwd};"
            "TrustServerCertificate=yes;"
        )
        
        return conn_str
    
    else:
        # Por enquanto, suporta apenas SQL Server
        raise ValueError(f"Unsupported database type: {db_type}. Only 'sqlserver' is supported.")


def shutdown_performance_optimizations():
    """
    Desliga otimizações de performance gracefully.
    
    Deve ser chamado ao encerrar a aplicação.
    """
    try:
        # Fecha connection pool
        close_connection_pool()
        logging.info("Connection Pool closed")
        
        # Cache não precisa ser fechado (thread daemon)
        cache = get_cache()
        stats = cache.get_stats()
        logging.info(f"Cache stats: {stats}")
        
    except Exception as e:
        logging.error(f"Error shutting down performance optimizations: {e}")


# Decoradores utilitários para facilitar uso do cache
def cache_connections(ttl: int = 60):
    """Cache para lista de conexões (1 minuto default)."""
    return cached(ttl=ttl, key_prefix="connections")


def cache_groups(ttl: int = 300):
    """Cache para lista de grupos (5 minutos default)."""
    return cached(ttl=ttl, key_prefix="groups")


def cache_users(ttl: int = 300):
    """Cache para dados de usuários (5 minutos default)."""
    return cached(ttl=ttl, key_prefix="users")


def cache_permissions(ttl: int = 180):
    """Cache para permissões (3 minutos default)."""
    return cached(ttl=ttl, key_prefix="permissions")


def cache_config(ttl: int = 600):
    """Cache para configurações (10 minutos default)."""
    return cached(ttl=ttl, key_prefix="config")


def invalidate_connection_caches():
    """Invalida todos os caches relacionados a conexões."""
    invalidate_cache_pattern("connections:*")
    logging.debug("Connection caches invalidated")


def invalidate_user_caches():
    """Invalida todos os caches relacionados a usuários e conexões (que dependem de permissões)."""
    invalidate_cache_pattern("users:*")
    invalidate_cache_pattern("permissions:*")
    invalidate_cache_pattern("connections:*")  # Conexões dependem de permissões
    logging.debug("User, permission and connection caches invalidated")


def invalidate_group_caches():
    """Invalida todos os caches relacionados a grupos, permissões e conexões."""
    invalidate_cache_pattern("groups:*")
    invalidate_cache_pattern("permissions:*")
    invalidate_cache_pattern("connections:*")  # Conexões dependem de grupos
    logging.debug("Group, permission and connection caches invalidated")


# Exemplo de uso em repositories:
"""
class OptimizedConnectionRepository(ConnectionRepository):
    
    @cache_connections(ttl=60)
    def select_all(self, username: str):
        # Usa connection pool automaticamente via DatabaseManager atualizado
        return super().select_all(username)
    
    def admin_create_connection(self, data):
        result = super().admin_create_connection(data)
        if result[0]:  # Se sucesso
            invalidate_connection_caches()
        return result
"""
