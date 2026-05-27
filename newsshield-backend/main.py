"""
NewsShield FastAPI application entry point.

Run locally:
    uvicorn main:app --reload --port 8000

Docs:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc  (ReDoc)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# --- Import routers -----------------------------------------------------------
from app.routers import health        # GET /api/v1/health
from app.routers import risk          # GET /api/v1/risk/...
from app.routers import forecast      # GET /api/v1/forecast/...
from app.routers import alerts        # GET /api/v1/alerts/feed   ← new
from app.routers import predict       # POST /api/v1/predict/...
from app.routers import history       # GET /api/v1/history
from app.routers import search        # GET /api/v1/search
from app.routers import ask           # POST /api/v1/ask

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NewsShield — Supply Chain Disruption API",
    version="1.0.0",
    description=(
        "Real-time supply chain risk signals derived from GDELT news data. "
        "Provides disruption alerts, risk scores, and ML-based forecasts."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS (tighten origins in production) ------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "CORS_ORIGINS", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register routers ---------------------------------------------------------
API_PREFIX = "/api/v1"

app.include_router(health.router,   prefix=API_PREFIX)
app.include_router(risk.router,     prefix=API_PREFIX)
app.include_router(forecast.router, prefix=API_PREFIX)
app.include_router(alerts.router,   prefix=API_PREFIX)   # ← /api/v1/alerts/feed
app.include_router(predict.router,  prefix=API_PREFIX)
app.include_router(history.router, prefix=API_PREFIX)
app.include_router(search.router, prefix=API_PREFIX)
app.include_router(ask.router, prefix=API_PREFIX)

# ---------------------------------------------------------------------------
# Root redirect (optional quality-of-life)
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def root():
    return {"message": "NewsShield API is running. Visit /docs for the API reference."}