from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import pandas as pd
from app.schemas.alerts import AlertsResponse, Alert
from app.core.risk_engine import load_feature_matrix

router = APIRouter()

CATEGORY_RISK_TYPE = {
    "cat_geopolitical": "Geopolitical",
    "cat_trade_policy": "Trade Policy",
    "cat_labor":        "Labour",
    "cat_port":         "Shipping / Port",
    "cat_economic":     "Economic",
}

# sig_response removed — not present in feature_matrix.csv
SIGNAL_TYPE_MAP = {
    "sig_trigger":     "Trigger",
    "sig_precursor":   "Precursor",
    "sig_amplifier":   "Amplifier",
    "sig_propagation": "Propagation",
}


def _compute_risk_score(row: pd.Series) -> float:
    """
    Derive a normalised 0–1 risk score from columns that actually exist.

    Formula:
      avg_severity is always 4.0 or 5.0  → normalise with (value - 4) / 1
        so 4.0 → 0.0, 5.0 → 1.0
      conflict_ratio is already 0–1
      label (0/1) acts as a binary boost

    Weighted blend: 50% severity + 30% conflict + 20% label
    """
    severity_norm = float(row.get("avg_severity", 4.0)) - 4.0   # 0.0 or 1.0
    conflict      = float(row.get("conflict_ratio", 0.0))        # 0–1
    label_boost   = float(row.get("label", 0))                   # 0 or 1
    score = (0.50 * severity_norm) + (0.30 * conflict) + (0.20 * label_boost)
    return round(min(max(score, 0.0), 1.0), 4)


def _dominant_risk_type(row: pd.Series) -> str:
    available = [c for c in CATEGORY_RISK_TYPE if c in row.index]
    if not available:
        return "Unknown"
    dominant = max(available, key=lambda c: float(row[c]))
    return CATEGORY_RISK_TYPE[dominant]


def _dominant_signal_type(row: pd.Series) -> str:
    available = [c for c in SIGNAL_TYPE_MAP if c in row.index]
    if not available:
        return "Unknown"
    dominant = max(available, key=lambda c: float(row[c]))
    return SIGNAL_TYPE_MAP[dominant]


def _lead_days(risk_score: float) -> int:
    if risk_score >= 0.85:
        return 21
    elif risk_score >= 0.70:
        return 18
    elif risk_score >= 0.55:
        return 14
    return 10


def _source_count(row: pd.Series) -> int:
    return int(row.get("num_sources_sum", row.get("article_count", 0)))


@router.get("/alerts", response_model=AlertsResponse, summary="Top-5 current risk alerts")
def get_alerts(
    days: int = Query(
        default=7,
        ge=1,
        le=30,
        description=(
            "Rolling window in days. Since data is aggregated weekly, this selects "
            "the last N distinct week-start dates (1–30)."
        ),
    ),
    region: Optional[str] = Query(None, description="Filter by region, e.g. Middle_East"),
    risk_type: Optional[str] = Query(
        None, description="Filter by dominant risk type, e.g. Geopolitical"
    ),
    min_severity: float = Query(
        default=0.0, ge=0.0, le=1.0, description="Minimum computed risk score (0–1)"
    ),
):
    """
    Returns top-5 highest-risk supply chain alerts from the latest N week-windows.
    Sorted by computed risk_score descending. Powers alert cards and the ticker on
    the dashboard.

    risk_score is derived from avg_severity, conflict_ratio, and the disruption
    label — there is no pre-computed column in the CSV.
    """
    try:
        df = load_feature_matrix()
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="feature_matrix.csv not found.")

    # ── Compute risk_score for every row (not in CSV — derived here) ─────────
    df = df.copy()
    df["risk_score"] = df.apply(_compute_risk_score, axis=1)

    # ── Date window: last N distinct week-start values ───────────────────────
    df_sorted    = df.sort_values("week_start", ascending=False)
    cutoff_weeks = df_sorted["week_start"].unique()[:days]
    subset       = df_sorted[df_sorted["week_start"].isin(cutoff_weeks)]

    if subset.empty:                        # dataset older than window → latest 50
        subset = df_sorted.head(50)

    # ── Optional filters ─────────────────────────────────────────────────────
    if region:
        subset = subset[subset["region"].str.lower() == region.strip().lower()]

    if risk_type:
        # Compute dominant risk type per row and filter — no "industry" column exists
        subset = subset[
            subset.apply(_dominant_risk_type, axis=1).str.lower()
            == risk_type.strip().lower()
        ]

    if min_severity > 0:
        subset = subset[subset["risk_score"] >= min_severity]

    if subset.empty:
        raise HTTPException(status_code=404, detail="No alerts match the given filters.")

    # ── Sort by risk_score, take top 5 ───────────────────────────────────────
    top5 = subset.sort_values("risk_score", ascending=False).head(5)

    alerts = []
    for rank, (_, row) in enumerate(top5.iterrows(), start=1):
        risk_type_val   = _dominant_risk_type(row)
        signal_type_val = _dominant_signal_type(row)

        alerts.append(Alert(
            rank=rank,
            industry=risk_type_val,          # no industry column; risk_type is the proxy
            region=row["region"],
            risk_score=round(float(row["risk_score"]), 3),
            risk_type=risk_type_val,
            headline=(
                f"Elevated {risk_type_val.lower()} risk detected in {row['region']} "
                f"({int(row.get('article_count', 0))} articles, "
                f"tone: {float(row.get('avg_tone', 0)):.2f}, "
                f"signal: {signal_type_val})"
            ),
            source_count=_source_count(row),
            detected_date=str(
                row["week_start"].date()
                if hasattr(row["week_start"], "date")
                else row["week_start"]
            ),
            lead_days=_lead_days(float(row["risk_score"])),
        ))

    return AlertsResponse(alerts=alerts)