import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from db.database import create_tables
from api.routes import router
from scheduler.cron import start_scheduler, stop_scheduler
from ws.binance_monitor import BinanceMonitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

monitor = BinanceMonitor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    start_scheduler()
    await monitor.start()
    yield
    stop_scheduler()
    await monitor.stop()


app = FastAPI(
    title="AI Trading Assistant API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
