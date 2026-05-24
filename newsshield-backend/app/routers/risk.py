from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.schemas.risk import RiskHeatmapResponse, RiskCell
from app.core.risk_engine import load_feature_matrix, get_latest_week

router = APIRouter()


@router.get("/risk/heatmap", response_model=RiskHeatmapResponse, summary="Risk heatmap data")
def get_risk_heatmap(
    week: Optional[str] = Query(None, description="ISO week, e.g. 2024-W20. Defaults to latest."),
    industry: Optional[str] = Query(None, description="Filter by derived risk category"),
    region: Optional[str] = Query(None, description="Filter by region"),
):
    """
    Returns real risk scores per region x derived-industry cell, computed
    from feature_matrix.csv using a weighted composite of LLM signal columns.
    """
    try:
        df = load_feature_matrix()
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="feature_matrix.csv not found. Check GDELT_OUTPUT_DIR in .env")

    target_week = week or get_latest_week(df)

    subset = df[df["week"] == target_week]
    if subset.empty:
        target_week = get_latest_week(df)
        subset = df[df["week"] == target_week]

    if industry:
        subset = subset[subset["industry"].str.lower() == industry.lower()]
    if region:
        subset = subset[subset["region"].str.lower() == region.lower()]

    cells = [
        RiskCell(
            industry=row["industry"],
            region=row["region"],
            risk_score=row["risk_score"],
            week=row["week"],
        )
        for _, row in subset.iterrows()
    ]

    cells.sort(key=lambda c: c.risk_score, reverse=True)

    return RiskHeatmapResponse(week=target_week, cells=cells)