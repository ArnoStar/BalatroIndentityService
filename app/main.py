from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.sqlalchemy.sqlalchemy import init_models
from app.presentation.api.routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Before the start of the app

    await init_models()

    yield
    # Before the closing of the app


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
