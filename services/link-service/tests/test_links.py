"""Tests for link-service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Base62 ─────────────────────────────────────────────────────────────────
from app.base62 import encode, decode


def test_base62_encode_zero():
    assert encode(0) == "0"


def test_base62_encode_decode_roundtrip():
    for n in [1, 62, 100, 99999, 3_844_000]:
        assert decode(encode(n)) == n


def test_base62_encode_is_alphanumeric():
    result = encode(123456789)
    assert result.isalnum()


# ── QR generation ──────────────────────────────────────────────────────────
from app.qr import generate_qr_base64
import base64


def test_qr_returns_nonempty_base64():
    b64 = generate_qr_base64("https://example.com/test")
    assert len(b64) > 0
    # Must be valid base64
    decoded = base64.b64decode(b64)
    # PNG magic bytes
    assert decoded[:8] == b"\x89PNG\r\n\x1a\n"


# ── Model validation ────────────────────────────────────────────────────────
from app.models import CreateLinkRequest
import pydantic


def test_valid_url_passes():
    req = CreateLinkRequest(long_url="https://example.com")
    assert str(req.long_url) == "https://example.com/"


def test_invalid_url_raises():
    with pytest.raises(pydantic.ValidationError):
        CreateLinkRequest(long_url="not-a-url")


def test_reserved_custom_code_raises():
    for code in ["api", "metrics", "dashboard", "expired", "health"]:
        with pytest.raises(pydantic.ValidationError):
            CreateLinkRequest(long_url="https://example.com", custom_code=code)


def test_custom_code_too_short_raises():
    with pytest.raises(pydantic.ValidationError):
        CreateLinkRequest(long_url="https://example.com", custom_code="ab")


def test_custom_code_too_long_raises():
    with pytest.raises(pydantic.ValidationError):
        CreateLinkRequest(long_url="https://example.com", custom_code="a" * 21)


def test_custom_code_non_alphanumeric_raises():
    with pytest.raises(pydantic.ValidationError):
        CreateLinkRequest(long_url="https://example.com", custom_code="bad-code!")


def test_valid_custom_code_passes():
    req = CreateLinkRequest(long_url="https://example.com", custom_code="mycode123")
    assert req.custom_code == "mycode123"


# ── Route-level tests (async, mocked deps) ─────────────────────────────────
import asyncio
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Provide a TestClient with all external deps mocked."""
    with (
        patch("app.db._db") as mock_db,
        patch("app.redis_client._redis") as mock_redis,
        patch("app.kafka_producer._producer", None),
    ):
        mock_col = AsyncMock()
        mock_col.find_one.return_value = None
        mock_col.insert_one.return_value = MagicMock()
        mock_col.find_one_and_update.return_value = {"value": 1}
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_db.links = mock_col
        mock_db.counters = mock_col

        mock_redis.set = AsyncMock()

        from app.main import app
        with TestClient(app) as c:
            yield c


def test_create_link_returns_201(client):
    resp = client.post("/api/links", json={"long_url": "https://example.com"})
    assert resp.status_code == 201
    data = resp.json()
    assert "short_code" in data
    assert "qr_code_base64" in data
    assert len(data["qr_code_base64"]) > 0
    assert data["verified"] == "pending"


def test_create_link_custom_code_conflict_409(client):
    with patch("app.db._db") as mock_db:
        mock_col = AsyncMock()
        mock_col.find_one.return_value = {"short_code": "taken"}
        mock_db.links = mock_col
        mock_db.counters = mock_col
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        resp = client.post(
            "/api/links",
            json={"long_url": "https://example.com", "custom_code": "taken"},
        )
        assert resp.status_code == 409
