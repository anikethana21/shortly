"""Token-bucket rate limiter implemented as an atomic Redis Lua script."""
from typing import Tuple

import redis.asyncio as aioredis

# Lua script: atomic token-bucket rate limiter.
# Keys: KEYS[1] = bucket key (hash with fields: tokens, last_refill)
# Args: ARGV[1]=max_tokens, ARGV[2]=refill_rate (tokens/sec), ARGV[3]=now (unix ms), ARGV[4]=cost
_RATE_LIMIT_LUA = """
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now_ms = tonumber(ARGV[3])
local cost = tonumber(ARGV[4])

local data = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(data[1])
local last_refill = tonumber(data[2])

if tokens == nil then
    tokens = max_tokens
    last_refill = now_ms
end

-- Refill based on elapsed time
local elapsed_sec = (now_ms - last_refill) / 1000.0
local new_tokens = math.min(max_tokens, tokens + elapsed_sec * refill_rate)

local allowed = 0
local retry_after = 0

if new_tokens >= cost then
    new_tokens = new_tokens - cost
    allowed = 1
else
    -- seconds until enough tokens accumulate
    retry_after = math.ceil((cost - new_tokens) / refill_rate)
end

redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now_ms)
redis.call('EXPIRE', key, 120)

return {allowed, retry_after}
"""


async def check_rate_limit(
    redis: aioredis.Redis,
    ip: str,
    route: str,
    max_tokens: int = 100,
    refill_rate: float = 100 / 60,  # 100 per minute
) -> Tuple[bool, int]:
    """
    Returns (allowed, retry_after_seconds).
    Uses a single atomic EVAL call — no separate GET/SET.
    """
    import time

    key = f"ratelimit:{ip}:{route}"
    now_ms = int(time.time() * 1000)
    result = await redis.eval(
        _RATE_LIMIT_LUA,
        1,
        key,
        str(max_tokens),
        str(refill_rate),
        str(now_ms),
        "1",
    )
    allowed = bool(result[0])
    retry_after = int(result[1])
    return allowed, retry_after
