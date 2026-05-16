"""Redis client — singleton connection with graceful degradation.

When Redis is unavailable, all operations are no-ops (no crash),
so the app works with or without Redis being online.
"""
import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)

_redis = None
_redis_available = False


def _get_redis():
    """Lazy-init Redis connection. Returns None if unavailable."""
    global _redis, _redis_available
    if _redis is not None:
        return _redis if _redis_available else None
    try:
        import redis.asyncio as aioredis
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        _redis_available = True
        logger.info("Redis connected: %s", settings.REDIS_URL)
    except Exception as e:
        logger.warning("Redis unavailable, caching disabled: %s", e)
        _redis_available = False
        _redis = None
    return _redis if _redis_available else None


async def get_cache(key: str) -> dict | None:
    """Get a cached JSON value. Returns None on miss or unavailable."""
    r = _get_redis()
    if r is None:
        return None
    try:
        val = await r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


async def set_cache(key: str, value: dict, ttl_seconds: int = 3600) -> None:
    """Set a cached JSON value with TTL."""
    r = _get_redis()
    if r is None:
        return
    try:
        await r.set(key, json.dumps(value), ex=ttl_seconds)
    except Exception:
        pass


async def delete_cache(key: str) -> None:
    """Delete a cache key."""
    r = _get_redis()
    if r is None:
        return
    try:
        await r.delete(key)
    except Exception:
        pass


async def cache_or_compute(
    key: str,
    compute_fn,
    ttl_seconds: int = 3600,
) -> dict:
    """Get from cache or compute and store. compute_fn is an async callable."""
    cached = await get_cache(key)
    if cached is not None:
        return cached
    result = await compute_fn()
    if result is not None:
        await set_cache(key, result, ttl_seconds)
    return result
