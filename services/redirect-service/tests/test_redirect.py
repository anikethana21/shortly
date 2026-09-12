"""Tests for redirect-service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


# ── Fixtures ───────────────────────────────────────────────────────────────

def _make_client(redis_return=None, mongo_return=None):
    """Build a TestClient with mocked Redis, MongoDB, and Kafka."""
    with (
        patch("app.db._db") as mock_db,
        patch("app.redis_client._redis") as mock_redis,
        patch("app.kafka_producer._producer", None),
    ):
        mock_redis.get = AsyncMock(return_value=redis_return)
        mock_redis.set = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=[1, 0])  # allowed, retry_after=0

        mock_col = AsyncMock()
        mock_col.find_one = AsyncMock(return_value=mongo_return)
        mock_col.delete_one = AsyncMock()
        mock_db.links = mock_col

        from app.main import app
        return TestClient(app, raise_server_exceptions=False)


# ── Cache hit → 302 ────────────────────────────────────────────────────────

def test_redirect_cache_hit_302():
    from app.metrics import redis_cache_hits_total
    before = redis_cache_hits_total._value.get()

    client = _make_client(redis_return="https://example.com")
    resp = client.get("/abc123", allow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["location"] == "https://example.com"
    assert redis_cache_hits_total._value.get() > before


# ── Cache miss + MongoDB found → 302 ──────────────────────────────────────

def test_redirect_cache_miss_mongo_hit_302():
    from app.metrics import redis_cache_misses_total
    before = redis_cache_misses_total._value.get()

    mongo_doc = {
        "short_code": "abc123",
        "long_url": "https://example.com",
        "expires_at": None,
    }
    client = _make_client(redis_return=None, mongo_return=mongo_doc)
    resp = client.get("/abc123", allow_redirects=False)

    assert resp.status_code == 302
    assert redis_cache_misses_total._value.get() > before


# ── Not found → 404 ───────────────────────────────────────────────────────

def test_redirect_not_found_404():
    client = _make_client(redis_return=None, mongo_return=None)
    resp = client.get("/doesnotexist", allow_redirects=False)
    assert resp.status_code == 404


# ── Expired link → 410 ────────────────────────────────────────────────────

def test_redirect_expired_link_410():
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    mongo_doc = {
        "short_code": "expired1",
        "long_url": "https://example.com",
        "expires_at": past,
    }
    client = _make_client(redis_return=None, mongo_return=mongo_doc)
    resp = client.get("/expired1", allow_redirects=False)
    assert resp.status_code == 410


# ── Rate limit → 429 + Retry-After ────────────────────────────────────────

def test_rate_limit_429():
    with (
        patch("app.db._db") as mock_db,
        patch("app.redis_client._redis") as mock_redis,
        patch("app.kafka_producer._producer", None),
    ):
        mock_redis.get = AsyncMock(return_value=None)
        # Lua returns [0, 12] → not allowed, retry after 12s
        mock_redis.eval = AsyncMock(return_value=[0, 12])

        from app.metrics import rate_limit_rejections_total
        before = rate_limit_rejections_total._value.get()

        from app.main import app
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/anycode", allow_redirects=False)

        assert resp.status_code == 429
        assert "Retry-After" in resp.headers
        assert int(resp.headers["Retry-After"]) == 12
        assert rate_limit_rejections_total._value.get() > before
