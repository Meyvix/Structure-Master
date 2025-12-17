"""
Stracture-Master - Cache Manager Module
Manages smart caching for improved scan performance.
"""

import json
import hashlib
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict

from ..config import Config
from .logger import Logger


@dataclass
class CacheEntry:
    """Single cache entry."""
    key: str
    data: Any
    created: datetime
    expires: datetime
    hits: int = 0
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'data': self.data,
            'created': self.created.isoformat(),
            'expires': self.expires.isoformat(),
            'hits': self.hits,
            'size_bytes': self.size_bytes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        return cls(
            key=data['key'],
            data=data['data'],
            created=datetime.fromisoformat(data['created']),
            expires=datetime.fromisoformat(data['expires']),
            hits=data.get('hits', 0),
            size_bytes=data.get('size_bytes', 0),
        )


class CacheManager:
    """
    Manages smart caching for scan results and other data.
    Features:
    - Memory and disk caching
    - TTL-based expiration
    - Size limits
    - Hit statistics
    """
    
    def __init__(self,
                 cache_dir: Optional[Path] = None,
                 max_memory_mb: float = 100,
                 max_disk_mb: float = 500,
                 default_ttl_seconds: int = 3600):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for disk cache
            max_memory_mb: Maximum memory cache size
            max_disk_mb: Maximum disk cache size
            default_ttl_seconds: Default TTL for entries
        """
        self.logger = Logger.get_instance()
        self.cache_dir = cache_dir or Config.get_paths().cache
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.max_disk_bytes = int(max_disk_mb * 1024 * 1024)
        self.default_ttl = timedelta(seconds=default_ttl_seconds)
        
        # In-memory cache
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._memory_size = 0
        self._lock = threading.Lock()
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
        }
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        # Check memory cache first
        with self._lock:
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                if not entry.is_expired():
                    entry.hits += 1
                    self._stats['hits'] += 1
                    return entry.data
                else:
                    # Remove expired entry
                    self._remove_memory_entry(key)
        
        # Check disk cache
        disk_entry = self._get_from_disk(key)
        if disk_entry and not disk_entry.is_expired():
            # Promote to memory cache
            with self._lock:
                self._add_to_memory(disk_entry)
                self._stats['hits'] += 1
            return disk_entry.data
        
        self._stats['misses'] += 1
        return None
    
    def set(self, key: str, data: Any, 
            ttl: Optional[timedelta] = None,
            persist: bool = False) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live (default: default_ttl)
            persist: Also save to disk
        """
        ttl = ttl or self.default_ttl
        now = datetime.now()
        
        # Estimate size
        try:
            size_bytes = len(json.dumps(data, default=str).encode())
        except:
            size_bytes = 1000
        
        entry = CacheEntry(
            key=key,
            data=data,
            created=now,
            expires=now + ttl,
            size_bytes=size_bytes,
        )
        
        with self._lock:
            # Evict if needed to make space
            self._ensure_memory_space(size_bytes)
            self._add_to_memory(entry)
        
        if persist:
            self._save_to_disk(entry)
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was deleted
        """
        deleted = False
        
        with self._lock:
            if key in self._memory_cache:
                self._remove_memory_entry(key)
                deleted = True
        
        # Also delete from disk
        disk_path = self._get_disk_path(key)
        if disk_path.exists():
            disk_path.unlink()
            deleted = True
        
        return deleted
    
    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._memory_cache.clear()
            self._memory_size = 0
        
        # Clear disk cache
        for file in self.cache_dir.glob('*.cache'):
            try:
                file.unlink()
            except:
                pass
    
    def clear_expired(self) -> int:
        """
        Clear expired entries.
        
        Returns:
            Number of entries cleared
        """
        cleared = 0
        
        # Clear expired memory entries
        with self._lock:
            expired_keys = [
                key for key, entry in self._memory_cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                self._remove_memory_entry(key)
                cleared += 1
        
        # Clear expired disk entries
        for file in self.cache_dir.glob('*.cache'):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    entry = CacheEntry.from_dict(json.load(f))
                if entry.is_expired():
                    file.unlink()
                    cleared += 1
            except:
                pass
        
        return cleared
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            memory_entries = len(self._memory_cache)
            memory_size = self._memory_size
        
        disk_entries = len(list(self.cache_dir.glob('*.cache')))
        disk_size = sum(f.stat().st_size for f in self.cache_dir.glob('*.cache'))
        
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'memory_entries': memory_entries,
            'memory_size_bytes': memory_size,
            'memory_size_mb': memory_size / (1024 * 1024),
            'disk_entries': disk_entries,
            'disk_size_bytes': disk_size,
            'disk_size_mb': disk_size / (1024 * 1024),
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'hit_rate': hit_rate,
            'evictions': self._stats['evictions'],
        }
    
    def _add_to_memory(self, entry: CacheEntry) -> None:
        """Add entry to memory cache."""
        if entry.key in self._memory_cache:
            self._memory_size -= self._memory_cache[entry.key].size_bytes
        
        self._memory_cache[entry.key] = entry
        self._memory_size += entry.size_bytes
    
    def _remove_memory_entry(self, key: str) -> None:
        """Remove entry from memory cache."""
        if key in self._memory_cache:
            self._memory_size -= self._memory_cache[key].size_bytes
            del self._memory_cache[key]
    
    def _ensure_memory_space(self, needed_bytes: int) -> None:
        """Ensure there's enough space in memory cache."""
        while self._memory_size + needed_bytes > self.max_memory_bytes:
            if not self._memory_cache:
                break
            
            # Evict oldest entry
            oldest_key = min(
                self._memory_cache,
                key=lambda k: self._memory_cache[k].created
            )
            self._remove_memory_entry(oldest_key)
            self._stats['evictions'] += 1
    
    def _get_disk_path(self, key: str) -> Path:
        """Get disk path for a cache key."""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def _save_to_disk(self, entry: CacheEntry) -> None:
        """Save entry to disk."""
        try:
            disk_path = self._get_disk_path(entry.key)
            with open(disk_path, 'w', encoding='utf-8') as f:
                json.dump(entry.to_dict(), f, default=str)
        except Exception as e:
            self.logger.debug(f"Failed to save cache to disk: {e}")
    
    def _get_from_disk(self, key: str) -> Optional[CacheEntry]:
        """Get entry from disk cache."""
        disk_path = self._get_disk_path(key)
        
        if not disk_path.exists():
            return None
        
        try:
            with open(disk_path, 'r', encoding='utf-8') as f:
                return CacheEntry.from_dict(json.load(f))
        except Exception as e:
            self.logger.debug(f"Failed to load cache from disk: {e}")
            return None


# Create singleton instance
cache_manager = CacheManager()
