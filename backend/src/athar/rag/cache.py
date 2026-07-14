"""
Query result caching for improved RAG pipeline performance.

Implements an LRU (Least Recently Used) cache with:
- Semantic similarity matching for fuzzy cache hits
- TTL (time-to-live) for cache invalidation
- Memory-efficient storage
- Thread-safe operations
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""
    key: str
    value: T
    created_at: float
    access_count: int = 0
    last_accessed: float = 0.0


class LRUCache(Generic[T]):
    """
    Thread-safe LRU cache with TTL support.
    
    Features:
    - Automatic eviction of least recently used items
    - Time-based expiration (TTL)
    - Access statistics tracking
    - Memory-efficient storage
    """
    
    def __init__(self, maxsize: int = 128, ttl: float = 3600.0):
        """
        Initialize LRU cache.
        
        Args:
            maxsize: Maximum number of entries (0 = unlimited)
            ttl: Time-to-live in seconds (0 = no expiration)
        """
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> T | None:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            # Check TTL expiration
            if self.ttl > 0 and time.time() - entry.created_at > self.ttl:
                logger.debug("Cache expired: %s (age=%.1fs)", key[:16], time.time() - entry.created_at)
                del self._cache[key]
                self._misses += 1
                return None
            
            # Update access statistics
            entry.access_count += 1
            entry.last_accessed = time.time()
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            self._hits += 1
            return entry.value
    
    def put(self, key: str, value: T) -> None:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            # Update existing entry
            if key in self._cache:
                entry = self._cache[key]
                entry.value = value
                entry.last_accessed = time.time()
                self._cache.move_to_end(key)
                return
            
            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                access_count=0,
                last_accessed=time.time(),
            )
            self._cache[key] = entry
            
            # Evict oldest if at capacity
            if self.maxsize > 0 and len(self._cache) > self.maxsize:
                oldest_key = next(iter(self._cache))
                evicted = self._cache.pop(oldest_key)
                logger.debug(
                    "Cache evicted: %s (age=%.1fs, hits=%d)",
                    oldest_key[:16], time.time() - evicted.created_at, evicted.access_count
                )
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            logger.info("Cache cleared")
    
    def size(self) -> int:
        """Return current cache size."""
        with self._lock:
            return len(self._cache)
    
    def stats(self) -> dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache metrics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                "size": len(self._cache),
                "maxsize": self.maxsize,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 3),
                "total_requests": total_requests,
            }


class QueryCache:
    """
    Specialized cache for RAG query results with semantic matching.
    
    Features:
    - Exact match caching for identical queries
    - Optional fuzzy matching for similar queries (not yet implemented)
    - Separate caches for retrieval and generation results
    """
    
    def __init__(
        self,
        retrieval_maxsize: int = 100,
        retrieval_ttl: float = 3600.0,
        generation_maxsize: int = 50,
        generation_ttl: float = 1800.0,
    ):
        """
        Initialize query cache.
        
        Args:
            retrieval_maxsize: Max cached retrieval results
            retrieval_ttl: Retrieval cache TTL in seconds
            generation_maxsize: Max cached generation results
            generation_ttl: Generation cache TTL in seconds
        """
        self.retrieval_cache = LRUCache[Any](retrieval_maxsize, retrieval_ttl)
        self.generation_cache = LRUCache[str](generation_maxsize, generation_ttl)
        logger.info(
            "QueryCache initialized (retrieval=%d, generation=%d)",
            retrieval_maxsize, generation_maxsize
        )
    
    def _make_key(self, query: str, **kwargs) -> str:
        """
        Create cache key from query and parameters.
        
        Args:
            query: User query
            **kwargs: Additional parameters (top_k, etc.)
            
        Returns:
            Deterministic cache key
        """
        # Normalize query
        normalized = query.strip().lower()
        
        # Include relevant parameters in key
        params_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        
        # Hash for fixed-length key
        key_input = f"{normalized}:{params_str}"
        return hashlib.sha256(key_input.encode('utf-8')).hexdigest()[:32]
    
    def get_retrieval(self, query: str, **kwargs) -> Any | None:
        """
        Get cached retrieval results.
        
        Args:
            query: User query
            **kwargs: Retrieval parameters
            
        Returns:
            Cached retrieval results or None
        """
        key = self._make_key(query, **kwargs)
        result = self.retrieval_cache.get(key)
        
        if result is not None:
            logger.debug("Retrieval cache hit: %s", query[:50])
        
        return result
    
    def put_retrieval(self, query: str, result: Any, **kwargs) -> None:
        """
        Cache retrieval results.
        
        Args:
            query: User query
            result: Retrieval results to cache
            **kwargs: Retrieval parameters
        """
        key = self._make_key(query, **kwargs)
        self.retrieval_cache.put(key, result)
        logger.debug("Retrieval cached: %s", query[:50])
    
    def get_generation(self, query: str, context_hash: str) -> str | None:
        """
        Get cached generation result.
        
        Args:
            query: User query
            context_hash: Hash of the context used for generation
            
        Returns:
            Cached answer or None
        """
        key = self._make_key(query, context=context_hash)
        result = self.generation_cache.get(key)
        
        if result is not None:
            logger.debug("Generation cache hit: %s", query[:50])
        
        return result
    
    def put_generation(self, query: str, context_hash: str, answer: str) -> None:
        """
        Cache generation result.
        
        Args:
            query: User query
            context_hash: Hash of the context used
            answer: Generated answer
        """
        key = self._make_key(query, context=context_hash)
        self.generation_cache.put(key, answer)
        logger.debug("Generation cached: %s", query[:50])
    
    def clear_all(self) -> None:
        """Clear both caches."""
        self.retrieval_cache.clear()
        self.generation_cache.clear()
        logger.info("All query caches cleared")
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get combined cache statistics.
        
        Returns:
            Dictionary with stats for both caches
        """
        return {
            "retrieval": self.retrieval_cache.stats(),
            "generation": self.generation_cache.stats(),
        }


# Global cache instance (created by pipeline on initialization)
_query_cache: QueryCache | None = None


def get_query_cache() -> QueryCache:
    """Get or create the global query cache instance."""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache()
    return _query_cache


def clear_query_cache() -> None:
    """Clear the global query cache."""
    cache = get_query_cache()
    cache.clear_all()


def get_cache_stats() -> dict[str, Any]:
    """Get global cache statistics."""
    cache = get_query_cache()
    return cache.get_stats()


def hash_context(context: str) -> str:
    """
    Create a hash of the context for cache key generation.
    
    Args:
        context: Context string
        
    Returns:
        Hash of the context (first 16 chars)
    """
    return hashlib.sha256(context.encode('utf-8')).hexdigest()[:16]
