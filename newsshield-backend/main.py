from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.routers import health, risk, forecast, alerts, predict
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 NewsShield API starting — env: {settings.ENV}")
    yield
    print("🛑 NewsShield API shutting down")


app = FastAPI(
    title="NewsShield API",
    description="Supply chain disruption prediction API powered by GDELT + LLM signals",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router,   tags=["Health"])
app.include_router(risk.router,     prefix="/api/v1", tags=["Risk Scores"])
app.include_router(forecast.router, prefix="/api/v1", tags=["Forecast"])
app.include_router(alerts.router,   prefix="/api/v1", tags=["Alerts"])
app.include_router(predict.router,  prefix="/api/v1", tags=["Prediction"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)