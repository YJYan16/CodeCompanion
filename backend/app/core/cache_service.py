# backend/app/core/cache_service.py
import hashlib
import json
import asyncio
from typing import Optional, Any, Callable, Union
from cachetools import TTLCache
from functools import wraps
import time
import importlib
from abc import ABC, abstractmethod

try:
    import orjson as json_lib
    HAS_ORJSON = True
except ImportError:
    import json as json_lib
    HAS_ORJSON = False


class CacheLayer(ABC):
    """缓存层抽象基类"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    def clear(self) -> None:
        pass
    
    @abstractmethod
    def get_stats(self) -> dict:
        pass


class LRUCacheLayer(CacheLayer):
    """内存LRU缓存层，使用cachetools的TTLCache实现，支持自动过期"""

    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0
        }

    def get(self, key: str) -> Optional[Any]:
        try:
            value = self.cache[key]
            self.stats["hits"] += 1
            return value
        except KeyError:
            self.stats["misses"] += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self.cache[key] = value
        self.stats["sets"] += 1

    def delete(self, key: str) -> bool:
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> None:
        self.cache.clear()

    def get_stats(self) -> dict:
        total = self.stats["hits"] + self.stats["misses"]
        return {
            "type": "lru_cache",
            "size": len(self.cache),
            "maxsize": self.cache.maxsize,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": self.stats["hits"] / total if total > 0 else 0
        }


class RedisCacheLayer(CacheLayer):
    """Redis缓存层（可选依赖）"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.redis_client = None
        self.connected = False
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0
        }
        self._init_redis()

    def _init_redis(self):
        """初始化Redis连接，失败则优雅降级"""
        # 先检查redis模块是否安装
        try:
            redis_spec = importlib.util.find_spec('redis')
            if redis_spec is None:
                print("redis模块未安装，将仅使用内存缓存")
                return
        except Exception:
            print("redis模块未安装，将仅使用内存缓存")
            return
        
        try:
            import redis
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # 测试连接
            self.redis_client.ping()
            self.connected = True
            print(f"Redis连接成功: {self.host}:{self.port}")
        except Exception as e:
            print(f"Redis连接失败: {e}, 将仅使用内存缓存")
            self.connected = False

    def get(self, key: str) -> Optional[Any]:
        if not self.connected:
            return None
        try:
            value = self.redis_client.get(key)
            if value:
                self.stats["hits"] += 1
                try:
                    return json_lib.loads(value)
                except:
                    return value
            else:
                self.stats["misses"] += 1
                return None
        except Exception as e:
            self.stats["errors"] += 1
            print(f"Redis读取错误: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self.connected:
            return
        try:
            serialized = json_lib.dumps(value)
            if ttl:
                self.redis_client.setex(key, ttl, serialized)
            else:
                self.redis_client.set(key, serialized)
            self.stats["sets"] += 1
        except Exception as e:
            self.stats["errors"] += 1
            print(f"Redis写入错误: {e}")

    def delete(self, key: str) -> bool:
        if not self.connected:
            return False
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            self.stats["errors"] += 1
            return False

    def clear(self) -> None:
        if self.connected:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                print(f"Redis清空错误: {e}")

    def get_stats(self) -> dict:
        total = self.stats["hits"] + self.stats["misses"]
        return {
            "type": "redis_cache",
            "connected": self.connected,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "errors": self.stats["errors"],
            "hit_rate": self.stats["hits"] / total if total > 0 else 0
        }


class TwoLayerCache(CacheLayer):
    """双层缓存：LRU内存缓存 + Redis缓存（可选）"""

    def __init__(self, lru_maxsize: int = 1000, lru_ttl: int = 3600, 
                 redis_host: str = "localhost", redis_port: int = 6379, 
                 redis_db: int = 0, redis_password: Optional[str] = None,
                 namespace: str = "code_companion",
                 use_redis: bool = False):
        self.lru_cache = LRUCacheLayer(maxsize=lru_maxsize, ttl=lru_ttl)
        self.use_redis = use_redis
        self.namespace = namespace
        
        self.redis_cache = RedisCacheLayer(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password
        ) if use_redis else None
        
        if use_redis:
            print(f"双层缓存初始化完成 (命名空间: {namespace}, Redis: {'启用' if use_redis else '禁用'})")
        else:
            print(f"内存LRU缓存初始化完成 (命名空间: {namespace})")

    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_str = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        hash_obj = hashlib.sha256(key_str.encode('utf-8'))
        return f"{self.namespace}:{hash_obj.hexdigest()}"

    def get(self, prefix: str, *args, **kwargs) -> Optional[Any]:
        """从缓存获取数据"""
        key = self._make_key(prefix, *args, **kwargs)
        
        # 首先尝试内存缓存
        value = self.lru_cache.get(key)
        if value is not None:
            return value
            
        # 再尝试Redis缓存
        if self.use_redis and self.redis_cache is not None:
            value = self.redis_cache.get(key)
            if value is not None:
                self.lru_cache.set(key, value)
                return value
            
        return None

    def set(self, prefix: str, value: Any, ttl: Optional[int] = None, *args, **kwargs) -> None:
        """设置缓存"""
        key = self._make_key(prefix, *args, **kwargs)
        self.lru_cache.set(key, value, ttl)
        if self.use_redis and self.redis_cache is not None:
            self.redis_cache.set(key, value, ttl)

    def delete(self, prefix: str, *args, **kwargs) -> bool:
        """删除缓存"""
        key = self._make_key(prefix, *args, **kwargs)
        lru_deleted = self.lru_cache.delete(key)
        redis_deleted = False
        if self.use_redis and self.redis_cache is not None:
            redis_deleted = self.redis_cache.delete(key)
        return lru_deleted or redis_deleted

    def clear(self) -> None:
        """清空所有缓存"""
        self.lru_cache.clear()
        if self.use_redis and self.redis_cache is not None:
            self.redis_cache.clear()

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        stats = {
            "lru_cache": self.lru_cache.get_stats(),
            "use_redis": self.use_redis
        }
        if self.use_redis and self.redis_cache is not None:
            stats["redis_cache"] = self.redis_cache.get_stats()
        return stats


_cache_instance: Optional[TwoLayerCache] = None


def init_cache(namespace: str = "code_companion", 
               lru_maxsize: int = 1000, 
               lru_ttl: int = 3600,
               redis_host: str = "localhost", 
               redis_port: int = 6379,
               redis_db: int = 0,
               redis_password: Optional[str] = None,
               use_redis: bool = False):
    """初始化全局缓存"""
    global _cache_instance
    _cache_instance = TwoLayerCache(
        lru_maxsize=lru_maxsize,
        lru_ttl=lru_ttl,
        redis_host=redis_host,
        redis_port=redis_port,
        redis_db=redis_db,
        redis_password=redis_password,
        namespace=namespace,
        use_redis=use_redis
    )
    return _cache_instance


def get_cache() -> TwoLayerCache:
    """获取全局缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = TwoLayerCache(use_redis=False)
    return _cache_instance


def cached(prefix: str, ttl: Optional[int] = 3600):
    """缓存装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache()
            result = cache.get(prefix, *args, **kwargs)
            if result is not None:
                return result
            result = await func(*args, **kwargs)
            cache.set(prefix, result, ttl, *args, **kwargs)
            return result
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache()
            result = cache.get(prefix, *args, **kwargs)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache.set(prefix, result, ttl, *args, **kwargs)
            return result
            
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
