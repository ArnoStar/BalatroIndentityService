from contextlib import asynccontextmanager

from fastapi import FastAPI

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

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(oauth_router)
