from pydantic import BaseModel
from typing import Dict, Optional


class SignalBreakdown(BaseModel):
    geopolitical: float
    trade_policy: float
    labour: float
    port: float
    economic: float


class RiskPredictionResponse(BaseModel):
    region: str
    industry: str
    horizon_days: int
    risk_score: float          # 0.0 – 1.0
    confidence: float          # 0.0 – 1.0
    disruption_probability: float
    model_used: str            # "xgboost" or "lstm"
    signal_breakdown: SignalBreakdown
    latest_week: str
    article_count: int
    avg_tone: float
    warning_level: str         # "low" / "medium" / "high" / "critical"