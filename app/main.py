from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Before the start of the app
    yield
    # Before the closing of the app


app = FastAPI(lifespan=lifespan)
