"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from safestreets.api.routes import router
from safestreets.config import get_settings

log = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from safestreets.store.redis_client import get_redis
        await get_redis().flushdb()
        log.info("Redis cache cleared on startup")
    except Exception:
        log.warning("Could not clear Redis cache on startup (Redis may not be running)")
    yield


app = FastAPI(title="Streets of Berkeley API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
