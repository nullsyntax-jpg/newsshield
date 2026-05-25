"""
inspect_and_prepare.py
======================
Prepares clean input for Member B from gdelt_all_supply_chain.csv
Uses Option B: SourceLabel + Actor names as pseudo-headline (no scraping needed)

Run:
    python src/inspect_and_prepare.py
"""

import os
import pandas as pd

OUTPUT_DIR  = "gdelt_output"
SOURCE_FILE = "data/raw/gdelt_all_supply_chain.csv"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Load full file ───────────────────────────────────────────────────────────
print(f"\n  Loading {SOURCE_FILE}...")
df = pd.read_csv(SOURCE_FILE, on_bad_lines="skip", low_memory=False)
print(f"  Loaded {len(df):,} rows x {len(df.columns)} columns")

# ── Show ALL columns with sample values to diagnose ─────────────────────────
print(f"\n  COLUMN AUDIT (name → sample value):")
print(f"  {'-'*60}")
for col in df.columns:
    sample = df[col].dropna().iloc[0] if df[col].notna().any() else "ALL NULL"
    print(f"  {col:<30} → {str(sample)[:60]}")

# ── Parse date from Day column (YYYYMMDD integer) ───────────────────────────
df["published_date"] = pd.to_datetime(
    df["Day"].astype(str).str[:8],
    format="%Y%m%d",
    errors="coerce"
).dt.strftime("%Y-%m-%d")

df = df.dropna(subset=["published_date"])
print(f"\n  After date parse: {len(df):,} rows")
print(f"  Date range: {df['published_date'].min()} → {df['published_date'].max()}")

# ── Find the real URL column ─────────────────────────────────────────────────
print(f"\n  FINDING URL COLUMN — checking which column has http links:")
for col in df.columns:
    sample_vals = df[col].dropna().astype(str).head(10)
    http_count = sample_vals.str.startswith("http").sum()
    if http_count > 0:
        print(f"  ✅ '{col}' has {http_count}/10 rows starting with http")
        url_col = col
        break
else:
    print(f"  ⚠  No URL column found — will use text fields only")
    url_col = None

# ── Build pseudo-headline from available text fields ─────────────────────────
# Combine Actor1Name + Actor2Name + SourceLabel as context for Member B
text_cols = []
for col in ["Actor1Name", "Actor2Name", "SourceLabel", "EventCode",
            "ActionGeo_CountryCode", "Actor1Geo_CountryCode"]:
    if col in df.columns:
        text_cols.append(col)

print(f"\n  Text columns available for pseudo-headline: {text_cols}")

df["pseudo_headline"] = (
    df[text_cols]
    .fillna("")
    .astype(str)
    .apply(lambda row: " | ".join(v for v in row if v not in ("", "nan")), axis=1)
)

# ── Build output ─────────────────────────────────────────────────────────────
output_cols = ["published_date", "pseudo_headline"]
if url_col:
    output_cols.append(url_col)

output = df[output_cols].copy()
output = output[output["pseudo_headline"].str.len() > 3]
output = output.sort_values("published_date").reset_index(drop=True)
output.insert(0, "id", range(1, len(output) + 1))

if url_col:
    output.rename(columns={url_col: "source_url"}, inplace=True)

output_path = f"{OUTPUT_DIR}/member_b_input.csv"
output.to_csv(output_path, index=False)

size_mb = os.path.getsize(output_path) / 1024 / 1024

print(f"\n{'='*65}")
print(f"  OUTPUT SUMMARY")
print(f"{'='*65}")
print(f"  Total rows      : {len(output):,}")
print(f"  Date range      : {output['published_date'].min()} → {output['published_date'].max()}")
print(f"  File size       : {size_mb:.1f} MB")
print(f"\n  Sample rows:")
print(output.head(5).to_string())
print(f"\n  Saved → {output_path}")