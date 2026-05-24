from fastapi import APIRouter, HTTPException
from app.schemas.alerts import AlertsResponse, Alert
from app.core.risk_engine import load_feature_matrix, get_latest_week
from app.core.config import settings
import pandas as pd
from pathlib import Path

router = APIRouter()

# Risk type mapping from dominant category
CATEGORY_RISK_TYPE = {
    "cat_geopolitical": "Geopolitical",
    "cat_trade_policy": "Trade Policy",
    "cat_labor":        "Labour",
    "cat_port":         "Shipping / Port",
    "cat_economic":     "Economic",
}


def _dominant_risk_type(row: pd.Series) -> str:
    cat_cols = list(CATEGORY_RISK_TYPE.keys())
    available = [c for c in cat_cols if c in row.index]
    if not available:
        return "Unknown"
    dominant = max(available, key=lambda c: row[c])
    return CATEGORY_RISK_TYPE[dominant]


def _source_count(row: pd.Series) -> int:
    """Use num_sources_sum as a proxy for how many articles back this signal."""
    return int(row.get("num_sources_sum", row.get("article_count", 0)))


def _lead_days(risk_score: float) -> int:
    """
    Estimate lead days from risk score magnitude.
    High score = signal detected early = more lead days.
    Replace with model-specific lead time once ablation study is done.
    """
    if risk_score >= 0.85:
        return 21
    elif risk_score >= 0.70:
        return 18
    elif risk_score >= 0.55:
        return 14
    else:
        return 10


@router.get("/alerts", response_model=AlertsResponse, summary="Top-5 current risk alerts")
def get_alerts():
    """
    Returns the top 5 highest-risk supply chain alerts derived from the
    latest week in feature_matrix.csv. Sorted by risk_score descending.
    """
    try:
        df = load_feature_matrix()
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="feature_matrix.csv not found")

    latest_week = get_latest_week(df)
    latest = df[df["week"] == latest_week].sort_values("risk_score", ascending=False).head(5)

    alerts = []
    for rank, (_, row) in enumerate(latest.iterrows(), start=1):
        risk_type = _dominant_risk_type(row)
        alerts.append(Alert(
            rank=rank,
            industry=row["industry"],
            region=row["region"],
            risk_score=row["risk_score"],
            risk_type=risk_type,
            headline=f"Elevated {risk_type.lower()} risk signals detected in {row['region']} "
                     f"({int(row.get('article_count', 0))} articles, "
                     f"tone: {row.get('avg_tone', 0):.2f})",
            source_count=_source_count(row),
            detected_date=str(row["week_start"].date()),
            lead_days=_lead_days(row["risk_score"]),
        ))

    return AlertsResponse(alerts=alerts)