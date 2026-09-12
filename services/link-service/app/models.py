"""Pydantic models for link-service."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, field_validator


RESERVED_CODES = {"api", "metrics", "dashboard", "expired", "health", "rate-limited"}


class CreateLinkRequest(BaseModel):
    long_url: HttpUrl
    custom_code: Optional[str] = None
    expires_in_minutes: Optional[int] = None

    @field_validator("custom_code")
    @classmethod
    def validate_custom_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not (3 <= len(v) <= 20):
            raise ValueError("custom_code must be 3–20 characters")
        if not v.isalnum():
            raise ValueError("custom_code must be alphanumeric only")
        if v.lower() in RESERVED_CODES:
            raise ValueError(f"'{v}' is a reserved word")
        return v

    @field_validator("expires_in_minutes")
    @classmethod
    def validate_expiry(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("expires_in_minutes must be positive")
        return v


class LinkResponse(BaseModel):
    short_code: str
    short_url: str
    long_url: str
    qr_code_base64: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_custom: bool
    verified: str
    owner_token: str


class LinkRecord(BaseModel):
    short_code: str
    long_url: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_custom: bool
    click_count: int
    verified: str
    owner_token: str


class AnalyticsResponse(BaseModel):
    short_code: str
    total_clicks: int
    clicks_by_date: list[dict]
    top_referrers: list[dict]
