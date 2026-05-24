from pydantic import BaseModel
from typing import List


class ForecastPoint(BaseModel):
    date: str           # ISO date string
    predicted_risk: float
    lower_bound: float
    upper_bound: float


class ForecastResponse(BaseModel):
    industry: str
    region: str
    horizon_days: int
    forecast: List[ForecastPoint]