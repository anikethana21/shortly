"""verification-worker — Kafka consumer that verifies URLs via HTTP HEAD."""
import asyncio
import json
import logging
import os

import httpx
from aiokafka import AIOKafkaConsumer
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [verification-worker] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def get_db():
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.getenv("MONGO_DB_NAME", "shortly")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]


async def verify_url(long_url: str) -> str:
    """Returns 'verified' or 'unreachable'."""
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            resp = await client.head(long_url)
            if resp.status_code < 500:
                return "verified"
            return "unreachable"
    except Exception as exc:
        logger.warning("HEAD %s failed: %s", long_url, exc)
        return "unreachable"


async def process_message(db, data: dict) -> None:
    short_code = data.get("short_code")
    long_url = data.get("long_url")

    if not short_code or not long_url:
        logger.warning("Malformed message: %s", data)
        return

    status = await verify_url(long_url)
    await db.links.update_one(
        {"short_code": short_code},
        {"$set": {"verified": status}},
    )
    logger.info("Verified %s (%s) → %s", short_code, long_url, status)


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

    port = int(os.environ.get("PORT", "8004"))
    server = await asyncio.start_server(handle_health, "0.0.0.0", port)
    logger.info("verification-worker health server listening on port %d", port)
    return server


async def main() -> None:
    health_srv = await _health_server()
    bootstrap = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
    sasl_username = os.environ.get("KAFKA_USERNAME")
    sasl_password = os.environ.get("KAFKA_PASSWORD")

    consumer_kwargs = dict(
        bootstrap_servers=bootstrap,
        group_id="verification-workers",
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

    consumer = AIOKafkaConsumer("link.verify", **consumer_kwargs)
    db = get_db()

    await consumer.start()
    logger.info("verification-worker started, listening on link.verify")

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
        logger.info("verification-worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
