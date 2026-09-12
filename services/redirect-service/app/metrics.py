"""Prometheus counters for redirect-service."""
from prometheus_client import Counter

redis_cache_hits_total = Counter(
    "redis_cache_hits_total",
    "Total number of Redis cache hits for short code lookups",
)

redis_cache_misses_total = Counter(
    "redis_cache_misses_total",
    "Total number of Redis cache misses for short code lookups",
)

rate_limit_rejections_total = Counter(
    "rate_limit_rejections_total",
    "Total number of requests rejected by the rate limiter",
)
