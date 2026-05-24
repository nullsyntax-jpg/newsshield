from pydantic import BaseModel
from typing import List


class RiskCell(BaseModel):
    industry: str
    region: str
    risk_score: float   # 0.0 – 1.0
    week: str           # ISO week string, e.g. "2024-W20"


class RiskHeatmapResponse(BaseModel):
    week: str
    cells: List[RiskCell]