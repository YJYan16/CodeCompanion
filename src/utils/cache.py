from cachetools import TTLCache, cached
from functools import wraps
import hashlib

DEFAULT_CACHE_SIZE = 128
DEFAULT_CACHE_TTL = 3600

def get_cache(maxsize=DEFAULT_CACHE_SIZE, ttl=DEFAULT_CACHE_TTL):
    return TTLCache(maxsize=maxsize, ttl=ttl)

def cached_with_ttl(maxsize=DEFAULT_CACHE_SIZE, ttl=DEFAULT_CACHE_TTL):
    cache = TTLCache(maxsize=maxsize, ttl=ttl)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = _make_cache_key(args, kwargs)
            if key in cache:
                return cache[key]
            result = func(*args, **kwargs)
            cache[key] = result
            return result
        return wrapper
    return decorator

def _make_cache_key(args, kwargs):
    key_parts = []
    for arg in args:
        key_parts.append(str(arg))
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")
    key_str = ":".join(key_parts)
    return hashlib.md5(key_str.encode()).hexdigest()[:16]