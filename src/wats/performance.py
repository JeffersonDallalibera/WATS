"""
Performance Optimizations Integration Module
Facilita a integração de Connection Pool e Cache Inteligente no WATS
"""

import logging
from typing import Optional
from src.wats.db.connection_pool import get_connection_pool, close_connection_pool
from src.wats.util_cache.intelligent_cache import (
    get_cache,
    cached,
    invalidate_user_caches as _invalidate_user_caches,
    invalidate_group_caches as _invalidate_group_caches,
    invalidate_connection_caches as _invalidate_connection_caches,
)
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
        pool_size = max(1, int(getattr(config, "PERF_DB_POOL_SIZE", 5)))
        max_overflow = max(0, int(getattr(config, "PERF_DB_MAX_OVERFLOW", 10)))
        
        get_connection_pool(
            connection_string=connection_string,
            pool_size=pool_size,
            max_overflow=max_overflow
        )
        
        logging.info(f"Connection Pool initialized (size={pool_size}, overflow={max_overflow})")
        
        # 2. Inicializa Cache
        cache_ttl = max(5, int(getattr(config, "PERF_CACHE_TTL_SECONDS", 300)))
        cache_max_size = max(100, int(getattr(config, "PERF_CACHE_MAX_SIZE", 1000)))
        get_cache(default_ttl=cache_ttl, max_size=cache_max_size)
        
        logging.info(
            f"Cache system initialized (default TTL={cache_ttl}s, max_size={cache_max_size})"
        )
        
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
        db_port = getattr(config, "DB_PORT", None)
        database = config.DB_DATABASE
        uid = config.DB_UID
        pwd = config.DB_PWD

        server_with_port = f"{server},{db_port}" if db_port else server
        
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server_with_port};"
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
    _invalidate_connection_caches()
    logging.debug("Connection caches invalidated")


def invalidate_user_caches(user_id: Optional[int] = None):
    """
    Invalida todos os caches relacionados a usuários e conexões (que dependem de permissões).
    
    Args:
        user_id: ID do usuário específico (opcional). Se None, invalida todos.
    """
    _invalidate_user_caches(user_id)
    logging.debug(f"User, permission and connection caches invalidated (user_id={user_id})")


def invalidate_group_caches(group_id: Optional[int] = None):
    """
    Invalida todos os caches relacionados a grupos, permissões e conexões.
    
    Args:
        group_id: ID do grupo específico (opcional). Se None, invalida todos.
    """
    _invalidate_group_caches(group_id)
    logging.debug(f"Group, permission and connection caches invalidated (group_id={group_id})")


