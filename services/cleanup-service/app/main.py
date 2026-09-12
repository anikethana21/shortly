"""cleanup-service — APScheduler job that deletes expired links from MongoDB."""
import asyncio
import logging
import os
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [cleanup-service] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def get_db():
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.getenv("MONGO_DB_NAME", "shortly")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]


async def cleanup_expired(db) -> None:
    now = datetime.now(timezone.utc)
    result = await db.links.delete_many(
        {"expires_at": {"$lt": now, "$ne": None}}
    )
    if result.deleted_count > 0:
        logger.info("Cleaned up %d expired link(s)", result.deleted_count)
    else:
        logger.debug("No expired links to clean up")


async def main() -> None:
    db = get_db()
    interval_minutes = int(os.getenv("CLEANUP_INTERVAL_MINUTES", "15"))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        cleanup_expired,
        "interval",
        minutes=interval_minutes,
        args=[db],
        next_run_time=datetime.now(timezone.utc),  # run immediately on start
    )
    scheduler.start()
    logger.info(
        "cleanup-service started — running every %d minutes", interval_minutes
    )

    # Keep running until interrupted
    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("cleanup-service stopped")


if __name__ == "__main__":
    asyncio.run(main())
