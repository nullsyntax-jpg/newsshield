"""
GSCPI Downloader — NY Federal Reserve
======================================
Downloads the Global Supply Chain Pressure Index (GSCPI) directly
from the NY Fed's public Excel file. No account needed.
 
Run: pip install requests openpyxl pandas
Then: python gscpi_download.py
"""
 
import requests
import pandas as pd
import os
 
OUTPUT_DIR = "gdelt_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
 
# NY Fed GSCPI direct download URL (updated periodically)
# If this URL breaks, go to: https://www.newyorkfed.org/research/policy/gscpi
GSCPI_URL = "https://www.newyorkfed.org/medialibrary/media/research/policy/gscpi/downloads/gscpi-data.xlsx"
 
def download_gscpi():
    print("Downloading GSCPI from NY Federal Reserve...")
    headers = {
        "User-Agent": "Mozilla/5.0 (research pipeline)"
    }
    r = requests.get(GSCPI_URL, headers=headers, timeout=60)
    r.raise_for_status()
 
    raw_path = os.path.join(OUTPUT_DIR, "gscpi_raw.xlsx")
    with open(raw_path, "wb") as f:
        f.write(r.content)
    print(f"✓ Downloaded raw Excel → {raw_path}")
 
    # Parse — NY Fed sheet is usually "GSCPI" or first sheet
    try:
       df = pd.read_excel(raw_path, sheet_name=0, header=0, engine="xlrd")
    except Exception:
       df = pd.read_excel(raw_path, header=0, engine="xlrd")
 
    print(f"  Raw shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
 
    # NY Fed GSCPI has columns like: Date, GSCPI
    # Normalize column names
    df.columns = [str(c).strip() for c in df.columns]
 
    # Try to find the date column
    date_col = None
    for c in df.columns:
        if "date" in c.lower() or "month" in c.lower() or "year" in c.lower() or "period" in c.lower():
            date_col = c
            break
    if date_col is None:
        date_col = df.columns[0]  # fallback: assume first column is date
 
    # Find GSCPI value column
    val_col = None
    for c in df.columns:
        if "gscpi" in c.lower() or "index" in c.lower() or "value" in c.lower():
            val_col = c
            break
    if val_col is None:
        val_col = df.columns[1]  # fallback: assume second column
 
    df_clean = df[[date_col, val_col]].copy()
    df_clean.columns = ["date", "gscpi"]
    df_clean["date"] = pd.to_datetime(df_clean["date"], errors="coerce")
    df_clean = df_clean.dropna(subset=["date", "gscpi"])
    df_clean = df_clean.sort_values("date").reset_index(drop=True)
    df_clean["year"] = df_clean["date"].dt.year
    df_clean["month"] = df_clean["date"].dt.month
    df_clean["year_month"] = df_clean["date"].dt.strftime("%Y-%m")
 
    # Add signal column: flag months above 1.5 standard deviations as disruption
    mean_gscpi = df_clean["gscpi"].mean()
    std_gscpi = df_clean["gscpi"].std()
    df_clean["z_score"] = (df_clean["gscpi"] - mean_gscpi) / std_gscpi
    df_clean["high_pressure"] = df_clean["z_score"] > 1.5
 
    # Save
    out_path = os.path.join(OUTPUT_DIR, "gscpi_clean.csv")
    df_clean.to_csv(out_path, index=False)
    print(f"✓ Cleaned GSCPI saved → {out_path}")
    print(f"  Date range: {df_clean['date'].min().date()} → {df_clean['date'].max().date()}")
    print(f"  Rows: {len(df_clean)}")
    print(f"\n── High-pressure months (z > 1.5) ──")
    print(df_clean[df_clean["high_pressure"]][["year_month","gscpi","z_score"]].to_string(index=False))
 
    return df_clean
 
 
if __name__ == "__main__":
    df = download_gscpi()
    print("\nDone. Use gscpi_clean.csv to align with GDELT event counts.")