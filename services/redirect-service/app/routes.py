"""Redirect route — the hot path of Short.ly."""
import hashlib
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse

from .db import get_db
from .kafka_producer import fire_and_forget
from .metrics import (
    rate_limit_rejections_total,
    redis_cache_hits_total,
    redis_cache_misses_total,
)
from .rate_limit import check_rate_limit
from .redis_client import get_redis

router = APIRouter()

REDIS_DEFAULT_TTL = int(os.getenv("REDIS_DEFAULT_TTL", str(60 * 60 * 24 * 30)))


def _ip_hash(request: Request) -> str:
    ip = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


@router.get("/health")
async def health():
    return {"status": "ok", "service": "redirect-service"}


@router.get("/{short_code}")
async def redirect(short_code: str, request: Request):
    redis = get_redis()
    db = get_db()

    client_ip = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()
    referrer = request.headers.get("Referer", "")
    user_agent = request.headers.get("User-Agent", "")
    ip_hash = _ip_hash(request)

    # ── 1. Rate limit check (atomic Lua EVAL) ─────────────────────────────
    allowed, retry_after = await check_rate_limit(
        redis, client_ip, "redirect", max_tokens=100, refill_rate=100 / 60
    )
    if not allowed:
        rate_limit_rejections_total.inc()
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Slow down."},
            headers={"Retry-After": str(retry_after)},
        )

    # ── 2. Redis cache lookup ─────────────────────────────────────────────
    long_url = await redis.get(f"short:{short_code}")

    if long_url:
        redis_cache_hits_total.inc()
        _publish_click(short_code, referrer, user_agent, ip_hash)
        return RedirectResponse(url=long_url, status_code=302)

    # ── 3. Cache miss — query MongoDB ────────────────────────────────────
    redis_cache_misses_total.inc()
    doc = await db.links.find_one({"short_code": short_code})

    if not doc:
        return JSONResponse(status_code=404, content={"detail": "Short link not found"})

    # Check expiry
    expires_at = doc.get("expires_at")
    if expires_at:
        # Make tz-aware if naive
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            await db.links.delete_one({"short_code": short_code})
            return JSONResponse(status_code=410, content={"detail": "This link has expired"})

    # Repopulate Redis with remaining TTL
    long_url = doc["long_url"]
    if expires_at:
        remaining = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        if remaining > 0:
            await redis.set(f"short:{short_code}", long_url, ex=remaining)
    else:
        await redis.set(f"short:{short_code}", long_url, ex=REDIS_DEFAULT_TTL)

    _publish_click(short_code, referrer, user_agent, ip_hash)
    return RedirectResponse(url=long_url, status_code=302)


def _publish_click(short_code: str, referrer: str, user_agent: str, ip_hash: str) -> None:
    """Fire-and-forget Kafka publish. Redirect never fails because of this."""
    fire_and_forget(
        "link.clicked",
        {
            "short_code": short_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "referrer": referrer,
            "user_agent": user_agent,
            "ip_hash": ip_hash,
        },
    )
