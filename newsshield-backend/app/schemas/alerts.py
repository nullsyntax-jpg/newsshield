from pydantic import BaseModel
from typing import List


class Alert(BaseModel):
    rank: int
    industry: str
    region: str
    risk_score: float
    risk_type: str      # e.g. Geopolitical, Weather, Labour, Trade Policy
    headline: str
    source_count: int   # number of GDELT articles backing this signal
    detected_date: str  # ISO date when signal first crossed threshold
    lead_days: int      # predicted days before disruption hits


class AlertsResponse(BaseModel):
    alerts: List[Alert]