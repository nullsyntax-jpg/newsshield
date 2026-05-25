"""
Pydantic schemas for the alerts feed endpoint.
"""

from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Individual alert item
# ---------------------------------------------------------------------------

class Alert(BaseModel):
    rank: int = Field(..., description="Alert rank (1 = highest severity)")
    industry: str = Field(..., description="Affected industry")
    region: str = Field(..., description="Geographic region of the signal")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Normalised risk score (0–1)")
    risk_type: str = Field(..., description="Disruption category e.g. geopolitical, labor")
    headline: str = Field(..., description="Alert headline")
    source_count: int = Field(..., ge=0, description="Number of source articles")
    detected_date: str = Field(..., description="Date alert was detected (YYYY-MM-DD)")
    lead_days: int = Field(..., description="Estimated lead time in days before impact")

    model_config = {"json_schema_extra": {
        "example": {
            "rank": 1,
            "industry": "semiconductor",
            "region": "Taiwan",
            "risk_score": 1.0,
            "risk_type": "geopolitical",
            "headline": "Taiwan semiconductor orders decline for third consecutive month amid geopolitical tensions",
            "source_count": 1,
            "detected_date": "2025-05-25",
            "lead_days": 21,
        }
    }}


# ---------------------------------------------------------------------------
# Response envelope
# ---------------------------------------------------------------------------

class AlertsResponse(BaseModel):
    alerts: list[Alert]

    model_config = {"json_schema_extra": {
        "example": {
            "alerts": []
        }
    }}


# ---------------------------------------------------------------------------
# Keep old names as aliases so nothing else breaks
# ---------------------------------------------------------------------------

AlertItem = Alert
AlertsFeedResponse = AlertsResponse