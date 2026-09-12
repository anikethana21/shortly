"""MongoDB client for link-service."""
import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db


async def init_db() -> None:
    global _client, _db
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.getenv("MONGO_DB_NAME", "shortly")
    _client = AsyncIOMotorClient(mongo_url)
    _db = _client[db_name]
    # Ensure indexes
    await _db.links.create_index("short_code", unique=True)
    await _db.links.create_index("owner_token")
    await _db.links.create_index("expires_at")
    await _db.counters.create_index("_id")
    await _db.clicks.create_index("short_code")
    await _db.click_aggregates.create_index(
        [("short_code", 1), ("date", 1)], unique=True
    )


async def close_db() -> None:
    global _client
    if _client:
        _client.close()
        _client = None
