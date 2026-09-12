"""
FastAPI entrypoint for Qdesq Sales+.

Importing agent.orchestrator (transitively, via the routers -> services)
already calls agent.db.init_db() at module load time, so the DB schema
exists and inventory is seeded before the first request - no separate
setup step needed, consistent with how main.py's demo already behaves.
"""
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import (
    leads, chat, workspaces, availability, bookings, tours, handoffs, analytics,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qdesq.api")

app = FastAPI(
    title="Qdesq Sales+ API",
    description="Backend API for the Qdesq AI-powered coworking sales agent.",
    version="1.0.0",
)

# CORS: origins are configurable via env so this doesn't need a code change
# between local dev (Vite's default port) and a deployed frontend origin.
allowed_origins = os.environ.get(
    "QDESQ_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads.router)
app.include_router(chat.router)
app.include_router(workspaces.router)
app.include_router(availability.router)
app.include_router(bookings.router)
app.include_router(tours.router)
app.include_router(handoffs.router)
app.include_router(analytics.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Last-resort safety net so a bug never returns a raw stack trace to the
    # frontend - individual routers already handle their own known error
    # cases (404s, booking conflicts) before this ever triggers.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
