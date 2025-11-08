"""WATS Util Cache Module - Sistema de cache inteligente."""

# Cache antigo (manter compatibilidade)
from src.wats.util_cache.cache import (
    InMemoryCache,
    get_cache as get_old_cache,
    cached as old_cached,
    invalidate_cache,
    invalidate_cache_pattern as old_invalidate_cache_pattern,
    clear_all_cache,
)

# Novo cache inteligente (recomendado)
from src.wats.util_cache.intelligent_cache import (
    IntelligentCache,
    get_cache,
    cached,
    invalidate_user_caches,
    invalidate_group_caches,
    invalidate_connection_caches,
    invalidate_all_caches,
)

__all__ = [
    # Cache antigo (compatibilidade)
    "InMemoryCache",
    "get_old_cache",
    "old_cached",
    "invalidate_cache",
    "old_invalidate_cache_pattern",
    "clear_all_cache",
    
    # Cache inteligente (novo)
    "IntelligentCache",
    "get_cache",
    "cached",
    "invalidate_user_caches",
    "invalidate_group_caches",
    "invalidate_connection_caches",
    "invalidate_all_caches",
]

