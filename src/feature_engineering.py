"""
T4 — Feature Engineering Pipeline (NewsShield: Supply Chain Disruption Prediction)
====================================================================================
Adapted for actual GDELT CSV schema with columns:
  GlobalEventID, Day, MonthYear, Year, Actor1Code, Actor1Name,
  Actor2Code, Actor2Name, IsRootEvent, EventCode, EventBaseCode,
  EventRootCode, QuadClass, GoldsteinScale, NumMentions, NumSources,
  NumArticles, AvgTone, Actor1Geo_CountryCode, Actor2Geo_CountryCode,
  ActionGeo_CountryCode, ActionGeo_Lat, ActionGeo_Long,
  SOURCEURL, SourceMonth, SourceLabel

Input:
    data/raw/*.csv               ← GDELT event CSV files
    gdelt_output/gscpi_clean.csv ← NY Fed GSCPI monthly index  (optional)

Output:
    gdelt_output/feature_matrix.csv          ← full ML feature matrix
    gdelt_output/feature_matrix_smote.csv    ← oversampled train set
    gdelt_output/label_distribution.csv      ← class balance report
    gdelt_output/feature_names.txt           ← feature column names
    gdelt_output/feature_matrix_test.csv     ← held-out test set

Run:
    python feature_engineering.py                          # uses data/raw/
    python feature_engineering.py --raw /path/to/csvs     # custom directory
    python feature_engineering.py --demo                   # run on sample file
"""

import os
import glob
import argparse
import warnings
import numpy as np
import pandas as pd
from sklearn.utils import resample

warnings.filterwarnings("ignore")

# ── Try imbalanced-learn; fall back to sklearn resample ───────────────────────
try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
    print("  ✅ imbalanced-learn available — will use SMOTE")
except ImportError:
    SMOTE_AVAILABLE = False
    print("  ⚠  imbalanced-learn not available — will use sklearn resample fallback")

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════
RAW_DIR           = "data/raw"
OUTPUT_DIR        = "gdelt_output"
GSCPI_PATH        = "gdelt_output/gscpi_clean.csv"
GSCPI_THRESHOLD   = 1.5        # σ above mean = disruption spike
LABEL_WINDOW      = 14         # days ahead to look for GSCPI spike
TRAIN_END  = "2022-01-15"
TEST_START = "2022-01-16"
RANDOM_STATE      = 42

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# CAMEO CODE MAPPINGS
# EventCode → disruption_category
# ══════════════════════════════════════════════════════════════════════════════
CAMEO_TO_CATEGORY = {
    # Trade restrictions / sanctions
    "172":  "trade_policy",   # Impose embargo / sanctions
    "173":  "trade_policy",   # Reduce or restrict trade
    "131":  "trade_policy",   # Threaten with political sanctions
    "132":  "trade_policy",   # Threaten with economic sanctions
    "1321": "trade_policy",   # Threaten trade restriction
    "1322": "trade_policy",   # Threaten with sanctions
    "203":  "trade_policy",   # Appeal for trade
    # Port / blockade disruptions
    "174":  "port",           # Impose blockade / restrict passage
    "175":  "port",           # Halt negotiations (shipping context)
    # Labor / protest events
    "140":  "labor",          # Protest (general)
    "141":  "labor",          # Strike / hunger strike
    "143":  "labor",          # Strike or boycott
    "145":  "labor",          # Protest violently
    # Geopolitical coercion
    "170":  "geopolitical",   # Coerce (general)
    "130":  "geopolitical",   # Threaten (general)
    "190":  "geopolitical",   # Unconventional mass violence
    "180":  "geopolitical",   # Conventional military force
    # Economic cooperation / aid
    "202":  "economic",       # Appeal for economic aid
    "204":  "economic",       # Appeal for economic cooperation
    "163":  "economic",       # Impose economic aid / investment
}

DISRUPTION_CATEGORIES = sorted(set(CAMEO_TO_CATEGORY.values()))
# geopolitical is default for unmapped codes — add it explicitly
if "geopolitical" not in DISRUPTION_CATEGORIES:
    DISRUPTION_CATEGORIES = sorted(DISRUPTION_CATEGORIES + ["geopolitical"])

