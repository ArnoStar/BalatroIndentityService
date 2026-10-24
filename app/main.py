"""``uvicorn app.main:app``. Settings come from the environment (or .env):
see app/infrastructure/config/settings.py and .env.example."""

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap.container import Container
from app.infrastructure.config.settings import Settings, get_settings
from app.presentation.api.exception_handler import register_exception_handlers
from app.presentation.api.routes.auth import router as auth_router
from app.presentation.api.routes.meta import router as meta_router
from app.presentation.api.routes.oauth import router as oauth_router

DESCRIPTION = """
Accounts and sign-in for Balatro. Sign in with an email and a password, or
with a provider (Google); get an access token (an RS256 JWT, 15 minutes) and a
refresh token (single use, 30 days). Other services verify the access tokens
with the keys at `/.well-known/jwks.json`.
"""


def create_app(
    settings: Settings | None = None,
    container_factory: Callable[[Settings], Container] = Container,
) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        container = container_factory(settings)
        app.state.container = container
        yield
        await container.close()

    app = FastAPI(
        title="Balatro Identity Service",
        version="1.0.0",
        description=DESCRIPTION,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["Retry-After"],
    )
    register_exception_handlers(app)
    app.include_router(meta_router)
    app.include_router(auth_router)
    app.include_router(oauth_router)
    return app


logging.basicConfig(level=logging.INFO)
app = create_app()
