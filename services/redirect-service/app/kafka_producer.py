"""Kafka producer for redirect-service — fire-and-forget click events."""
import asyncio
import json
import logging
import os
from typing import Any

from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)

_producer: AIOKafkaProducer | None = None


async def init_producer() -> None:
    global _producer
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "")
    if not bootstrap:
        logger.warning("KAFKA_BOOTSTRAP_SERVERS not set — Kafka disabled")
        return
    try:
        sasl_username = os.environ.get("KAFKA_USERNAME")
        sasl_password = os.environ.get("KAFKA_PASSWORD")
        if sasl_username and sasl_password:
            _producer = AIOKafkaProducer(
                bootstrap_servers=bootstrap,
                security_protocol="SASL_SSL",
                sasl_mechanism="SCRAM-SHA-256",
                sasl_plain_username=sasl_username,
                sasl_plain_password=sasl_password,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        else:
            _producer = AIOKafkaProducer(
                bootstrap_servers=bootstrap,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        await _producer.start()
        logger.info("Kafka producer started")
    except Exception as exc:
        logger.warning("Kafka producer failed to start: %s", exc)
        _producer = None


async def close_producer() -> None:
    global _producer
    if _producer:
        try:
            await _producer.stop()
        except Exception:
            pass
        _producer = None


def fire_and_forget(topic: str, message: dict[str, Any]) -> None:
    """Schedule a Kafka send as background task. Redirect NEVER fails because of this."""
    asyncio.create_task(_send(topic, message))


async def _send(topic: str, message: dict[str, Any]) -> None:
    if _producer is None:
        logger.debug("Kafka unavailable, dropping click event for %s", message)
        return
    try:
        await _producer.send_and_wait(topic, message)
    except Exception as exc:
        logger.warning("Kafka send to %s failed (non-fatal): %s", topic, exc)
