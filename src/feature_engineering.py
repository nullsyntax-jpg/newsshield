"""
T4 — Feature Engineering Pipeline
===================================
NewsShield: Supply Chain Disruption Prediction

Input:
    gdelt_output/llm_extractions_full.json   ← Member B's full LLM extraction output
    gdelt_output/gscpi_clean.csv             ← NY Fed GSCPI monthly index

Output:
    gdelt_output/feature_matrix.csv          ← ML-ready feature matrix (X + y)
    gdelt_output/feature_matrix_smote.csv    ← SMOTE-balanced training set
    gdelt_output/label_distribution.csv      ← class balance report
    gdelt_output/feature_names.txt           ← list of all feature column names

JSON Schema expected from Member B:
    {
        "disruption_category": "geopolitical | trade_policy | labor | weather |
                                 factory | port | pandemic | regulatory | economic |
                                 infrastructure_failure | natural_disaster |
                                 component_shortage | cyber | none",
        "affected_industry":   "semiconductor | automotive | logistics | food |
                                 energy | pharmaceutical | apparel | agriculture |
                                 electronics | chemical | manufacturing | mining |
                                 aerospace | general | none",
        "region":              "country or region name string",
        "severity_score":      1-5 integer,
        "propagation_risk":    "local | regional | global | none",
        "signal_type":         "Precursor | Trigger | Amplifier | Propagation |
                                 Response | Recovery | none",
        "headline":            "original headline text",
        "published_date":      "YYYY-MM-DD",   ← REQUIRED for time-series
        "status":              "success | error"
    }

Run:
    pip install pandas numpy scikit-learn imbalanced-learn --break-system-packages
    python src/feature_engineering.py
    python src/feature_engineering.py --json path/to/extractions.json --gscpi path/to/gscpi.csv
"""

import json
import argparse
import os
import sys
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Try importing SMOTE ──────────────────────────────────────────────────────
try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
except ImportError:
    SMOTE_AVAILABLE = False
    print("  ⚠  imbalanced-learn not found.")
    print("     pip install imbalanced-learn --break-system-packages\n")

