from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import database
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await database.dispose()


app = FastAPI(title="Decision Provenance", lifespan=lifespan)
app.include_router(health.router)
