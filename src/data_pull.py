"""
GDELT 2.0 Supply Chain Event Scraper
=====================================
No BigQuery. No account. Pure Python.
 
Strategy: Download ~2 files per day (one morning, one evening slot)
for targeted months 2019-2024. Filter by CAMEO supply-chain event codes.
 
CAMEO codes filtered:
  13 = Threaten
  14 = Protest / demonstrate
  17 = Coerce
  20 = Assault / armed attack
  1211 = Impose economic sanctions
  1221 = Impose embargo
  141  = Demonstrate or rally (economic)
  172  = Impose administrative sanctions
 
Run: pip install requests pandas tqdm
Then: python gdelt_pipeline.py
"""
 
import requests
import zipfile
import io
import pandas as pd
import time
import os
import logging
from datetime import datetime, timedelta
from tqdm import tqdm
 
# ── Config ────────────────────────────────────────────────────────────────────
 
OUTPUT_DIR = r"C:\Users\Janhavi Patil\newsshield\data\raw"

os.makedirs(OUTPUT_DIR, exist_ok=True)
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(OUTPUT_DIR, "pipeline.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)
 
# CAMEO codes that signal supply-chain stress
# Keep as strings — GDELT stores them as strings
SUPPLY_CHAIN_CODES = {
    "13",    # Threaten
    "130",   # Threaten (general)
    "131",   # Threaten with military force
    "132",   # Accuse of threat
    "14",    # Protest
    "140",   # Protest (general)
    "141",   # Demonstrate or rally
    "145",   # Protest violently / riot
    "17",    # Coerce
    "170",   # Coerce (general)
    "172",   # Impose administrative sanctions
    "173",   # Impose embargo / boycott
    "174",   # Halt negotiations
    "175",   # Break relations
    "20",    # Assault
    "200",   # Assault (general)
    "201",   # Engage in mass expulsion
    "202",   # Engage in mass killings
    "203",   # Engage in ethnic cleansing
    "204",   # Attempt to assassinate
    "1211",  # Impose economic sanctions
    "1221",  # Impose embargo
    "1222",  # Impose boycott
    "1223",  # Threaten embargo
}
 
# GDELT 2.0 column 28 (0-indexed) = EventCode
# But let's also map key column indices for filtering/output
GDELT_COLS = {
    0:  "GlobalEventID",
    1:  "Day",           # YYYYMMDD
    2:  "MonthYear",
    3:  "Year",
    5:  "Actor1Code",
    6:  "Actor1Name",
    10: "Actor2Code",
    11: "Actor2Name",
    15: "IsRootEvent",
    26: "EventCode",     # ← this is what we filter on
    27: "EventBaseCode",
    28: "EventRootCode",
    29: "QuadClass",
    30: "GoldsteinScale",
    31: "NumMentions",
    32: "NumSources",
    33: "NumArticles",
    34: "AvgTone",
    37: "Actor1Geo_CountryCode",
    44: "Actor2Geo_CountryCode",
    51: "ActionGeo_CountryCode",
    52: "ActionGeo_Lat",
    53: "ActionGeo_Long",
    57: "SOURCEURL",
}
 
# ── Targeted month windows ─────────────────────────────────────────────────────
# Instead of all 2019-2024, we sample months around known disruptions
# PLUS one "quiet" baseline month per year for contrast.
# Expand EXTRA_MONTHS to add more coverage.
 
CRISIS_MONTHS = [
    # Baseline months (one per year)
    ("2019-03", "Baseline 2019"),
    ("2019-09", "Baseline 2019 Q3"),
 
    # COVID factory shutdowns
    ("2020-01", "COVID onset"),
    ("2020-02", "COVID factory shutdowns"),
    ("2020-03", "COVID global spread"),
    ("2020-04", "COVID peak lockdowns"),
 
    # Suez Canal blockage
    ("2021-03", "Suez Canal blockage"),
    ("2021-04", "Suez aftermath"),
 
    # Taiwan semiconductor drought
    ("2021-05", "Taiwan semiconductor drought"),
    ("2021-06", "Semiconductor shortage peak"),
 
    # Russia-Ukraine sanctions
    ("2022-02", "Russia-Ukraine invasion + sanctions"),
    ("2022-03", "Ukraine sanctions wave"),
    ("2022-04", "Shanghai lockdown begins"),
 
    # Shanghai lockdown
    ("2022-04", "Shanghai lockdown"),
    ("2022-05", "Shanghai lockdown peak"),
 
    # Baseline 2022
    ("2022-09", "Baseline 2022 Q3"),
 
    # Baseline 2023
    ("2023-06", "Baseline 2023"),
 
    # Red Sea / Houthi shipping crisis
    ("2023-12", "Red Sea crisis onset"),
    ("2024-01", "Red Sea crisis peak"),
    ("2024-02", "Red Sea rerouting impact"),
 
    # Baseline 2024
    ("2024-06", "Baseline 2024"),
]
 
# De-duplicate months (some appear twice due to overlapping events)
seen = set()
UNIQUE_MONTHS = []
for ym, label in CRISIS_MONTHS:
    if ym not in seen:
        seen.add(ym)
        UNIQUE_MONTHS.append((ym, label))
 
 
# ── Core download helpers ─────────────────────────────────────────────────────
 
def build_urls_for_month(year_month: str, files_per_day: int = 2) -> list[str]:
    """
    Generate GDELT file URLs for a YYYY-MM month.
    We pick `files_per_day` evenly-spaced 15-min slots per day (e.g. 09:00 and 21:00).
    GDELT files are named: YYYYMMDDHHMMSS.export.CSV.zip
    Valid minutes: 00, 15, 30, 45  Valid hours: 00-23
    """
    year, month = int(year_month[:4]), int(year_month[5:7])
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
 
    # Evenly spaced hour slots across the day
    if files_per_day == 1:
        hours = [12]
    elif files_per_day == 2:
        hours = [9, 21]
    elif files_per_day == 4:
        hours = [0, 6, 12, 18]
    else:
        hours = list(range(0, 24, max(1, 24 // files_per_day)))[:files_per_day]
 
    urls = []
    current = start
    while current < end:
        for h in hours:
            dt = current.replace(hour=h, minute=0, second=0)
            ts = dt.strftime("%Y%m%d%H%M%S")
            url = f"http://data.gdeltproject.org/gdeltv2/{ts}.export.CSV.zip"
            urls.append(url)
        current += timedelta(days=1)
    return urls
 
 
def download_and_filter(url: str, retries: int = 3) -> pd.DataFrame | None:
    """
    Download one GDELT zip, parse the TSV, filter by supply-chain CAMEO codes.
    Returns a filtered DataFrame or None on failure.
    """
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 404:
                return None  # File doesn't exist (gap in GDELT history)
            r.raise_for_status()
 
            filename = url.split("/")[-1].replace(".zip", "")
            zf = zipfile.ZipFile(io.BytesIO(r.content))
            with zf.open(filename) as f:
                df = pd.read_csv(f, sep="\t", header=None, dtype=str, low_memory=False)
 
            # Column 26 = EventCode in GDELT 2.0 export files
            event_col = 26
            filtered = df[df[event_col].isin(SUPPLY_CHAIN_CODES)].copy()
 
            if filtered.empty:
                return filtered  # Empty but valid
 
            # Rename only columns we care about
            rename = {k: v for k, v in GDELT_COLS.items() if k < len(filtered.columns)}
            filtered = filtered.rename(columns=rename)
 
            # Keep only named columns + drop the rest
            keep = list(rename.values())
            existing_keep = [c for c in keep if c in filtered.columns]
            return filtered[existing_keep]
 
        except Exception as e:
            log.warning(f"Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
 
    log.error(f"All retries exhausted for {url}")
    return None
 
 
# ── Main pipeline ─────────────────────────────────────────────────────────────
 
def run_pipeline(files_per_day: int = 2):
    """
    Main loop: for each target month, download files, filter, and save.
    """
    all_frames = []
    total_rows = 0
 
    for year_month, label in UNIQUE_MONTHS:
        log.info(f"\n{'='*60}")
        log.info(f"Processing {year_month} — {label}")
        urls = build_urls_for_month(year_month, files_per_day=files_per_day)
        log.info(f"  {len(urls)} files to download")
 
        month_frames = []
        for url in tqdm(urls, desc=year_month, unit="file"):
            df = download_and_filter(url)
            if df is not None and not df.empty:
                df["SourceMonth"] = year_month
                df["SourceLabel"] = label
                month_frames.append(df)
            time.sleep(0.3)  # Be polite to GDELT servers
 
        if month_frames:
            month_df = pd.concat(month_frames, ignore_index=True)
            out_path = os.path.join(OUTPUT_DIR, f"gdelt_{year_month}.csv")
            month_df.to_csv(out_path, index=False)
            rows = len(month_df)
            total_rows += rows
            log.info(f"  ✓ Saved {rows:,} rows → {out_path}")
            all_frames.append(month_df)
        else:
            log.info(f"  ⚠ No supply-chain events found for {year_month}")
 
    # Combine everything
    if all_frames:
        combined = pd.concat(all_frames, ignore_index=True)
        combined_path = os.path.join(OUTPUT_DIR, "gdelt_all_supply_chain.csv")
        combined.to_csv(combined_path, index=False)
        log.info(f"\n{'='*60}")
        log.info(f"DONE. Total rows: {total_rows:,}")
        log.info(f"Combined CSV saved → {combined_path}")
    else:
        log.warning("No data collected.")
 
 
if __name__ == "__main__":
    # files_per_day=2 → ~60 files/month → ~20 min per month on decent internet
    # files_per_day=4 → ~120 files/month → more coverage, 2x slower
    run_pipeline(files_per_day=2)