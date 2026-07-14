"""
Prompt 缓存层与性能优化模块
实现 TTL 缓存、LRU 驱逐、缓存预热与命中率统计。
"""
from __future__ import annotations
import time
import threading
import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class CacheStats:
    """缓存统计快照"""
    hits: int
    misses: int
    evictions: int
    size: int
    hit_rate: float

    def __str__(self) -> str:
        return (
            f"Cache(hits={self.hits}, misses={self.misses}, "
            f"evictions={self.evictions}, size={self.size}, "
            f"hit_rate={self.hit_rate:.1%})"
        )

@dataclass
class CacheEntry:
    value: Any
    expires_at: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)

@dataclass
class PromptCache:
    """支持 TTL + LRU 的 Prompt 渲染结果缓存"""
    max_size: int = 1024
    default_ttl: float = 300.0
    _store: OrderedDict[str, CacheEntry] = field(default_factory=OrderedDict)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)
    _hits: int = 0
    _misses: int = 0
    _evictions: int = 0

    def get(self, key: str) -> Any | None:
        """获取缓存值，命中则更新访问计数"""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            if time.time() > entry.expires_at:
                del self._store[key]
                self._misses += 1
                return None
            entry.access_count += 1
            entry.last_access = time.time()
            self._store.move_to_end(key)
            self._hits += 1
            return entry.value

    def put(self, key: str, value: Any, ttl: float | None = None) -> None:
        """写入缓存，超出容量时驱逐 LRU 条目"""
        with self._lock:
            ttl = ttl or self.default_ttl
            if key in self._store:
                self._store[key] = CacheEntry(value, time.time() + ttl)
                self._store.move_to_end(key)
                return
            if len(self._store) >= self.max_size:
                self._store.popitem(last=False)
                self._evictions += 1
            self._store[key] = CacheEntry(value, time.time() + ttl)

    def invalidate(self, key: str) -> bool:
        """主动失效指定缓存键"""
        with self._lock:
            return self._store.pop(key, None) is not None

    def invalidate_pattern(self, pattern: str) -> int:
        """批量失效匹配前缀的缓存键"""
        with self._lock:
            to_remove = [k for k in self._store if k.startswith(pattern)]
            for k in to_remove:
                del self._store[k]
            return len(to_remove)

    def warmup(self, keys: list[str], loader: Callable[[str], Any]) -> int:
        """缓存预热：批量加载并缓存指定键"""
        loaded = 0
        for key in keys:
            try:
                value = loader(key)
                self.put(key, value)
                loaded += 1
            except Exception as exc:
                logger.warning("Warmup failed for key %s: %s", key, exc)
        logger.info("Cache warmup: %d/%d entries loaded", loaded, len(keys))
        return loaded

    def stats(self) -> CacheStats:
        total = self._hits + self._misses
        return CacheStats(
            hits=self._hits,
            misses=self._misses,
            evictions=self._evictions,
            size=len(self._store),
            hit_rate=self._hits / total if total > 0 else 0.0
        )

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
