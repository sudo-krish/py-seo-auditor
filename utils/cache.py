"""
Caching utilities for SEO Auditor
Supports multiple backends: file, memory, and Redis
"""

import os
import json
import pickle
import hashlib
import time
from pathlib import Path
from functools import wraps, lru_cache
from typing import Any, Optional, Callable
from datetime import datetime, timedelta
import threading
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Main cache manager supporting multiple backends
    """

    def __init__(self, config: dict = None):
        """
        Initialize cache manager with configuration

        Args:
            config: Cache configuration dictionary from config.yaml
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.ttl = self.config.get('ttl', 3600)  # Default 1 hour
        self.backend = self.config.get('backend', 'file').lower()
        self.directory = Path(self.config.get('directory', 'data/cache'))
        self.max_size_mb = self.config.get('max_size_mb', 500)

        # Initialize backend
        if self.backend == 'file':
            self._backend = FileCache(self.directory, self.ttl, self.max_size_mb)
        elif self.backend == 'memory':
            self._backend = MemoryCache(self.ttl)
        elif self.backend == 'redis':
            self._backend = RedisCache(self.ttl)
        else:
            logger.warning(f"Unknown cache backend: {self.backend}, using memory")
            self._backend = MemoryCache(self.ttl)

        logger.info(f"Cache initialized with {self.backend} backend (TTL: {self.ttl}s)")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None

        try:
            return self._backend.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.enabled:
            return False

        try:
            return self._backend.set(key, value, ttl or self.ttl)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete specific key from cache"""
        try:
            return self._backend.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cache"""
        try:
            return self._backend.clear()
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        return self._backend.exists(key)

    def get_stats(self) -> dict:
        """Get cache statistics"""
        return self._backend.get_stats()

    @staticmethod
    def generate_key(*args, **kwargs) -> str:
        """
        Generate cache key from arguments

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            MD5 hash of arguments as cache key
        """
        key_data = f"{args}{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()


class FileCache:
    """
    File-based caching implementation
    """

    def __init__(self, directory: Path, ttl: int = 3600, max_size_mb: int = 500):
        """
        Initialize file cache

        Args:
            directory: Cache directory path
            ttl: Time to live in seconds
            max_size_mb: Maximum cache size in megabytes
        """
        self.directory = directory
        self.ttl = ttl
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.lock = threading.Lock()

        # Create cache directory
        self.directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"File cache directory: {self.directory}")

    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key"""
        return self.directory / f"{key}.cache"

    def get(self, key: str) -> Optional[Any]:
        """Get value from file cache"""
        file_path = self._get_file_path(key)

        if not file_path.exists():
            return None

        with self.lock:
            try:
                # Check if cache is expired
                file_age = time.time() - file_path.stat().st_mtime
                if file_age > self.ttl:
                    file_path.unlink()
                    return None

                # Load cached data
                with open(file_path, 'rb') as f:
                    return pickle.load(f)

            except Exception as e:
                logger.error(f"Error reading cache file {key}: {e}")
                return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in file cache"""
        file_path = self._get_file_path(key)

        with self.lock:
            try:
                # Check cache size limit
                if self._get_total_size() > self.max_size_bytes:
                    self._cleanup_old_files()

                # Save to cache file
                with open(file_path, 'wb') as f:
                    pickle.dump(value, f)

                return True

            except Exception as e:
                logger.error(f"Error writing cache file {key}: {e}")
                return False

    def delete(self, key: str) -> bool:
        """Delete cache file"""
        file_path = self._get_file_path(key)

        with self.lock:
            try:
                if file_path.exists():
                    file_path.unlink()
                return True
            except Exception as e:
                logger.error(f"Error deleting cache file {key}: {e}")
                return False

    def clear(self) -> bool:
        """Clear all cache files"""
        with self.lock:
            try:
                for file_path in self.directory.glob("*.cache"):
                    file_path.unlink()
                logger.info("File cache cleared")
                return True
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
                return False

    def exists(self, key: str) -> bool:
        """Check if cache file exists and is valid"""
        file_path = self._get_file_path(key)

        if not file_path.exists():
            return False

        # Check expiration
        file_age = time.time() - file_path.stat().st_mtime
        return file_age <= self.ttl

    def _get_total_size(self) -> int:
        """Get total cache directory size in bytes"""
        total_size = 0
        for file_path in self.directory.glob("*.cache"):
            total_size += file_path.stat().st_size
        return total_size

    def _cleanup_old_files(self):
        """Remove oldest cache files to free space"""
        files = list(self.directory.glob("*.cache"))
        files.sort(key=lambda f: f.stat().st_mtime)

        # Remove oldest 25% of files
        remove_count = len(files) // 4
        for file_path in files[:remove_count]:
            try:
                file_path.unlink()
                logger.debug(f"Removed old cache file: {file_path.name}")
            except Exception as e:
                logger.error(f"Error removing cache file: {e}")

    def get_stats(self) -> dict:
        """Get cache statistics"""
        files = list(self.directory.glob("*.cache"))
        total_size = self._get_total_size()

        return {
            'backend': 'file',
            'total_items': len(files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'max_size_mb': self.max_size_bytes / (1024 * 1024),
            'directory': str(self.directory)
        }


class MemoryCache:
    """
    In-memory caching implementation with TTL support
    """

    def __init__(self, ttl: int = 3600, maxsize: int = 1000):
        """
        Initialize memory cache

        Args:
            ttl: Time to live in seconds
            maxsize: Maximum number of items to store
        """
        self.ttl = ttl
        self.maxsize = maxsize
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            # Check if expired
            if self._is_expired(key):
                del self.cache[key]
                del self.timestamps[key]
                self.misses += 1
                return None

            # Move to end (LRU)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache"""
        with self.lock:
            try:
                # Remove oldest if at capacity
                if len(self.cache) >= self.maxsize and key not in self.cache:
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    del self.timestamps[oldest_key]

                self.cache[key] = value
                self.timestamps[key] = time.time()
                self.cache.move_to_end(key)

                return True
            except Exception as e:
                logger.error(f"Error setting cache: {e}")
                return False

    def delete(self, key: str) -> bool:
        """Delete from memory cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                del self.timestamps[key]
            return True

    def clear(self) -> bool:
        """Clear all memory cache"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            self.hits = 0
            self.misses = 0
            logger.info("Memory cache cleared")
            return True

    def exists(self, key: str) -> bool:
        """Check if key exists and is valid"""
        with self.lock:
            if key not in self.cache:
                return False
            return not self._is_expired(key)

    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.timestamps:
            return True
        age = time.time() - self.timestamps[key]
        return age > self.ttl

    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'backend': 'memory',
            'total_items': len(self.cache),
            'maxsize': self.maxsize,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 2),
            'ttl': self.ttl
        }