# ══════════════════════════════════════════════════════════════════════════════
# EventRootCode → signal_type  (1 or 2 digit root code)
# ══════════════════════════════════════════════════════════════════════════════
CAMEO_TO_SIGNAL = {
    "01": "response",       "1":  "response",    # Public statement
    "02": "response",       "2":  "response",    # Appeal
    "03": "response",       "3":  "response",    # Intent to cooperate
    "04": "propagation",    "4":  "propagation", # Consult
    "05": "propagation",    "5":  "propagation", # Diplomatic cooperation
    "06": "response",       "6":  "response",    # Material cooperation
    "07": "amplifier",      "7":  "amplifier",   # Provide aid
    "08": "precursor",      "8":  "precursor",   # Yield
    "09": "precursor",      "9":  "precursor",   # Investigate
    "10": "precursor",                           # Demand
    "11": "precursor",                           # Disapprove
    "12": "precursor",                           # Reject
    "13": "trigger",                             # Threaten
    "14": "trigger",                             # Protest
    "15": "trigger",                             # Exhibit force posture
    "16": "trigger",                             # Reduce relations
    "17": "trigger",                             # Coerce (trade restrict)
    "18": "trigger",                             # Assault
    "19": "trigger",                             # Fight
    "20": "trigger",                             # Mass violence
}

SIGNAL_TYPES = sorted(set(CAMEO_TO_SIGNAL.values()))

# ══════════════════════════════════════════════════════════════════════════════
# Country code → broad region
# (Actor1Geo_CountryCode uses FIPS 2-letter codes in this dataset)
# ══════════════════════════════════════════════════════════════════════════════
COUNTRY_TO_REGION = {
    "US": "North_America", "CA": "North_America", "MX": "North_America",
    "UK": "Europe",  "FR": "Europe",  "DE": "Europe",  "IT": "Europe",
    "SP": "Europe",  "NL": "Europe",  "PL": "Europe",  "GR": "Europe",
    "CH": "Europe",  "NO": "Europe",  "SW": "Europe",  "FI": "Europe",
    "GM": "Europe",  "AU": "Europe",  # Germany (FIPS=GM), Austria(AU)
    "CN": "East_Asia", "JA": "East_Asia", "KS": "East_Asia",
    "TW": "East_Asia", "HK": "East_Asia", "JP": "East_Asia",
    "IN": "South_Asia", "PK": "South_Asia", "BD": "South_Asia",
    "RS": "Russia_CIS", "UP": "Russia_CIS", "UZ": "Russia_CIS",
    "IS": "Middle_East", "SA": "Middle_East", "IR": "Middle_East",
    "TU": "Middle_East", "IZ": "Middle_East", "LE": "Middle_East",
    "NI": "Africa", "SF": "Africa", "EG": "Africa",
    "GH": "Africa", "KE": "Africa", "MO": "Africa",
    "BR": "Latin_America", "AR": "Latin_America", "CI": "Latin_America",
    "PE": "Latin_America", "CL": "Latin_America", "CO": "Latin_America",
    "AS": "Asia_Pacific", "RP": "Asia_Pacific", "TH": "Asia_Pacific",
    "VM": "Asia_Pacific", "ID": "Asia_Pacific", "SN": "Asia_Pacific",
    "PP": "Asia_Pacific",  # Papua New Guinea
}


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — LOAD & CLEAN GDELT CSVs
# ══════════════════════════════════════════════════════════════════════════════

