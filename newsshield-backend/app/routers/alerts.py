from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import json
import os
from datetime import datetime, timedelta
from app.schemas.alerts import AlertsResponse, Alert

router = APIRouter()

# Path to the extracted JSON dataset
JSON_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "gdelt_output", "final_extraction_100.json"
)

SEVERITY_TO_WARNING = {
    5: "critical",
    4: "high",
    3: "medium",
    2: "low",
    1: "low",
}


def _load_extractions() -> list[dict]:
    path = os.path.abspath(JSON_PATH)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Extraction JSON not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Keep only successful extractions
    return [r for r in data if r.get("status") == "success"]


def _severity_score(record: dict) -> float:
    """Normalise severity_score (1–5) to 0–1."""
    raw = float(record.get("severity_score", 3))
    return round((raw - 1) / 4, 4)


def _lead_days(risk_score: float) -> int:
    if risk_score >= 0.85:
        return 21
    elif risk_score >= 0.70:
        return 18
    elif risk_score >= 0.55:
        return 14
    return 10


@router.get("/alerts", response_model=AlertsResponse, summary="Top-5 current risk alerts")
def get_alerts(
    days: int = Query(
        default=7,
        ge=1,
        le=30,
        description="Rolling window in days to filter alerts.",
    ),
    region: Optional[str] = Query(None, description="Filter by region, e.g. Taiwan"),
    risk_type: Optional[str] = Query(
        None, description="Filter by disruption category, e.g. geopolitical, labor, semiconductor"
    ),
    min_severity: float = Query(
        default=0.0, ge=0.0, le=1.0, description="Minimum normalised severity score (0–1)"
    ),
):
    """
    Returns top-5 highest-severity supply chain alerts from the extracted JSON dataset.
    Sorted by severity_score descending. Powers alert cards and the ticker on the dashboard.
    """
    try:
        records = _load_extractions()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if not records:
        raise HTTPException(status_code=503, detail="Extraction dataset is empty.")

    # ── Simulate article_date as recent dates (JSON has no date field) ────────
    # Spread records across the last `days` window evenly for demo purposes
    base_date = datetime.utcnow()
    total = len(records)
    for i, rec in enumerate(records):
        offset = int((i / total) * days)
        rec["_article_date"] = (base_date - timedelta(days=offset)).strftime("%Y-%m-%d")

    # ── Optional filters ──────────────────────────────────────────────────────
    filtered = records

    if region:
        filtered = [
            r for r in filtered
            if r.get("region", "").lower() == region.strip().lower()
        ]

    if risk_type:
        rt = risk_type.strip().lower()
        filtered = [
            r for r in filtered
            if rt in r.get("disruption_category", "").lower()
            or rt in r.get("affected_industry", "").lower()
            or rt in r.get("signal_type", "").lower()
        ]

    if min_severity > 0:
        filtered = [
            r for r in filtered
            if _severity_score(r) >= min_severity
        ]

    if not filtered:
        raise HTTPException(status_code=404, detail="No alerts match the given filters.")

    # ── Sort by severity, take top 5 ─────────────────────────────────────────
    top5 = sorted(filtered, key=lambda r: r.get("severity_score", 0), reverse=True)[:5]

    alerts = []
    for rank, rec in enumerate(top5, start=1):
        risk_score = _severity_score(rec)
        alerts.append(Alert(
            rank=rank,
            industry=rec.get("affected_industry", "Unknown"),
            region=rec.get("region", "Unknown"),
            risk_score=risk_score,
            risk_type=rec.get("disruption_category", "Unknown"),
            headline=rec.get("headline", "No headline available"),
            source_count=1,
            detected_date=rec["_article_date"],
            lead_days=_lead_days(risk_score),
        ))

    return AlertsResponse(alerts=alerts)