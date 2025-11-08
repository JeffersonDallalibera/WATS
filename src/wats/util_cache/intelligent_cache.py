"""
Sistema de Cache Inteligente para WATS
Implementa cache multinível com TTL e invalidação automática
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Set, Callable
from functools import wraps


class IntelligentCache:
    """
    Cache inteligente com TTL, invalidação pattern-based e callbacks.
    
    Features:
    - TTL configurável por padrão de chave
    - Invalidação por pattern (ex: "users:*")
    - Callbacks de invalidação
    - Thread-safe
    - Estatísticas de hit/miss
    """

    def __init__(self, default_ttl: int = 60, max_size: int = 1000):
        """
        Inicializa o cache.
        
        Args:
            default_ttl: TTL padrão em segundos (default: 60s)
            max_size: Tamanho máximo do cache (default: 1000 itens)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl
        self.max_size = max_size
        
        # Estatísticas
        self._hits = 0
        self._misses = 0
        
        # Callbacks de invalidação
        self._invalidation_callbacks: Dict[str, Set[Callable]] = {}
        
        # Thread de limpeza
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
        logging.info(f"IntelligentCache initialized (TTL={default_ttl}s, max_size={max_size})")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor do cache.
        
        Args:
            key: Chave do cache
            default: Valor padrão se não encontrado
            
        Returns:
            Valor armazenado ou default
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default
            
            entry = self._cache[key]
            
            # Verifica se expirou
            if self._is_expired(entry):
                del self._cache[key]
                self._misses += 1
                return default
            
            self._hits += 1
            return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Armazena valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: TTL customizado (usa default se None)
        """
        with self._lock:
            # Limpa cache se atingir max_size
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            expires_at = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
            
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.now()
            }

    def invalidate(self, key: str):
        """
        Invalida uma chave específica.
        
        Args:
            key: Chave a invalidar
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logging.debug(f"Cache invalidated: {key}")

    def invalidate_pattern(self, pattern: str):
        """
        Invalida todas as chaves que correspondem ao pattern.
        
        Args:
            pattern: Pattern com wildcard (* ou ?)
                     Ex: "users:*", "connections:123:*"
        """
        import fnmatch
        
        with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            
            for key in keys_to_delete:
                del self._cache[key]
            
            if keys_to_delete:
                logging.info(f"Cache invalidated pattern '{pattern}': {len(keys_to_delete)} keys")
            
            # Invocar callbacks registrados para este pattern
            self._invoke_callbacks(pattern)

    def invalidate_all(self):
        """Limpa todo o cache."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logging.info(f"Cache cleared: {count} keys removed")

    def register_invalidation_callback(self, pattern: str, callback: Callable):
        """
        Registra callback a ser chamado quando pattern for invalidado.
        
        Args:
            pattern: Pattern de chave
            callback: Função a ser chamada (sem argumentos)
        """
        with self._lock:
            if pattern not in self._invalidation_callbacks:
                self._invalidation_callbacks[pattern] = set()
            self._invalidation_callbacks[pattern].add(callback)

    def _invoke_callbacks(self, pattern: str):
        """Invoca callbacks registrados para um pattern."""
        import fnmatch
        
        with self._lock:
            for callback_pattern, callbacks in self._invalidation_callbacks.items():
                if fnmatch.fnmatch(pattern, callback_pattern):
                    for callback in callbacks:
                        try:
                            callback()
                        except Exception as e:
                            logging.error(f"Error in invalidation callback: {e}")

    def _is_expired(self, entry: Dict) -> bool:
        """Verifica se entrada expirou."""
        return datetime.now() > entry['expires_at']

    def _evict_oldest(self):
        """Remove entrada mais antiga do cache."""
        if not self._cache:
            return
        
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]['created_at']
        )
        del self._cache[oldest_key]

    def _cleanup_loop(self):
        """Loop de limpeza de entradas expiradas."""
        while True:
            try:
                time.sleep(60)  # Limpa a cada 1 minuto
                self._cleanup_expired()
            except Exception as e:
                logging.error(f"Error in cache cleanup loop: {e}")

    def _cleanup_expired(self):
        """Remove entradas expiradas."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logging.debug(f"Cache cleanup: {len(expired_keys)} expired keys removed")

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.
        
        Returns:
            Dict com hits, misses, hit_rate, size
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            
            return {
                'hits': self._hits,
                'misses': self._misses,
                'total_requests': total,
                'hit_rate': round(hit_rate, 2),
                'current_size': len(self._cache),
                'max_size': self.max_size
            }

    def reset_stats(self):
        """Reseta estatísticas."""
        with self._lock:
            self._hits = 0
            self._misses = 0


# Singleton global
_cache: Optional[IntelligentCache] = None
_cache_lock = threading.Lock()


def get_cache(default_ttl: int = 60, max_size: int = 1000) -> IntelligentCache:
    """
    Obtém ou cria o cache singleton.
    
    Args:
        default_ttl: TTL padrão em segundos
        max_size: Tamanho máximo
        
    Returns:
        IntelligentCache instance
    """
    global _cache
    
    with _cache_lock:
        if _cache is None:
            _cache = IntelligentCache(default_ttl, max_size)
        return _cache


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator para cachear resultados de funções.
    
    Args:
        ttl: TTL customizado (usa default se None)
        key_prefix: Prefixo da chave de cache
        
    Usage:
        @cached(ttl=300, key_prefix="users")
        def get_user(user_id):
            return db.query(User).get(user_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Gerar chave de cache
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{':'.join(map(str, args))}"
            if kwargs:
                cache_key += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
            
            # Tentar obter do cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Funções de conveniência para invalidação
def invalidate_user_caches(user_id: int):
    """Invalida todos os caches relacionados a um usuário."""
    cache = get_cache()
    cache.invalidate_pattern(f"users:{user_id}:*")
    cache.invalidate_pattern(f"permissions:{user_id}:*")
    cache.invalidate_pattern("connections:*")  # Conexões podem ser afetadas
    logging.info(f"✅ Cache invalidated for user {user_id}")


def invalidate_group_caches(group_id: int):
    """Invalida todos os caches relacionados a um grupo."""
    cache = get_cache()
    cache.invalidate_pattern(f"groups:{group_id}:*")
    cache.invalidate_pattern("permissions:*")  # Permissões de grupo afetadas
    cache.invalidate_pattern("connections:*")  # Conexões podem ser afetadas
    logging.info(f"✅ Cache invalidated for group {group_id}")


def invalidate_connection_caches(connection_id: Optional[int] = None):
    """Invalida caches de conexões."""
    cache = get_cache()
    if connection_id:
        cache.invalidate_pattern(f"connections:{connection_id}:*")
    else:
        cache.invalidate_pattern("connections:*")
    logging.info(f"✅ Cache invalidated for connection{'s' if not connection_id else f' {connection_id}'}")


def invalidate_all_caches():
    """Invalida todos os caches."""
    cache = get_cache()
    cache.invalidate_all()
    logging.warning("⚠️ All caches invalidated")