def load_gdelt(raw_dir: str, demo_file: str = None) -> pd.DataFrame:
    print(f"\n  [1/6] Loading GDELT event files...")

    if demo_file:
        csv_files = [demo_file]
        print(f"        DEMO mode — using: {demo_file}")
    else:
        csv_files = sorted(glob.glob(f"{raw_dir}/*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in '{raw_dir}/'.\n"
            f"  → Put your GDELT monthly CSVs there, or pass --demo for the sample file."
        )

    parts = []
    for f in csv_files:
        try:
            df = pd.read_csv(f, on_bad_lines="skip", low_memory=False)
            if len(df) < 5:
                print(f"        ⚠  Skipped (too small): {os.path.basename(f)}")
                continue
            parts.append(df)
            print(f"        ✅  {os.path.basename(f):<45} {len(df):>7,} rows")
        except Exception as e:
            print(f"        ❌  {os.path.basename(f):<45} ERROR: {e}")

    combined = pd.concat(parts, ignore_index=True)
    print(f"\n        Raw total: {len(combined):,} rows")

    # ── Parse date from 'Day' column (YYYYMMDD int) ───────────────────────────
    combined["published_date"] = pd.to_datetime(
        combined["Day"].astype(str).str[:8],
        format="%Y%m%d",
        errors="coerce"
    )
    combined = combined.dropna(subset=["published_date"])

    # For demo/single-month files we relax the date filter so we keep all rows;
    # for multi-year runs we enforce 2019–2024.
    if not demo_file:
        combined = combined[
            (combined["published_date"] >= "2019-01-01") &
            (combined["published_date"] <= "2024-12-31")
        ]

    # ── EventCode → disruption_category ──────────────────────────────────────
    combined["EventCode_str"] = combined["EventCode"].astype(str).str.strip()
    combined["disruption_category"] = (
        combined["EventCode_str"].map(CAMEO_TO_CATEGORY).fillna("geopolitical")
    )

    # ── EventRootCode → signal_type ───────────────────────────────────────────
    combined["EventRootCode_str"] = (
        combined["EventRootCode"].astype(str).str.strip().str.zfill(2)
    )
    combined["signal_type"] = (
        combined["EventRootCode_str"].map(CAMEO_TO_SIGNAL).fillna("trigger")
    )

    # ── Country → region (prefer Actor1Geo_CountryCode) ───────────────────────
    combined["region"] = combined["Actor1Geo_CountryCode"].map(COUNTRY_TO_REGION)
    # fallback to Actor2
    mask = combined["region"].isna()
    combined.loc[mask, "region"] = (
        combined.loc[mask, "Actor2Geo_CountryCode"].map(COUNTRY_TO_REGION)
    )
    combined["region"] = combined["region"].fillna("Other")

    # ── Severity: GoldsteinScale (-10 → +10) mapped to 1–5 ───────────────────
    # More negative = more conflictual = higher disruption severity
    gs = combined["GoldsteinScale"].clip(-10, 10)
    combined["severity_score"] = ((-gs + 10) / 20 * 4 + 1).round().clip(1, 5).astype(int)

    # ── Propagation proxy from NumMentions ────────────────────────────────────
    def _prop_risk(n):
        if n <= 2:   return "local"
        if n <= 10:  return "regional"
        return "global"
    combined["propagation_risk"] = combined["NumMentions"].apply(_prop_risk)

    # ── QuadClass-based conflict flag (3=Verbal Conflict, 4=Material Conflict)
    combined["is_conflict"] = combined["QuadClass"].isin([3, 4]).astype(int)

    # ── Week start (Monday) ───────────────────────────────────────────────────
    combined["week_start"] = (
        combined["published_date"]
        - pd.to_timedelta(combined["published_date"].dt.weekday, unit="d")
    ).dt.normalize()

    print(f"        After cleaning : {len(combined):,} rows")
    print(f"        Date range     : "
          f"{combined['published_date'].min().date()} → "
          f"{combined['published_date'].max().date()}")
    print(f"        Regions        : {combined['region'].nunique()}")
    print(f"        Disrupt cats   : {combined['disruption_category'].value_counts().to_dict()}")
    print(f"        Signal types   : {combined['signal_type'].value_counts().to_dict()}")
    return combined


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — GROUP BY region × week  →  base feature rows
# ══════════════════════════════════════════════════════════════════════════════

def build_groups(df: pd.DataFrame) -> pd.DataFrame:
    print("\n  [2/6] Building region × week feature groups...")

    rows = []
    for (region, week), grp in df.groupby(["region", "week_start"]):
        n = len(grp)

        row = {
            "region":              region,
            "week_start":          week,
            # ── Volume features ──────────────────────────────────────────────
            "article_count":       n,
            "num_mentions_sum":    grp["NumMentions"].sum(),
            "num_sources_sum":     grp["NumSources"].sum(),
            "num_articles_sum":    grp["NumArticles"].sum(),
            # ── Sentiment / intensity features ───────────────────────────────
            "avg_tone":            round(float(grp["AvgTone"].mean()), 4),
            "std_tone":            round(float(grp["AvgTone"].std() or 0), 4),
            "avg_goldstein":       round(float(grp["GoldsteinScale"].mean()), 4),
            "avg_severity":        round(float(grp["severity_score"].mean()), 4),
            "max_severity":        int(grp["severity_score"].max()),
            # ── Conflict ratio ────────────────────────────────────────────────
            "conflict_ratio":      round((grp["AvgTone"] < 0).sum() / n, 4),
            "conflict_event_ratio":round(grp["is_conflict"].mean(), 4),
            # ── Source diversity ──────────────────────────────────────────────
            "root_event_ratio":    round(grp["IsRootEvent"].apply(
                                       lambda x: 1 if str(x).upper() in ("1","TRUE","COP") else 0
                                   ).mean(), 4),
        }

        # ── Signal type proportions (precursor / trigger / propagation / …) ──
        sig_counts = grp["signal_type"].value_counts()
        for s in SIGNAL_TYPES:
            row[f"sig_{s}"] = round(sig_counts.get(s, 0) / n, 4)

        # ── Disruption category proportions ───────────────────────────────────
        cat_counts = grp["disruption_category"].value_counts()
        for c in DISRUPTION_CATEGORIES:
            row[f"cat_{c}"] = round(cat_counts.get(c, 0) / n, 4)

        # ── Propagation proportions ────────────────────────────────────────────
        prop_counts = grp["propagation_risk"].value_counts()
        for p in ["local", "regional", "global"]:
            row[f"prop_{p}"] = round(prop_counts.get(p, 0) / n, 4)

        rows.append(row)

    groups = (
        pd.DataFrame(rows)
        .sort_values(["region", "week_start"])
        .reset_index(drop=True)
    )

    print(f"        Created {len(groups):,} group rows | "
          f"{groups['region'].nunique()} regions | "
          f"{groups['week_start'].nunique()} unique weeks")
    return groups


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — ROLLING FEATURES (7d ≈ 1 week, 14d ≈ 2 weeks + WoW change)
# ══════════════════════════════════════════════════════════════════════════════

def add_rolling_features(groups: pd.DataFrame) -> pd.DataFrame:
    print("\n  [3/6] Computing rolling features (r7, r14, WoW)...")

    meta_cols  = {"region", "week_start"}
    base_cols  = [c for c in groups.columns if c not in meta_cols]

    parts = []
    for region, grp in groups.groupby("region"):
        grp = grp.sort_values("week_start").copy()
        for col in base_cols:
            s = grp[col]
            grp[f"{col}_r7"]  = s.rolling(window=1, min_periods=1).mean()   # 1-wk rolling
            grp[f"{col}_r14"] = s.rolling(window=2, min_periods=1).mean()   # 2-wk rolling
            grp[f"{col}_wow"] = (
                s.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
            )
        parts.append(grp)

    result = (
        pd.concat(parts, ignore_index=True)
        .sort_values(["region", "week_start"])
        .reset_index(drop=True)
    )

    rolling_added = len(base_cols) * 3
    print(f"        Added {rolling_added} rolling columns "
          f"({len(base_cols)} base × 3 transforms)")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — BUILD Y LABELS FROM GSCPI  (or synthetic labels for demo)
# ══════════════════════════════════════════════════════════════════════════════

def load_gscpi(path: str) -> pd.DataFrame:
    """Load NY Fed GSCPI CSV.  Expects columns: date (or similar), gscpi (or similar)."""
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
            f"Cannot auto-detect date/value columns in GSCPI CSV.\n"
            f"Found: {list(gscpi.columns)}\n"
            f"Please rename columns to 'date' and 'gscpi'."
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


def make_synthetic_gscpi(feature_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate synthetic GSCPI labels when real GSCPI is unavailable.
    Uses high-conflict-ratio weeks as positive label proxies (~20% rate).
    Only used in demo mode — replace with real GSCPI for production.
    """
    print("\n  [4/6] GSCPI not found — generating synthetic labels (demo only).")
    print("        ⚠  Replace with real GSCPI from https://www.newyorkfed.org/research/gscpi")

    # Build a synthetic monthly index: high avg_goldstein (more negative = more stress)
    monthly = (
        feature_df
        .assign(month=lambda d: d["week_start"].dt.to_period("M"))
        .groupby("month")["avg_goldstein"].mean()
        .reset_index()
    )
    monthly.columns = ["date", "gscpi"]
    # Convert period to timestamp
    monthly["date"] = monthly["date"].dt.to_timestamp()
    # Invert sign so negative goldstein = higher stress index
    monthly["gscpi"] = -monthly["gscpi"]

    mean_val  = monthly["gscpi"].mean()
    std_val   = monthly["gscpi"].std()
    threshold = mean_val + GSCPI_THRESHOLD * std_val
    monthly["is_spike"] = (monthly["gscpi"] >= threshold).astype(int)

    spike_count = monthly["is_spike"].sum()
    print(f"        Synthetic GSCPI — spikes: {spike_count}/{len(monthly)} months")
    return monthly


def build_labels(feature_df: pd.DataFrame, gscpi: pd.DataFrame) -> pd.DataFrame:
    """
    Label = 1 if a GSCPI spike occurs within the next LABEL_WINDOW days
    of week_start; else 0.
    """
    # Build a set of all calendar dates that fall inside a spike month
    spike_dates = set()
    for _, row in gscpi[gscpi["is_spike"] == 1].iterrows():
        month_start = row["date"].replace(day=1)
        month_end   = month_start + pd.offsets.MonthEnd(0)
        for d in pd.date_range(month_start, month_end, freq="D"):
            spike_dates.add(d.date())

    def label_row(week_start):
        for offset in range(0, LABEL_WINDOW + 1):
            check_date = (week_start + pd.Timedelta(days=offset)).date()
            if check_date in spike_dates:
                return 1
        return 0

    feature_df = feature_df.copy()
    feature_df["label"] = feature_df["week_start"].apply(label_row)

    pos = int(feature_df["label"].sum())
    neg = len(feature_df) - pos
    ratio = neg // max(pos, 1)
    print(f"        Labels — positive(1): {pos}  negative(0): {neg}  "
          f"imbalance 1:{ratio}")
    return feature_df


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — TEMPORAL TRAIN / TEST SPLIT
# ══════════════════════════════════════════════════════════════════════════════

def split_train_test(df: pd.DataFrame):
    print(f"\n  [5/6] Temporal split  "
          f"train ≤ {TRAIN_END}  /  test ≥ {TEST_START}")

    train = df[df["week_start"] <= TRAIN_END].copy()
    test  = df[df["week_start"] >= TEST_START].copy()

    # If no split is possible (single-month demo file), use 80/20 row split
    if len(train) == 0 or len(test) == 0:
        print("        ⚠  Date range doesn't span train/test boundary — "
              "using 80/20 row split (demo mode).")
        split_idx = int(len(df) * 0.8)
        train = df.iloc[:split_idx].copy()
        test  = df.iloc[split_idx:].copy()

    print(f"        Train : {len(train):>6,} rows  | "
          f"label=1: {int(train['label'].sum())}  "
          f"({train['label'].mean()*100:.1f}%)")
    print(f"        Test  : {len(test):>6,} rows  | "
          f"label=1: {int(test['label'].sum())}  "
          f"({test['label'].mean()*100:.1f}%)")
    return train, test


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — OVERSAMPLE MINORITY CLASS IN TRAIN SET
# Uses SMOTE if imbalanced-learn is available, else sklearn resample
# ══════════════════════════════════════════════════════════════════════════════

def apply_oversampling(train: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    print(f"\n  [6/6] Balancing training set...")

    X     = train[feature_cols].fillna(0).values
    y     = train["label"].values
    class_counts = dict(zip(*np.unique(y, return_counts=True)))
    n0    = class_counts.get(0, 0)
    n1    = class_counts.get(1, 0)
    print(f"        Before — class 0: {n0:,}  class 1: {n1:,}")

    if n1 < 2:
        print("        ⚠  Too few positives to oversample — returning as-is.")
        out = train[feature_cols + ["label"]].copy()
        out["is_synthetic"] = 0
        return out

    if SMOTE_AVAILABLE:
        k     = min(5, n1 - 1)
        smote = SMOTE(random_state=RANDOM_STATE, k_neighbors=k)
        X_res, y_res = smote.fit_resample(X, y)
        method = "SMOTE"
    else:
        # sklearn fallback: upsample minority class with replacement
        X0, y0 = X[y == 0], y[y == 0]
        X1, y1 = X[y == 1], y[y == 1]
        X1_up  = resample(X1, replace=True, n_samples=n0, random_state=RANDOM_STATE)
        y1_up  = np.ones(n0, dtype=int)
        X_res  = np.vstack([X0, X1_up])
        y_res  = np.concatenate([y0, y1_up])
        method = "sklearn resample"

    new_counts = dict(zip(*np.unique(y_res, return_counts=True)))
    print(f"        After  — class 0: {new_counts.get(0,0):,}  "
          f"class 1: {new_counts.get(1,0):,}  [{method}]")

    df_out = pd.DataFrame(X_res, columns=feature_cols)
    df_out["label"] = y_res
    # Mark rows beyond original length as synthetic
    df_out["is_synthetic"] = 0
    df_out.loc[len(train):, "is_synthetic"] = 1
    return df_out


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="T4 NewsShield Feature Engineering Pipeline"
    )
    parser.add_argument("--raw",   default=RAW_DIR,
                        help=f"Directory containing GDELT CSVs (default: {RAW_DIR})")
    parser.add_argument("--gscpi", default=GSCPI_PATH,
                        help=f"Path to GSCPI CSV (default: {GSCPI_PATH})")
    parser.add_argument("--demo",  action="store_true",
                        help="Run on the uploaded sample file at "
                             "/mnt/user-data/uploads/gdelt_2019-03.csv")
    args = parser.parse_args()

    demo_file = None
    if args.demo:
        demo_file = "/mnt/user-data/uploads/gdelt_2019-03.csv"
        if not os.path.exists(demo_file):
            demo_file = "gdelt_2019-03.csv"

    print("\n" + "="*65)
    print("  NEWSSHIELD — T4 FEATURE ENGINEERING PIPELINE")
    print("="*65)

    # ── Step 1: Load ─────────────────────────────────────────────────────────
    df = load_gdelt(args.raw, demo_file=demo_file)

    # ── Step 2: Group features ───────────────────────────────────────────────
    groups = build_groups(df)

    # ── Step 3: Rolling features ─────────────────────────────────────────────
    features = add_rolling_features(groups)

    # ── Step 4: Labels ───────────────────────────────────────────────────────
    if os.path.exists(args.gscpi):
        gscpi = load_gscpi(args.gscpi)
    else:
        gscpi = make_synthetic_gscpi(features)

    features = build_labels(features, gscpi)

    # ── Step 5: Train/test split ─────────────────────────────────────────────
    train, test = split_train_test(features)

    # ── Identify feature columns (exclude metadata) ──────────────────────────
    meta_cols    = {"region", "week_start", "label"}
    feature_cols = [c for c in features.columns if c not in meta_cols]

    # ── Step 6: Oversample train ─────────────────────────────────────────────
    train_balanced = apply_oversampling(train, feature_cols)

    # ══════════════════════════════════════════════════════════════════════════
    # SAVE OUTPUTS
    # ══════════════════════════════════════════════════════════════════════════
    paths = {
        "feature_matrix":       f"{OUTPUT_DIR}/feature_matrix.csv",
        "feature_matrix_smote": f"{OUTPUT_DIR}/feature_matrix_smote.csv",
        "feature_matrix_test":  f"{OUTPUT_DIR}/feature_matrix_test.csv",
        "label_distribution":   f"{OUTPUT_DIR}/label_distribution.csv",
        "feature_names":        f"{OUTPUT_DIR}/feature_names.txt",
    }

    features.to_csv(paths["feature_matrix"], index=False)
    train_balanced.to_csv(paths["feature_matrix_smote"], index=False)
    test[feature_cols + ["label"]].to_csv(paths["feature_matrix_test"], index=False)

    label_dist = pd.DataFrame({
        "split":        ["train_original", "train_balanced", "test"],
        "total":        [len(train), len(train_balanced), len(test)],
        "label_1":      [int(train["label"].sum()),
                         int(train_balanced["label"].sum()),
                         int(test["label"].sum())],
        "label_0":      [int((train["label"] == 0).sum()),
                         int((train_balanced["label"] == 0).sum()),
                         int((test["label"] == 0).sum())],
        "pct_positive": [round(train["label"].mean() * 100, 1),
                         round(train_balanced["label"].mean() * 100, 1),
                         round(test["label"].mean() * 100, 1)],
    })
    label_dist.to_csv(paths["label_distribution"], index=False)

    with open(paths["feature_names"], "w") as f:
        for col in feature_cols:
            f.write(col + "\n")

    # ══════════════════════════════════════════════════════════════════════════
    # FINAL REPORT
    # ══════════════════════════════════════════════════════════════════════════
    base_count = len([
        c for c in feature_cols
        if not any(c.endswith(s) for s in ["_r7", "_r14", "_wow"])
    ])

    print("\n" + "="*65)
    print("  PIPELINE COMPLETE")
    print("="*65)
    print(f"\n  Feature breakdown:")
    print(f"    Base features          : {base_count}")
    print(f"    Rolling variants (×3)  : {base_count * 3}  (r7, r14, wow)")
    print(f"    Total feature columns  : {len(feature_cols)}")
    print(f"\n  Row counts:")
    print(f"    Full matrix            : {len(features):,}")
    print(f"    Train (original)       : {len(train):,}")
    print(f"    Train (balanced)       : {len(train_balanced):,}")
    print(f"    Test                   : {len(test):,}")
    print(f"\n  Class balance:")
    print(label_dist.to_string(index=False))
    print(f"\n  Outputs:")
    for name, path in paths.items():
        print(f"    ✅  {path}")
    print(f"\n  Ready for T5 model training ✓\n")


if __name__ == "__main__":
    main()