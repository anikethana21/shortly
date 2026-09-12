"""analytics-consumer — Kafka consumer writing click events to MongoDB."""
import asyncio
import json
import logging
import os
from datetime import datetime, timezone

from aiokafka import AIOKafkaConsumer
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [analytics-consumer] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def get_db():
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.getenv("MONGO_DB_NAME", "shortly")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]


async def process_message(db, data: dict) -> None:
    short_code = data.get("short_code")
    timestamp_str = data.get("timestamp", datetime.now(timezone.utc).isoformat())
    referrer = data.get("referrer", "")
    user_agent = data.get("user_agent", "")
    ip_hash = data.get("ip_hash", "")

    try:
        ts = datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError):
        ts = datetime.now(timezone.utc)

    date_str = ts.strftime("%Y-%m-%d")

    # Insert raw click
    await db.clicks.insert_one(
        {
            "short_code": short_code,
            "timestamp": ts,
            "referrer": referrer,
            "user_agent": user_agent,
            "ip_hash": ip_hash,
        }
    )

    # Upsert daily aggregate
    await db.click_aggregates.update_one(
        {"short_code": short_code, "date": date_str},
        {"$inc": {"count": 1}},
        upsert=True,
    )

    # Increment click_count on the link document
    await db.links.update_one(
        {"short_code": short_code},
        {"$inc": {"click_count": 1}},
    )

    logger.info("Processed click for %s on %s", short_code, date_str)


async def _health_server():
    async def handle_health(reader, writer):
        try:
            await reader.read(1024)
            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: application/json\r\n"
                b"Content-Length: 16\r\n\r\n"
                b"{\"status\":\"ok\"}\n"
            )
            writer.write(response)
            await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    port = int(os.environ.get("PORT", "8003"))
    server = await asyncio.start_server(handle_health, "0.0.0.0", port)
    logger.info("analytics-consumer health server listening on port %d", port)
    return server


async def main() -> None:
    health_srv = await _health_server()
    bootstrap = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
    sasl_username = os.environ.get("KAFKA_USERNAME")
    sasl_password = os.environ.get("KAFKA_PASSWORD")

    consumer_kwargs = dict(
        bootstrap_servers=bootstrap,
        group_id="analytics-workers",
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    if sasl_username and sasl_password:
        import ssl
        consumer_kwargs.update(
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-256",
            sasl_plain_username=sasl_username,
            sasl_plain_password=sasl_password,
            ssl_context=ssl.create_default_context(),
        )

    consumer = AIOKafkaConsumer("link.clicked", **consumer_kwargs)
    db = get_db()

    await consumer.start()
    logger.info("analytics-consumer started, listening on link.clicked")

    try:
        async for msg in consumer:
            try:
                await process_message(db, msg.value)
            except Exception as exc:
                logger.error("Error processing message: %s", exc)
    finally:
        await consumer.stop()
        health_srv.close()
        await health_srv.wait_closed()
        logger.info("analytics-consumer stopped")


if __name__ == "__main__":
    asyncio.run(main())
