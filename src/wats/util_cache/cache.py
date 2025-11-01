"""
Sistema de Cache Inteligente para WATS
Reduz consultas ao banco e operações de I/O
"""

import time
import threading
from typing import Any, Callable, Optional, Dict, Tuple
from functools import wraps
import logging


class CacheEntry:
    """Entrada individual do cache com timestamp."""
    
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.timestamp = time.time()
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """Verifica se a entrada expirou."""
        if self.ttl == 0:
            return False  # Cache permanente
        return (time.time() - self.timestamp) > self.ttl


class InMemoryCache:
    """
    Cache em memória thread-safe com TTL (Time To Live).
    
    Features:
    - TTL configurável por entrada
    - Thread-safe com locks
    - Limpeza automática de entradas expiradas
    - Estatísticas de hit/miss
    """
    
    def __init__(self, default_ttl: int = 300, cleanup_interval: int = 60):
        """
        Inicializa o cache.
        
        Args:
            default_ttl: Tempo de vida padrão em segundos (0 = permanente)
            cleanup_interval: Intervalo de limpeza automática em segundos
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        # Estatísticas
        self._hits = 0
        self._misses = 0
        
        # Inicia limpeza automática
        self._start_cleanup_thread()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtém valor do cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor ou None se não existir/expirado
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None
            
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Armazena valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Tempo de vida (usa default_ttl se None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
    
    def delete(self, key: str):
        """Remove entrada do cache."""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """Limpa todo o cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': round(hit_rate, 2),
                'total_requests': total_requests
            }
    
    def _cleanup_expired(self):
        """Remove entradas expiradas do cache."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logging.debug(f"Cache cleanup: removed {len(expired_keys)} expired entries")
    
    def _start_cleanup_thread(self):
        """Inicia thread de limpeza automática."""
        def cleanup_loop():
            while True:
                time.sleep(self.cleanup_interval)
                try:
                    self._cleanup_expired()
                except Exception as e:
                    logging.error(f"Error in cache cleanup: {e}")
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()


# Singleton global do cache
_global_cache: Optional[InMemoryCache] = None
_cache_lock = threading.Lock()


def get_cache(default_ttl: int = 300) -> InMemoryCache:
    """
    Obtém o cache singleton global.
    
    Args:
        default_ttl: TTL padrão em segundos
        
    Returns:
        InMemoryCache instance
    """
    global _global_cache
    
    with _cache_lock:
        if _global_cache is None:
            _global_cache = InMemoryCache(default_ttl=default_ttl)
        return _global_cache


def cached(ttl: Optional[int] = None, key_prefix: str = "", namespace: str = ""):
    """
    Decorator para cachear resultado de funções.
    
    Args:
        ttl: Tempo de vida do cache em segundos
        key_prefix: Prefixo para a chave do cache (deprecated, use namespace)
        namespace: Namespace do cache (ex: "users", "connections")
    
    Usage:
        @cached(ttl=300, namespace="users")
        def get_user(user_id):
            return fetch_user_from_db(user_id)
    """
    # Se namespace foi fornecido, usa ele como key_prefix
    if namespace:
        key_prefix = namespace
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gera chave do cache baseada em args/kwargs
            cache_key = _generate_cache_key(func, args, kwargs, key_prefix)
            
            # Tenta pegar do cache
            cache = get_cache()
            cached_value = cache.get(cache_key)
            
            if cached_value is not None:
                logging.debug(f"Cache HIT: {cache_key}")
                return cached_value
            
            # Cache miss - executa função
            logging.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)
            
            # Armazena no cache
            cache.set(cache_key, result, ttl)
            
            return result
        
        # Adiciona função para limpar cache específico
        def clear_cache(*args, **kwargs):
            cache_key = _generate_cache_key(func, args, kwargs, key_prefix)
            get_cache().delete(cache_key)
        
        wrapper.clear_cache = clear_cache
        return wrapper
    
    return decorator


def _generate_cache_key(func: Callable, args: Tuple, kwargs: Dict, prefix: str) -> str:
    """Gera chave única para o cache baseada na função e argumentos."""
    func_name = f"{func.__module__}.{func.__name__}"
    
    # Serializa args e kwargs para string
    args_str = "_".join(str(arg) for arg in args)
    kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    
    parts = [prefix, func_name, args_str, kwargs_str]
    key = ":".join(filter(None, parts))
    
    return key


def invalidate_cache_pattern(pattern: str):
    """
    Invalida todas as entradas do cache que correspondem ao padrão.
    
    Args:
        pattern: Padrão para matching (ex: "user:*")
    """
    cache = get_cache()
    with cache._lock:
        keys_to_delete = [
            key for key in cache._cache.keys()
            if _matches_pattern(key, pattern)
        ]
        
        for key in keys_to_delete:
            cache.delete(key)
        
        logging.info(f"Invalidated {len(keys_to_delete)} cache entries matching '{pattern}'")


def _matches_pattern(key: str, pattern: str) -> bool:
    """Verifica se a chave corresponde ao padrão (suporta * como wildcard)."""
    if '*' not in pattern:
        return key == pattern
    
    parts = pattern.split('*')
    
    # Verifica início
    if not key.startswith(parts[0]):
        return False
    
    # Verifica fim
    if parts[-1] and not key.endswith(parts[-1]):
        return False
    
    return True


def invalidate_cache(namespace: str = "", pattern: str = "*"):
    """
    Invalida entradas do cache por namespace ou padrão.
    
    Args:
        namespace: Namespace para invalidar (ex: "users", "connections")
        pattern: Padrão adicional (default: "*" - todos do namespace)
    
    Examples:
        invalidate_cache(namespace="users")  # Limpa todos os caches de usuários
        invalidate_cache(namespace="connections", pattern="*admin*")  # Caches de admin
    """
    cache = get_cache()
    
    # Constrói padrão completo
    if namespace:
        full_pattern = f"*{namespace}*{pattern}"
    else:
        full_pattern = pattern
    
    with cache._lock:
        keys_to_delete = [
            key for key in cache._cache.keys()
            if _matches_pattern(key, full_pattern)
        ]
        
        for key in keys_to_delete:
            cache.delete(key)
        
        if keys_to_delete:
            logging.debug(f"Cache invalidation: removed {len(keys_to_delete)} entries (namespace='{namespace}')")


def clear_all_cache():
    """Limpa completamente o cache."""
    cache = get_cache()
    cache.clear()
    logging.info("All cache cleared")
