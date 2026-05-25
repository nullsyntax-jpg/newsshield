from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import pandas as pd
import os

router = APIRouter()

# ── Data paths ────────────────────────────────────────────────────────────────
BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "gdelt_output")
FEATURE_MATRIX_PATH = os.path.join(BASE, "feature_matrix.csv")
GSCPI_PATH          = os.path.join(BASE, "gscpi_clean.csv")

CATEGORY_MAP = {
    "semiconductor": "cat_economic",
    "geopolitical":  "cat_geopolitical",
    "labor":         "cat_labor",
    "shipping":      "cat_port",
    "trade":         "cat_trade_policy",
    "economic":      "cat_economic",
}


def _load_feature_matrix() -> pd.DataFrame:
    path = os.path.abspath(FEATURE_MATRIX_PATH)
    if not os.path.exists(path):
        raise FileNotFoundError(f"feature_matrix.csv not found at {path}")
    df = pd.read_csv(path, parse_dates=["week_start"])
    return df


def _load_gscpi() -> pd.DataFrame:
    path = os.path.abspath(GSCPI_PATH)
    if not os.path.exists(path):
        raise FileNotFoundError(f"gscpi_clean.csv not found at {path}")
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.rename(columns={"date": "month"})
    return df


def _compute_risk_score(row: pd.Series) -> float:
    """Same formula as alerts.py — normalised 0–1."""
    severity_norm = float(row.get("avg_severity", 4.0)) - 4.0
    conflict      = float(row.get("conflict_ratio", 0.0))
    label_boost   = float(row.get("label", 0))
    score = (0.50 * severity_norm) + (0.30 * conflict) + (0.20 * label_boost)
    return round(min(max(score, 0.0), 1.0), 4)


@router.get("/history", summary="Historical weekly risk score + GSCPI")
def get_history(
    region: Optional[str] = Query(
        None, description="Filter by region e.g. Middle_East, Africa, Europe"
    ),
    industry: Optional[str] = Query(
        None,
        description=(
            "Filter by industry signal: semiconductor, geopolitical, "
            "labor, shipping, trade, economic"
        ),
    ),
    days: int = Query(
        default=90,
        description="Look-back window: 30, 90, or 365 days",
    ),
):
    """
    Returns parallel arrays of weekly risk scores and monthly GSCPI values
    for the requested region/industry over the chosen look-back window.

    Powers:
    - Risk vs GSCPI comparison chart
    - Sparklines
    - GitHub-style heatmap on dashboard
    - Case study timeline charts (Page 3)
    """
    # ── Load data ─────────────────────────────────────────────────────────────
    try:
        fm = _load_feature_matrix()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    try:
        gscpi = _load_gscpi()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # ── Date filter ───────────────────────────────────────────────────────────
    cutoff = fm["week_start"].max() - pd.Timedelta(days=days)
    fm = fm[fm["week_start"] >= cutoff].copy()

    # ── Region filter ─────────────────────────────────────────────────────────
    if region:
        fm = fm[fm["region"].str.lower() == region.strip().lower()]
        if fm.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for region '{region}'."
            )

    # ── Industry filter (boosts weight of that category column) ───────────────
    industry_col = None
    if industry:
        key = industry.strip().lower()
        industry_col = CATEGORY_MAP.get(key)
        if industry_col and industry_col in fm.columns:
            # Filter to rows where that category signal is active (> 0)
            fm = fm[fm[industry_col] > 0]
            if fm.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found for industry '{industry}' in the selected window."
                )

    # ── Compute risk score ────────────────────────────────────────────────────
    fm["risk_score"] = fm.apply(_compute_risk_score, axis=1)

    # ── Aggregate weekly (group by week_start if multiple regions) ────────────
    weekly = (
        fm.groupby("week_start")
        .agg(
            risk_score=("risk_score", "mean"),
            avg_severity=("avg_severity", "mean"),
            conflict_ratio=("conflict_ratio", "mean"),
            article_count=("article_count", "sum"),
        )
        .reset_index()
        .sort_values("week_start")
    )

    # ── Merge GSCPI by month ──────────────────────────────────────────────────
    weekly["month"] = weekly["week_start"].dt.to_period("M").dt.to_timestamp()
    merged = weekly.merge(gscpi, on="month", how="left")

    # ── Build response ────────────────────────────────────────────────────────
    weeks       = merged["week_start"].dt.strftime("%Y-%m-%d").tolist()
    risk_scores = merged["risk_score"].round(4).tolist()
    gscpi_vals  = merged["gscpi"].fillna(0).round(4).tolist()
    severities  = merged["avg_severity"].round(4).tolist()
    articles    = merged["article_count"].fillna(0).astype(int).tolist()

    return {
        "meta": {
            "region":   region or "all",
            "industry": industry or "all",
            "days":     days,
            "weeks_returned": len(weeks),
        },
        "weeks":       weeks,
        "risk_scores": risk_scores,
        "gscpi":       gscpi_vals,
        "avg_severity": severities,
        "article_counts": articles,
    }