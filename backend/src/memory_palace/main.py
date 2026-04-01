"""Memory Palace - FastAPI application entry point."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from memory_palace.api.health import router as health_router
from memory_palace.api.reviews import router as reviews_router
from memory_palace.api.rooms import router as rooms_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Memory Palace API",
        description="記憶宮殿バックエンド API",
        version="0.1.0",
    )

    cors_origins_raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
    cors_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    app.include_router(health_router)
    app.include_router(rooms_router)
    app.include_router(reviews_router)

    return app


app = create_app()
