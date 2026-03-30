"""Memory Palace - FastAPI application entry point."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from memory_palace.api.health import router as health_router
from memory_palace.api.rooms import router as rooms_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Memory Palace API",
        description="記憶宮殿バックエンド API",
        version="0.1.0",
    )

    cors_origins_raw = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
    cors_origins = [origin.strip() for origin in cors_origins_raw.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(rooms_router)

    return app


app = create_app()
