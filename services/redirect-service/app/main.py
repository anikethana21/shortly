"""redirect-service FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from .db import close_db, init_db
from .kafka_producer import close_producer, init_producer
from .redis_client import close_redis, init_redis
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_redis()
    await init_producer()
    yield
    await close_producer()
    await close_redis()
    await close_db()


app = FastAPI(
    title="Short.ly — Redirect Service",
    description="Handles short-code resolution and HTTP 302 redirects.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus instrumentation — exposes /metrics
Instrumentator().instrument(app).expose(app)

app.include_router(router)
