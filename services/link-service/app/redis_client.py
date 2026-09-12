"""Redis client for link-service (write-through cache)."""
import os
from typing import Optional

import redis.asyncio as aioredis

_redis: aioredis.Redis | None = None

DEFAULT_TTL = 60 * 60 * 24 * 30  # 30 days in seconds


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis


async def init_redis() -> None:
    global _redis
    redis_url = os.environ["REDIS_URL"]
    _redis = aioredis.from_url(redis_url, decode_responses=True)


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


async def set_link(short_code: str, long_url: str, ttl_seconds: Optional[int] = None) -> None:
    r = get_redis()
    key = f"short:{short_code}"
    if ttl_seconds:
        await r.set(key, long_url, ex=ttl_seconds)
    else:
        await r.set(key, long_url, ex=DEFAULT_TTL)


async def get_link(short_code: str) -> Optional[str]:
    r = get_redis()
    return await r.get(f"short:{short_code}")