class RedisCache:
    """
    Redis-based caching implementation
    """

    def __init__(self, ttl: int = 3600, host: str = 'localhost', port: int = 6379):
        """
        Initialize Redis cache

        Args:
            ttl: Time to live in seconds
            host: Redis server host
            port: Redis server port
        """
        self.ttl = ttl
        self.redis_client = None

        try:
            import redis
            self.redis_client = redis.StrictRedis(
                host=host,
                port=port,
                decode_responses=False
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis cache connected to {host}:{port}")
        except ImportError:
            logger.error("Redis package not installed. Install with: pip install redis")
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            logger.warning("Falling back to memory cache")

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self.redis_client:
            return None

        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return pickle.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache"""
        if not self.redis_client:
            return False

        try:
            serialized = pickle.dumps(value)
            self.redis_client.setex(key, ttl or self.ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete from Redis cache"""
        if not self.redis_client:
            return False

        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    def clear(self) -> bool:
        """Clear all Redis cache (flushdb)"""
        if not self.redis_client:
            return False

        try:
            self.redis_client.flushdb()
            logger.info("Redis cache cleared")
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.redis_client:
            return False

        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    def get_stats(self) -> dict:
        """Get Redis cache statistics"""
        if not self.redis_client:
            return {'backend': 'redis', 'status': 'disconnected'}

        try:
            info = self.redis_client.info()
            return {
                'backend': 'redis',
                'total_keys': self.redis_client.dbsize(),
                'memory_used_mb': round(info.get('used_memory', 0) / (1024 * 1024), 2),
                'connected_clients': info.get('connected_clients', 0),
                'ttl': self.ttl
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {'backend': 'redis', 'error': str(e)}


# Decorator for caching function results
def cached(cache_manager: CacheManager, ttl: Optional[int] = None, key_prefix: str = ''):
    """
    Decorator to cache function results

    Args:
        cache_manager: CacheManager instance
        ttl: Optional custom TTL for this function
        key_prefix: Optional prefix for cache keys

    Usage:
        @cached(cache_manager, ttl=600, key_prefix='api_')
        def expensive_function(url):
            return fetch_data(url)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{key_prefix}{func.__name__}_{CacheManager.generate_key(*args, **kwargs)}"

            # Try to get from cache
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {func.__name__}")
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(key, result, ttl)
            logger.debug(f"Cache miss: {func.__name__}, result cached")

            return result

        return wrapper

    return decorator


# TTL Cache decorator (alternative implementation)
def ttl_cache(ttl_seconds: int = 3600, maxsize: int = 128):
    """
    Decorator for TTL-based caching using functools.lru_cache

    Args:
        ttl_seconds: Time to live in seconds
        maxsize: Maximum cache size

    Usage:
        @ttl_cache(ttl_seconds=600, maxsize=256)
        def fetch_page(url):
            return requests.get(url)
    """

    def decorator(func: Callable) -> Callable:
        @lru_cache(maxsize=maxsize)
        def cached_with_ttl(ttl_hash, *args, **kwargs):
            return func(*args, **kwargs)

        @wraps(func)
        def wrapper(*args, **kwargs):
            ttl_hash = int(time.time() / ttl_seconds)
            return cached_with_ttl(ttl_hash, *args, **kwargs)

        wrapper.cache_clear = cached_with_ttl.cache_clear
        wrapper.cache_info = cached_with_ttl.cache_info

        return wrapper

    return decorator