# ── Config ───────────────────────────────────────────────────────────────────
OUTPUT_DIR         = "gdelt_output"
DEFAULT_JSON       = "gdelt_output/llm_extractions_full.json"
DEFAULT_GSCPI      = "gdelt_output/gscpi_clean.csv"
GSCPI_THRESHOLD    = 1.0        # std deviations above mean = spike
LABEL_WINDOW       = 14         # days: label=1 if spike within next N days
TRAIN_END          = "2022-12-31"
TEST_START         = "2023-01-01"
SMOTE_RANDOM_STATE = 42

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Enum definitions (must match Member B's schema exactly) ──────────────────
SIGNAL_TYPES = [
    "Precursor", "Trigger", "Amplifier",
    "Propagation", "Response", "Recovery", "none"
]

DISRUPTION_CATEGORIES = [
    "geopolitical", "trade_policy", "labor", "weather", "factory",
    "port", "pandemic", "regulatory", "economic", "infrastructure_failure",
    "natural_disaster", "component_shortage", "cyber", "none"
]

PROPAGATION_LEVELS = ["local", "regional", "global", "none"]


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — LOAD & CLEAN LLM EXTRACTIONS
# ══════════════════════════════════════════════════════════════════════════════

def load_extractions(path: str) -> pd.DataFrame:
    """Load Member B's JSON extractions and return a clean DataFrame."""
    print(f"\n  [1/6] Loading LLM extractions from: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    # Drop failed extractions
    if "status" in df.columns:
        before = len(df)
        df = df[df["status"] == "success"].copy()
        print(f"        Dropped {before - len(df)} failed extractions.")

    # Require published_date
    if "published_date" not in df.columns:
        raise ValueError(
            "\n  ❌ JSON records must include 'published_date' (YYYY-MM-DD).\n"
            "     Ask Member B to include the article publication date in each record."
        )

    # Parse dates and drop unparseable
    df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")
    bad_dates = df["published_date"].isna().sum()
    if bad_dates:
        print(f"        ⚠  Dropped {bad_dates} rows with unparseable dates.")
    df = df.dropna(subset=["published_date"])

    # Normalise text fields to lowercase/stripped
    df["disruption_category"] = df["disruption_category"].str.lower().str.strip()
    df["affected_industry"]   = df["affected_industry"].str.lower().str.strip()
    df["signal_type"]         = df["signal_type"].str.strip()       # preserve case for Precursor etc
    df["propagation_risk"]    = df["propagation_risk"].str.lower().str.strip()
    df["region"]              = df["region"].str.strip()

    # Numeric severity
    df["severity_score"] = pd.to_numeric(df["severity_score"], errors="coerce")

    # Add week_start (Monday of each article's week)
    df["week_start"] = (
        df["published_date"] - pd.to_timedelta(df["published_date"].dt.weekday, unit="d")
    ).dt.normalize()

    print(f"        Loaded {len(df):,} valid extractions  "
          f"({df['published_date'].min().date()} → {df['published_date'].max().date()})")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — GROUP BY industry × region × week  →  base features
# ══════════════════════════════════════════════════════════════════════════════

def build_groups(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each (affected_industry, region, week_start) group compute:
      - article_count
      - avg_severity
      - proportion of each signal_type     (sig_*)
      - proportion of each disruption_cat  (cat_*)
      - proportion of each propagation lvl (prop_*)
    """
    print("\n  [2/6] Building industry × region × week groups...")

    GROUP_KEYS = ["affected_industry", "region", "week_start"]
    rows = []

    for (industry, region, week), grp in df.groupby(GROUP_KEYS):
        n = len(grp)
        row = {
            "industry":      industry,
            "region":        region,
            "week_start":    week,
            "article_count": n,
            "avg_severity":  round(grp["severity_score"].mean(), 4),
        }

        # Signal type proportions
        sig_counts = grp["signal_type"].value_counts()
        for s in SIGNAL_TYPES:
            row[f"sig_{s.lower()}"] = round(sig_counts.get(s, 0) / n, 4)

        # Disruption category proportions
        cat_counts = grp["disruption_category"].value_counts()
        for c in DISRUPTION_CATEGORIES:
            row[f"cat_{c}"] = round(cat_counts.get(c, 0) / n, 4)

        # Propagation risk proportions
        prop_counts = grp["propagation_risk"].value_counts()
        for p in PROPAGATION_LEVELS:
            row[f"prop_{p}"] = round(prop_counts.get(p, 0) / n, 4)

        rows.append(row)

    groups = (
        pd.DataFrame(rows)
        .sort_values(["industry", "region", "week_start"])
        .reset_index(drop=True)
    )

    print(f"        Created {len(groups):,} group rows  |  "
          f"{groups['industry'].nunique()} industries, "
          f"{groups['region'].nunique()} regions")
    return groups


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — ROLLING FEATURES  (7-day, 14-day, week-over-week change)
# ══════════════════════════════════════════════════════════════════════════════

def add_rolling_features(groups: pd.DataFrame) -> pd.DataFrame:
    """
    Within each industry × region series (sorted by week), add:
      _r7  : 1-week (7-day)  rolling mean
      _r14 : 2-week (14-day) rolling mean
      _wow : week-over-week pct change
    """
    print("\n  [3/6] Computing rolling features (7d, 14d, WoW)...")

    base_cols = [c for c in groups.columns
                 if c not in ("industry", "region", "week_start")]

    parts = []
    for (industry, region), grp in groups.groupby(["industry", "region"]):
        grp = grp.sort_values("week_start").copy()

        for col in base_cols:
            grp[f"{col}_r7"]  = grp[col].rolling(window=1, min_periods=1).mean()
            grp[f"{col}_r14"] = grp[col].rolling(window=2, min_periods=1).mean()
            grp[f"{col}_wow"] = grp[col].pct_change().replace([np.inf, -np.inf], np.nan)

        parts.append(grp)

    result = (
        pd.concat(parts, ignore_index=True)
        .sort_values(["industry", "region", "week_start"])
        .reset_index(drop=True)
    )

    # Fill first-row NaN WoW values with 0
    wow_cols = [c for c in result.columns if c.endswith("_wow")]
    result[wow_cols] = result[wow_cols].fillna(0)

    n_rolling = len(wow_cols)          # one wow col per base col
    print(f"        Added {n_rolling * 3} rolling columns  "
          f"({len(base_cols)} base cols × 3 transforms)")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — BUILD Y LABELS FROM GSCPI
# ══════════════════════════════════════════════════════════════════════════════

def load_gscpi(path: str) -> pd.DataFrame:
    """
    Load NY Fed GSCPI CSV.
    Expected columns: a date column and a numeric GSCPI value column.
    """
    print(f"\n  [4/6] Loading GSCPI from: {path}")
    gscpi = pd.read_csv(path)

    date_col = next(
        (c for c in gscpi.columns if any(k in c.lower() for k in ["date","month","year"])),
        None
    )
    val_col = next(
        (c for c in gscpi.columns if any(k in c.lower() for k in ["gscpi","value","index","score"])),
        None
    )

    if not date_col or not val_col:
        raise ValueError(
            f"Cannot find date/value columns in GSCPI CSV.\n"
            f"Found: {list(gscpi.columns)}\n"
            f"Rename to 'date' and 'gscpi'."
        )

    gscpi = gscpi[[date_col, val_col]].copy()
    gscpi.columns = ["date", "gscpi"]
    gscpi["date"]  = pd.to_datetime(gscpi["date"], infer_datetime_format=True, errors="coerce")
    gscpi["gscpi"] = pd.to_numeric(gscpi["gscpi"], errors="coerce")
    gscpi = gscpi.dropna().sort_values("date").reset_index(drop=True)

    mean_val  = gscpi["gscpi"].mean()
    std_val   = gscpi["gscpi"].std()
    threshold = mean_val + GSCPI_THRESHOLD * std_val
    gscpi["is_spike"] = (gscpi["gscpi"] >= threshold).astype(int)

    spike_count = gscpi["is_spike"].sum()
    print(f"        GSCPI  mean={mean_val:.3f}  std={std_val:.3f}  "
          f"threshold={threshold:.3f}  ({GSCPI_THRESHOLD}σ)")
    print(f"        Spike months: {spike_count}/{len(gscpi)}  "
          f"({spike_count/len(gscpi)*100:.1f}%)")
    return gscpi


def build_labels(feature_df: pd.DataFrame, gscpi: pd.DataFrame) -> pd.DataFrame:
    """
    label = 1 if any GSCPI spike month overlaps the next LABEL_WINDOW days
    after each week_start row.
    """
    # Expand monthly spikes to a set of daily dates
    spike_dates = set()
    for _, row in gscpi[gscpi["is_spike"] == 1].iterrows():
        month_start = row["date"].replace(day=1)
        month_end   = month_start + pd.offsets.MonthEnd(0)
        for d in pd.date_range(month_start, month_end, freq="D"):
            spike_dates.add(d.date())

    def label_row(week_start):
        for offset in range(0, LABEL_WINDOW + 1):
            if (week_start + pd.Timedelta(days=offset)).date() in spike_dates:
                return 1
        return 0

    feature_df = feature_df.copy()
    feature_df["label"] = feature_df["week_start"].apply(label_row)

    pos = int(feature_df["label"].sum())
    neg = len(feature_df) - pos
    print(f"        Labels — positive (1): {pos}  negative (0): {neg}  "
          f"imbalance ratio: 1:{neg//max(pos,1)}")
    return feature_df


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — TRAIN / TEST TEMPORAL SPLIT
# ══════════════════════════════════════════════════════════════════════════════

def split_train_test(df: pd.DataFrame):
    """
    Temporal split to prevent data leakage:
      Train : 2019 – 2022
      Test  : 2023 – 2024
    """
    print(f"\n  [5/6] Temporal split  train≤{TRAIN_END}  /  test≥{TEST_START}")

    train = df[df["week_start"] <= TRAIN_END].copy()
    test  = df[df["week_start"] >= TEST_START].copy()

    print(f"        Train : {len(train):>6,} rows  |  "
          f"label=1: {int(train['label'].sum())}  ({train['label'].mean()*100:.1f}%)")
    print(f"        Test  : {len(test):>6,} rows  |  "
          f"label=1: {int(test['label'].sum())}  ({test['label'].mean()*100:.1f}%)")
    return train, test


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — SMOTE OVERSAMPLING  (train set only)
# ══════════════════════════════════════════════════════════════════════════════

def apply_smote(train: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """
    Apply SMOTE to the training set only.
    - Fills NaN with 0 before resampling
    - Marks synthetic rows with is_synthetic=1
    - Returns a flat DataFrame with feature_cols + label + is_synthetic
    """
    print(f"\n  [6/6] Applying SMOTE to training set...")

    if not SMOTE_AVAILABLE:
        print("        ⚠  Skipped — install imbalanced-learn to enable SMOTE.")
        train = train[feature_cols + ["label"]].copy()
        train["is_synthetic"] = 0
        return train

    X = train[feature_cols].fillna(0).values
    y = train["label"].values

    class_counts = dict(zip(*np.unique(y, return_counts=True)))
    min_class    = min(class_counts.values())
    print(f"        Before — class 0: {class_counts.get(0,0):,}  "
          f"class 1: {class_counts.get(1,0):,}")

    if class_counts.get(1, 0) < 2:
        print("        ⚠  Fewer than 2 positive samples — SMOTE skipped.")
        train = train[feature_cols + ["label"]].copy()
        train["is_synthetic"] = 0
        return train

    k = min(5, min_class - 1)
    smote = SMOTE(random_state=SMOTE_RANDOM_STATE, k_neighbors=k)
    X_res, y_res = smote.fit_resample(X, y)

    new_counts = dict(zip(*np.unique(y_res, return_counts=True)))
    print(f"        After  — class 0: {new_counts.get(0,0):,}  "
          f"class 1: {new_counts.get(1,0):,}")

    df_smote = pd.DataFrame(X_res, columns=feature_cols)
    df_smote["label"] = y_res

    n_original = len(train)
    df_smote["is_synthetic"] = 0
    df_smote.loc[n_original:, "is_synthetic"] = 1

    return df_smote


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="T4 — NewsShield Feature Engineering Pipeline"
    )
    parser.add_argument("--json",  default=DEFAULT_JSON,
                        help="Path to LLM extractions JSON")
    parser.add_argument("--gscpi", default=DEFAULT_GSCPI,
                        help="Path to GSCPI CSV")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print("  NEWSSHIELD — T4 FEATURE ENGINEERING PIPELINE")
    print("=" * 65)

    # Input validation
    missing = []
    if not os.path.exists(args.json):
        missing.append(f"  ❌ JSON not found  : {args.json}")
    if not os.path.exists(args.gscpi):
        missing.append(f"  ❌ GSCPI not found : {args.gscpi}")
    if missing:
        print("\n" + "\n".join(missing))
        print("\n  Waiting for Member B's full extraction dataset.")
        print("  Test with sample data:")
        print("  python src/feature_engineering.py "
              "--json gdelt_output/final_extraction_100.json\n")
        sys.exit(1)

    # Run pipeline
    df          = load_extractions(args.json)
    groups      = build_groups(df)
    features    = add_rolling_features(groups)
    gscpi       = load_gscpi(args.gscpi)
    features    = build_labels(features, gscpi)
    train, test = split_train_test(features)

    # Feature columns = everything except meta + label
    meta_cols    = ["industry", "region", "week_start", "label"]
    feature_cols = [c for c in features.columns if c not in meta_cols]

    # SMOTE on train only
    train_smote = apply_smote(train, feature_cols)

    # Save outputs
    features_path = f"{OUTPUT_DIR}/feature_matrix.csv"
    smote_path    = f"{OUTPUT_DIR}/feature_matrix_smote.csv"
    dist_path     = f"{OUTPUT_DIR}/label_distribution.csv"
    names_path    = f"{OUTPUT_DIR}/feature_names.txt"

    features.to_csv(features_path, index=False)
    train_smote.to_csv(smote_path, index=False)

    label_dist = pd.DataFrame({
        "split":        ["train_original", "train_smote", "test"],
        "total":        [len(train), len(train_smote), len(test)],
        "label_1":      [int(train["label"].sum()),
                         int(train_smote["label"].sum()),
                         int(test["label"].sum())],
        "label_0":      [int((train["label"]==0).sum()),
                         int((train_smote["label"]==0).sum()),
                         int((test["label"]==0).sum())],
        "pct_positive": [round(train["label"].mean()*100, 1),
                         round(train_smote["label"].mean()*100, 1),
                         round(test["label"].mean()*100, 1)],
    })
    label_dist.to_csv(dist_path, index=False)

    with open(names_path, "w") as f:
        for col in feature_cols:
            f.write(col + "\n")

    # Final report
    base_count = 2 + len(SIGNAL_TYPES) + len(DISRUPTION_CATEGORIES) + len(PROPAGATION_LEVELS)
    print("\n" + "=" * 65)
    print("  PIPELINE COMPLETE")
    print("=" * 65)
    print(f"\n  Feature breakdown:")
    print(f"    Base features  : {base_count}  "
          f"(article_count, avg_severity, "
          f"{len(SIGNAL_TYPES)} signal types, "
          f"{len(DISRUPTION_CATEGORIES)} categories, "
          f"{len(PROPAGATION_LEVELS)} propagation levels)")
    print(f"    Rolling cols   : {base_count} × 3  (r7, r14, wow)  =  {base_count*3}")
    print(f"    Total features : {len(feature_cols)}")
    print(f"\n  Row counts:")
    print(f"    Full matrix    : {len(features):,}")
    print(f"    Train original : {len(train):,}")
    print(f"    Train SMOTE    : {len(train_smote):,}")
    print(f"    Test           : {len(test):,}")
    print(f"\n  Class balance:")
    print(label_dist.to_string(index=False))
    print(f"\n  Saved → {features_path}")
    print(f"  Saved → {smote_path}")
    print(f"  Saved → {dist_path}")
    print(f"  Saved → {names_path}")
    print(f"\n  ✅ Pass feature_matrix_smote.csv to T5 model training\n")


if __name__ == "__main__":
    main()