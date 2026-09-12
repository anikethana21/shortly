"""Routes for link-service."""
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request

from .base62 import encode
from .db import get_db
from .kafka_producer import fire_and_forget
from .models import (
    AnalyticsResponse,
    CreateLinkRequest,
    LinkRecord,
    LinkResponse,
    RESERVED_CODES,
)
from .qr import generate_qr_base64
from .redis_client import set_link

router = APIRouter()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


@router.post("/api/links", response_model=LinkResponse, status_code=201)
async def create_link(req: CreateLinkRequest, request: Request):
    db = get_db()
    now = datetime.now(timezone.utc)
    long_url_str = str(req.long_url)

    # Determine expiry
    expires_at: Optional[datetime] = None
    ttl_seconds: Optional[int] = None
    if req.expires_in_minutes:
        expires_at = now + timedelta(minutes=req.expires_in_minutes)
        ttl_seconds = req.expires_in_minutes * 60

    # Determine short code
    if req.custom_code:
        short_code = req.custom_code
        existing = await db.links.find_one({"short_code": short_code})
        if existing:
            raise HTTPException(status_code=409, detail="Custom code already taken")
        is_custom = True
    else:
        # Atomic counter increment
        result = await db.counters.find_one_and_update(
            {"_id": "link_counter"},
            {"$inc": {"value": 1}},
            upsert=True,
            return_document=True,
        )
        counter_val = result["value"]
        short_code = encode(counter_val)
        is_custom = False

    # Generate QR code (inline, base64)
    short_url = f"{BASE_URL}/{short_code}"
    qr_b64 = generate_qr_base64(short_url)

    # Owner token
    owner_token = secrets.token_urlsafe(32)

    # Insert document
    doc = {
        "_id": str(uuid.uuid4()),
        "short_code": short_code,
        "long_url": long_url_str,
        "created_at": now,
        "expires_at": expires_at,
        "is_custom": is_custom,
        "click_count": 0,
        "verified": "pending",
        "owner_token": owner_token,
    }
    await db.links.insert_one(doc)

    # Write-through to Redis
    await set_link(short_code, long_url_str, ttl_seconds)

    # Publish to Kafka (fire-and-forget — never blocks response)
    fire_and_forget("link.verify", {"short_code": short_code, "long_url": long_url_str})

    return LinkResponse(
        short_code=short_code,
        short_url=short_url,
        long_url=long_url_str,
        qr_code_base64=qr_b64,
        created_at=now,
        expires_at=expires_at,
        is_custom=is_custom,
        verified="pending",
        owner_token=owner_token,
    )


@router.get("/api/links/mine", response_model=list[LinkRecord])
async def get_my_links(x_owner_token: str = Header(...)):
    db = get_db()
    cursor = db.links.find(
        {"owner_token": x_owner_token},
        sort=[("created_at", -1)],
    )
    docs = await cursor.to_list(length=200)
    return [
        LinkRecord(
            short_code=d["short_code"],
            long_url=d["long_url"],
            created_at=d["created_at"],
            expires_at=d.get("expires_at"),
            is_custom=d["is_custom"],
            click_count=d["click_count"],
            verified=d["verified"],
            owner_token=d["owner_token"],
        )
        for d in docs
    ]


@router.get("/api/analytics/{short_code}", response_model=AnalyticsResponse)
async def get_analytics(short_code: str):
    db = get_db()

    link = await db.links.find_one({"short_code": short_code})
    if not link:
        raise HTTPException(status_code=404, detail="Short code not found")

    # Clicks by date (from click_aggregates)
    agg_cursor = db.click_aggregates.find(
        {"short_code": short_code},
        sort=[("date", 1)],
    )
    agg_docs = await agg_cursor.to_list(length=365)
    clicks_by_date = [{"date": d["date"], "count": d["count"]} for d in agg_docs]

    # Top referrers
    pipeline = [
        {"$match": {"short_code": short_code}},
        {"$group": {"_id": "$referrer", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    ref_cursor = db.clicks.aggregate(pipeline)
    ref_docs = await ref_cursor.to_list(length=10)
    top_referrers = [{"referrer": d["_id"] or "direct", "count": d["count"]} for d in ref_docs]

    return AnalyticsResponse(
        short_code=short_code,
        total_clicks=link.get("click_count", 0),
        clicks_by_date=clicks_by_date,
        top_referrers=top_referrers,
    )


@router.get("/health")
async def health():
    return {"status": "ok", "service": "link-service"}
