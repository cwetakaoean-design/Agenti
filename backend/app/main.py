"""Agenti FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import init_db
from app.routers import clients, health, orders, revenue

settings = get_settings()
logging.basicConfig(level=settings.log_level)

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Agenti — AI Content Agency",
    version="0.1.0",
    description="Автономное агентство ИИ-агентов, которое пишет контент для клиентов.",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(clients.router)
app.include_router(orders.router)
app.include_router(revenue.router)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
