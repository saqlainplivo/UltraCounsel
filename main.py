"""
main.py
UltraCounsel — Apex Coaching Institute Voice Counsellor Agent
Built with Ultravox + Plivo + FastAPI

Sage is a voice AI counsellor who helps students find the right coaching
course, understand the syllabus, check batch availability, explore
scholarships, and book free demo classes.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from lib.db import create_pool, close_pool
from api.webhook.answer import router as answer_router
from api.webhook.events import router as events_router
from api.tools import router as tools_router
from api.calls import router as calls_router

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB pool. Shutdown: close pool."""
    logger.info("🚀 UltraCounsel starting up...")

    # Connect to database
    await create_pool()
    logger.info("✅ Database pool ready")

    yield

    # Cleanup
    await close_pool()
    logger.info("👋 UltraCounsel shut down cleanly")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="UltraCounsel — Apex Coaching Institute",
    description="Voice AI counsellor for Apex Coaching Institute. Powered by Ultravox + Plivo.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(answer_router)
app.include_router(events_router)
app.include_router(tools_router)
app.include_router(calls_router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    """Health check endpoint for Vercel and monitoring."""
    return {
        "status": "healthy",
        "service": "UltraCounsel",
        "agent": "Sage",
        "institute": os.getenv("INSTITUTE_NAME", "Apex Coaching Institute"),
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    return {
        "message": "UltraCounsel — Apex Coaching Institute Voice Counsellor",
        "docs": "/docs",
        "health": "/api/health",
    }
