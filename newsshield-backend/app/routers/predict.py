"""
app/routers/predict.py
----------------------
GET /api/v1/risk
Powers the dashboard gauges, map, and forecast chart.
"""

from fastapi import APIRouter, Query, HTTPException
import numpy as np
import torch

from app.schemas.prediction import RiskPredictionResponse, SignalBreakdown
from app.core.risk_engine import load_feature_matrix, get_latest_week
from app.core.model_loader import load_xgboost, load_lstm

router = APIRouter()

FEATURE_COLS = [
    'article_count', 'num_mentions_sum', 'num_sources_sum', 'num_articles_sum',
    'avg_tone', 'std_tone', 'avg_goldstein', 'avg_severity', 'max_severity',
    'conflict_ratio', 'conflict_event_ratio', 'root_event_ratio',
    'sig_amplifier', 'sig_precursor', 'sig_propagation', 'sig_response', 'sig_trigger',
    'cat_economic', 'cat_geopolitical', 'cat_labor', 'cat_port', 'cat_trade_policy',
    'prop_local', 'prop_regional', 'prop_global',
    'article_count_r7', 'article_count_r14', 'article_count_wow',
    'num_mentions_sum_r7', 'num_mentions_sum_r14', 'num_mentions_sum_wow',
    'num_sources_sum_r7', 'num_sources_sum_r14', 'num_sources_sum_wow',
    'num_articles_sum_r7', 'num_articles_sum_r14', 'num_articles_sum_wow',
    'avg_tone_r7', 'avg_tone_r14', 'avg_tone_wow',
    'std_tone_r7', 'std_tone_r14', 'std_tone_wow',
    'avg_goldstein_r7', 'avg_goldstein_r14', 'avg_goldstein_wow',
    'avg_severity_r7', 'avg_severity_r14', 'avg_severity_wow',
    'max_severity_r7', 'max_severity_r14', 'max_severity_wow',
    'conflict_ratio_r7', 'conflict_ratio_r14', 'conflict_ratio_wow',
    'conflict_event_ratio_r7', 'conflict_event_ratio_r14', 'conflict_event_ratio_wow',
    'root_event_ratio_r7', 'root_event_ratio_r14', 'root_event_ratio_wow',
    'sig_amplifier_r7', 'sig_amplifier_r14', 'sig_amplifier_wow',
    'sig_precursor_r7', 'sig_precursor_r14', 'sig_precursor_wow',
    'sig_propagation_r7', 'sig_propagation_r14', 'sig_propagation_wow',
    'sig_response_r7', 'sig_response_r14', 'sig_response_wow',
    'sig_trigger_r7', 'sig_trigger_r14', 'sig_trigger_wow',
    'cat_economic_r7', 'cat_economic_r14', 'cat_economic_wow',
    'cat_geopolitical_r7', 'cat_geopolitical_r14', 'cat_geopolitical_wow',
    'cat_labor_r7', 'cat_labor_r14', 'cat_labor_wow',
    'cat_port_r7', 'cat_port_r14', 'cat_port_wow',
    'cat_trade_policy_r7', 'cat_trade_policy_r14', 'cat_trade_policy_wow',
    'prop_local_r7', 'prop_local_r14', 'prop_local_wow',
    'prop_regional_r7', 'prop_regional_r14', 'prop_regional_wow',
    'prop_global_r7', 'prop_global_r14', 'prop_global_wow',
]


def _warning_level(score: float) -> str:
    if score >= 0.75:
        return "critical"
    elif score >= 0.55:
        return "high"
    elif score >= 0.35:
        return "medium"
    return "low"


def _predict_xgboost(X: np.ndarray) -> tuple[float, float]:
    """Returns (risk_score, confidence)."""
    model = load_xgboost()
    proba = model.predict_proba(X)[0]  # [prob_0, prob_1]
    risk_score = float(proba[1])
    confidence = float(max(proba))
    return risk_score, confidence


def _predict_lstm(X: np.ndarray, horizon: int) -> tuple[float, float]:
    """Returns (risk_score, confidence)."""
    model = load_lstm(horizon)
    tensor = torch.FloatTensor(X).unsqueeze(0)  # (1, 1, features)
    with torch.no_grad():
        output = model(tensor)
    risk_score = float(output.squeeze())
    # Confidence: distance from 0.5 mapped to [0.5, 1.0]
    confidence = 0.5 + abs(risk_score - 0.5)
    return risk_score, confidence


@router.get("/risk", response_model=RiskPredictionResponse, summary="Risk score prediction")
def get_risk_prediction(
    region:   str = Query("Middle_East", description="Target region"),
    industry: str = Query("Geopolitical", description="Risk category"),
    horizon:  int = Query(21, description="Forecast horizon in days (7, 14, or 21)"),
):
    """
    Loads the trained XGBoost model (or LSTM for 7/14/21-day horizons),
    runs prediction on the latest features for the given region,
    and returns risk score + confidence + signal breakdown.

    Powers the dashboard gauges, map, and forecast chart.
    """
    if horizon not in (7, 14, 21):
        raise HTTPException(status_code=400, detail="horizon must be 7, 14, or 21")

    # ── Load latest features for this region ─────────────────────────────────
    try:
        df = load_feature_matrix()
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="feature_matrix.csv not found")

    latest_week = get_latest_week(df)
    subset = df[(df["week"] == latest_week) & (df["region"].str.lower() == region.lower())]

    if subset.empty:
        # Fall back to any available data for this region
        subset = df[df["region"].str.lower() == region.lower()].tail(1)

    if subset.empty:
        raise HTTPException(status_code=404, detail=f"No data found for region: {region}")

    row = subset.iloc[0]

    # ── Build feature vector ──────────────────────────────────────────────────
    X = np.array([[row.get(col, 0.0) for col in FEATURE_COLS]], dtype=np.float32)

    # ── Run prediction ────────────────────────────────────────────────────────
    try:
        if horizon == 21:
            risk_score, confidence = _predict_xgboost(X)
            model_used = "xgboost"
        else:
            risk_score, confidence = _predict_lstm(X, horizon)
            model_used = f"lstm_h{horizon}"
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Model prediction failed: {str(e)}")

    # ── Signal breakdown ──────────────────────────────────────────────────────
    total_cat = (
        row.get("cat_geopolitical", 0) +
        row.get("cat_trade_policy", 0) +
        row.get("cat_labor", 0) +
        row.get("cat_port", 0) +
        row.get("cat_economic", 0)
    ) or 1.0

    breakdown = SignalBreakdown(
        geopolitical=round(float(row.get("cat_geopolitical", 0)) / total_cat, 3),
        trade_policy=round(float(row.get("cat_trade_policy", 0)) / total_cat, 3),
        labour=round(float(row.get("cat_labor", 0)) / total_cat, 3),
        port=round(float(row.get("cat_port", 0)) / total_cat, 3),
        economic=round(float(row.get("cat_economic", 0)) / total_cat, 3),
    )

    return RiskPredictionResponse(
        region=row["region"],
        industry=industry,
        horizon_days=horizon,
        risk_score=round(risk_score, 3),
        confidence=round(confidence, 3),
        disruption_probability=round(risk_score, 3),
        model_used=model_used,
        signal_breakdown=breakdown,
        latest_week=latest_week,
        article_count=int(row.get("article_count", 0)),
        avg_tone=round(float(row.get("avg_tone", 0)), 3),
        warning_level=_warning_level(risk_score),
    )