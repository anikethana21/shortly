"""Redis client for redirect-service."""
import os
from typing import Optional

import redis.asyncio as aioredis

_redis: aioredis.Redis | None = None


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
