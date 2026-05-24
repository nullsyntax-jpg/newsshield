from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.schemas.forecast import ForecastResponse, ForecastPoint
from app.core.risk_engine import load_feature_matrix
from app.core.config import settings
import pandas as pd
import numpy as np
from pathlib import Path

router = APIRouter()


def _forecast_from_history(df: pd.DataFrame, region: str, industry: str) -> list:
    """
    Simple 21-day rolling forecast using the last 14 weeks of risk scores
    for the given region. Uses exponential smoothing as a lightweight baseline
    until the trained LSTM/XGBoost model files are wired in.
    """
    subset = df[df["region"].str.lower() == region.lower()].sort_values("week_start")

    if subset.empty:
        # Region not found — return flat 0.3 with uncertainty
        from datetime import date, timedelta
        today = date.today()
        return [
            ForecastPoint(
                date=str(today + timedelta(days=i)),
                predicted_risk=0.3,
                lower_bound=0.23,
                upper_bound=0.37,
            )
            for i in range(21)
        ]

    scores = subset["risk_score"].values
    alpha = 0.3  # smoothing factor
    smoothed = scores[-1]
    for s in scores[-14:]:
        smoothed = alpha * s + (1 - alpha) * smoothed

    from datetime import date, timedelta
    today = date.today()
    points = []
    current = smoothed
    std = float(np.std(scores[-8:])) if len(scores) >= 8 else 0.05

    for i in range(21):
        drift = 0.003 * i  # slight forward drift
        pred = float(np.clip(current + drift, 0, 1))
        points.append(ForecastPoint(
            date=str(today + timedelta(days=i)),
            predicted_risk=round(pred, 3),
            lower_bound=round(max(0.0, pred - std), 3),
            upper_bound=round(min(1.0, pred + std), 3),
        ))

    return points


def _load_rag_predictions(region: str) -> list | None:
    """
    Try to load Member B's RAG predictions from member_b/rag_predictions_7d.csv.
    Returns None if file not found or region not present.
    """
    path = Path(settings.GDELT_OUTPUT_DIR) / "member_b" / "rag_predictions_7d.csv"
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
        subset = df[df["region"].str.lower() == region.lower()] if "region" in df.columns else df
        if subset.empty:
            return None
        return subset.to_dict("records")
    except Exception:
        return None


@router.get("/forecast", response_model=ForecastResponse, summary="21-day disruption forecast")
def get_forecast(
    industry: str = Query("Geopolitical", description="Risk category / industry"),
    region: str   = Query("Middle East",  description="Target region"),
):
    """
    Returns a 21-day forward-looking disruption probability time series.
    Uses exponential smoothing over historical risk scores from feature_matrix.csv.
    Wire in the trained XGBoost/LSTM model here in Week 8.
    """
    try:
        df = load_feature_matrix()
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="feature_matrix.csv not found")

    points = _forecast_from_history(df, region, industry)
    return ForecastResponse(industry=industry, region=region, horizon_days=21, forecast=points)