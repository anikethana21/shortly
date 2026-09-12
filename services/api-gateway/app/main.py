"""api-gateway — thin reverse proxy. Single public entrypoint for the frontend."""
import logging
import os

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [api-gateway] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

LINK_SERVICE_URL = os.environ.get("LINK_SERVICE_URL", "http://link-service:8001")
REDIRECT_SERVICE_URL = os.environ.get("REDIRECT_SERVICE_URL", "http://redirect-service:8002")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI(
    title="Short.ly — API Gateway",
    description="Thin reverse proxy. Routes /api/* to link-service, everything else to redirect-service.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi import Request as _Req
from fastapi.responses import PlainTextResponse
import traceback as _tb

@app.exception_handler(Exception)
async def _global_exc_handler(request: _Req, exc: Exception):
    tb = _tb.format_exc()
    logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url, tb)
    return PlainTextResponse(f"500 Internal Server Error\n\n{tb}", status_code=500)


# Shared async HTTP client — reused across requests
_client: httpx.AsyncClient | None = None


@app.on_event("startup")
async def startup():
    global _client
    _client = httpx.AsyncClient(timeout=30.0, follow_redirects=False, http2=False)
    logger.info(
        "api-gateway started | link-service=%s | redirect-service=%s",
        LINK_SERVICE_URL,
        REDIRECT_SERVICE_URL,
    )


@app.on_event("shutdown")
async def shutdown():
    global _client
    if _client:
        await _client.aclose()


def _hop_by_hop_headers():
    return {
        "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
        "te", "trailer", "transfer-encoding", "upgrade", "host",
    }


async def _proxy(request: Request, target_base: str) -> Response:
    path = request.url.path
    query = request.url.query
    url = f"{target_base}{path}"
    if query:
        url = f"{url}?{query}"

    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in _hop_by_hop_headers()
    }
    # Force identity encoding upstream so we receive raw bytes we can forward as-is
    headers["Accept-Encoding"] = "identity"
    # Pass real client IP downstream
    headers["X-Forwarded-For"] = request.client.host

    body = await request.body()

    try:
        upstream = await _client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )
    except Exception as exc:
        logger.exception("Upstream request failed: %s -> %s", request.method, url)
        return Response(content=f"Gateway upstream error: {exc}", status_code=502)

    response_headers = {
        k: v
        for k, v in upstream.headers.items()
        if k.lower() not in _hop_by_hop_headers() | {"content-encoding", "content-length", "transfer-encoding"}
    }

    content_encoding = upstream.headers.get("content-encoding", "").lower()
    body_bytes = upstream.content  # httpx decodes gzip/deflate automatically

    # httpx does NOT decode brotli — handle it explicitly
    if content_encoding == "br":
        try:
            import brotli  # type: ignore
            body_bytes = brotli.decompress(body_bytes)
            logger.info("Brotli-decoded upstream response (%d bytes)", len(body_bytes))
        except Exception as exc:
            logger.warning("brotli decompress failed: %s — forwarding raw bytes", exc)

    logger.info(
        "%s %s -> %s %d bytes (enc=%s)",
        request.method, url, upstream.status_code, len(body_bytes), content_encoding or "none",
    )

    return Response(
        content=body_bytes,
        status_code=upstream.status_code,
        headers=response_headers,
    )


@app.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_to_link_service(request: Request, path: str):
    return await _proxy(request, LINK_SERVICE_URL)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-gateway"}


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_to_redirect_service(request: Request, path: str):
    return await _proxy(request, REDIRECT_SERVICE_URL)
