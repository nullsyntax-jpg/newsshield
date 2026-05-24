"""
app/core/risk_engine.py
-----------------------
Computes a normalised risk score (0-1) for each region × week row
from the raw feature_matrix.csv columns.

No industry column exists in the data, so we derive a dominant
risk category (geopolitical / trade / labour / port / economic)
and use that as a proxy industry label for the frontend.
"""

import pandas as pd
import numpy as np
from functools import lru_cache
from pathlib import Path
from app.core.config import settings


# ── Weights for composite risk score ────────────────────────────────────────
# Tuned to match the paper's signal importance findings.
# Increase weight of a feature to make it dominate the score.
WEIGHTS = {
    "avg_severity":           0.25,
    "conflict_ratio":         0.20,
    "avg_goldstein":         -0.15,   # negative = bad (destabilising events)
    "avg_tone":              -0.10,   # negative tone = higher risk
    "sig_trigger":            0.10,
    "sig_precursor":          0.08,
    "sig_amplifier":          0.07,
    "conflict_event_ratio":   0.05,
}

# Map dominant category column → human-readable industry label
CATEGORY_TO_INDUSTRY = {
    "cat_geopolitical": "Geopolitical",
    "cat_trade_policy": "Trade Policy",
    "cat_labor":        "Labour / Industrial",
    "cat_port":         "Shipping / Ports",
    "cat_economic":     "Economic",
}


def _compute_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a `risk_score` column (0–1) and an `industry` column to df.
    Works on a copy; does not mutate the input.
    """
    df = df.copy()

    # 1. Normalise each weighted feature to [0, 1]
    score = pd.Series(np.zeros(len(df)), index=df.index)
    for col, weight in WEIGHTS.items():
        if col not in df.columns:
            continue
        col_min, col_max = df[col].min(), df[col].max()
        if col_max == col_min:
            normalised = pd.Series(np.zeros(len(df)), index=df.index)
        else:
            normalised = (df[col] - col_min) / (col_max - col_min)
        score += weight * normalised

    # 2. Clip and re-normalise to [0, 1]
    score = score.clip(lower=0)
    s_max = score.max()
    if s_max > 0:
        score = score / s_max
    df["risk_score"] = score.round(3)

    # 3. Derive dominant industry from category columns
    cat_cols = [c for c in CATEGORY_TO_INDUSTRY if c in df.columns]
    if cat_cols:
        df["industry"] = df[cat_cols].idxmax(axis=1).map(CATEGORY_TO_INDUSTRY)
    else:
        df["industry"] = "General"

    return df


@lru_cache(maxsize=1)
def load_feature_matrix() -> pd.DataFrame:
    """
    Loads and enriches feature_matrix.csv once; cached for the process lifetime.
    Call invalidate_cache() after a data refresh.
    """
    path = Path(settings.GDELT_OUTPUT_DIR) / "feature_matrix.csv"
    df = pd.read_csv(path, parse_dates=["week_start"])
    df = _compute_risk_scores(df)
    df["week"] = df["week_start"].dt.strftime("%Y-W%W")
    return df


def invalidate_cache():
    load_feature_matrix.cache_clear()


def get_latest_week(df: pd.DataFrame) -> str:
    return df["week"].iloc[-1]