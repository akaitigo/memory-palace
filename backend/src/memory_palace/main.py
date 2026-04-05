"""Memory Palace - FastAPI application entry point."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from memory_palace.api.auth import router as auth_router
from memory_palace.api.health import router as health_router
from memory_palace.api.reviews import router as reviews_router
from memory_palace.api.rooms import router as rooms_router


def _validate_jwt_secret() -> None:
    """Validate that JWT_SECRET is configured at startup.

    Raises:
        SystemExit: If JWT_SECRET is not set or is empty.
    """
    secret = os.environ.get("JWT_SECRET", "")
    if not secret:
        msg = (
            "FATAL: JWT_SECRET environment variable is not set. "
            "Set a strong secret key (min 32 chars) before starting the server."
        )
        raise SystemExit(msg)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler — validates configuration at startup."""
    _validate_jwt_secret()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Memory Palace API",
        description="記憶宮殿バックエンド API",
        version="0.1.0",
        lifespan=lifespan,
    )

    cors_origins_raw = os.environ.get("CORS_ORIGINS", "")
    cors_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(rooms_router)
    app.include_router(reviews_router)

    return app


app = create_app()
