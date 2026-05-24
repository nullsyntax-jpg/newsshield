from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()

@router.get("/", summary="Root")
def root():
    return {"message": "NewsShield API is live"}

@router.get("/health", summary="Health check")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }