from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.config.settings import settings
from app.infrastructure.sqlalchemy.sqlalchemy import init_models
from app.presentation.api.exception_handler import register_exception_handlers
from app.presentation.api.routes.auth import router as auth_router
from app.presentation.api.routes.oauth import router as oauth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Before the start of the app

    await init_models()

    yield
    # Before the closing of the app


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origines,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(oauth_router)
