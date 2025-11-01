"""WATS Util Cache Module - Sistema de cache."""

from src.wats.util_cache.cache import (
    InMemoryCache,
    get_cache,
    cached,
    invalidate_cache,
    invalidate_cache_pattern,
    clear_all_cache,
)

__all__ = [
    "InMemoryCache",
    "get_cache",
    "cached",
    "invalidate_cache",
    "invalidate_cache_pattern",
    "clear_all_cache",
]
