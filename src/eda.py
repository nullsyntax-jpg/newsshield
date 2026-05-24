"""
Task 2 — Exploratory Data Analysis
====================================
Generates 4 publication-ready figures:
  1. Monthly GDELT event volume with disruption overlays
  2. GSCPI index with disruption overlays
  3. Heatmap of event volume by country and month
  4. CAMEO event code distribution

Run: python src/eda.py
Output: gdelt_output/figures/
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")

# ── Output folder ─────────────────────────────────────────────────────────────
FIGURES_DIR = "gdelt_output/figures"
os.makedirs(FIGURES_DIR, exist_ok=True)

# ── Plot style ────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 150,
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
})

# ── Known disruption events ───────────────────────────────────────────────────
DISRUPTIONS = [
    ("2019-05-10", "US-China\nTariffs",        "above"),
    ("2020-01-23", "COVID\nWuhan",              "below"),
    ("2020-03-15", "COVID\nGlobal\nLockdown",   "above"),
    ("2021-03-23", "Suez Canal\nBlockage",      "below"),
    ("2021-05-01", "Taiwan\nChip Drought",      "above"),
    ("2022-02-24", "Russia-Ukraine\nInvasion",  "below"),
    ("2022-04-01", "Shanghai\nLockdown",        "above"),
    ("2023-08-01", "Panama\nDrought",           "below"),
    ("2023-12-08", "Red Sea\nCrisis",           "above"),
    ("2024-03-26", "Baltimore\nBridge",         "below"),
]

# Colors alternating for readability
DISRUPT_COLORS = ["#e63946", "#457b9d"]

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading data...")

gdelt = pd.read_csv("data/raw/gdelt_all_supply_chain.csv", low_memory=False)
gscpi = pd.read_csv("gdelt_output/gscpi_clean.csv")

print(f"  GDELT rows: {len(gdelt):,}")
print(f"  GSCPI rows: {len(gscpi)}")
print(f"  GDELT columns: {list(gdelt.columns)}")

# ── Parse dates ───────────────────────────────────────────────────────────────
# GDELT Day column is YYYYMMDD integer
gdelt["date"] = pd.to_datetime(gdelt["Day"].astype(str), format="%Y%m%d", errors="coerce")
gdelt["year_month"] = gdelt["date"].dt.to_period("M").astype(str)
gdelt = gdelt.dropna(subset=["date"])

gscpi["date"] = pd.to_datetime(gscpi["date"], errors="coerce")
gscpi = gscpi.dropna(subset=["date"])

print(f"  GDELT date range: {gdelt['date'].min().date()} → {gdelt['date'].max().date()}")
print(f"  GSCPI date range: {gscpi['date'].min().date()} → {gscpi['date'].max().date()}")

# ── Helper: draw disruption vertical lines ────────────────────────────────────
def draw_disruptions(ax, y_min, y_max, disruptions=DISRUPTIONS):
    y_range = y_max - y_min
    for i, (date_str, label, position) in enumerate(disruptions):
        dt = pd.to_datetime(date_str)
        color = DISRUPT_COLORS[i % 2]
        ax.axvline(dt, color=color, linewidth=1.2, linestyle="--", alpha=0.8, zorder=3)
        if position == "above":
            y_pos = y_max - y_range * 0.03
            va = "top"
        else:
            y_pos = y_min + y_range * 0.03
            va = "bottom"
        ax.text(
            dt, y_pos, label,
            fontsize=6.5, color=color, va=va, ha="center",
            rotation=90, alpha=0.9,
            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.6)
        )


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — Monthly GDELT Event Volume
# ══════════════════════════════════════════════════════════════════════════════
print("\nPlotting Figure 1: Monthly GDELT event volume...")

monthly = gdelt.groupby("year_month").size().reset_index(name="event_count")
monthly["date"] = pd.to_datetime(monthly["year_month"])
monthly = monthly.sort_values("date")

# Rolling 3-month average
monthly["rolling_avg"] = monthly["event_count"].rolling(3, center=True).mean()

fig, ax = plt.subplots(figsize=(14, 5))

ax.bar(monthly["date"], monthly["event_count"],
       width=25, color="#a8dadc", alpha=0.7, label="Monthly event count", zorder=2)
ax.plot(monthly["date"], monthly["rolling_avg"],
        color="#1d3557", linewidth=2, label="3-month rolling avg", zorder=4)

y_min, y_max = 0, monthly["event_count"].max() * 1.25
ax.set_ylim(y_min, y_max)
draw_disruptions(ax, y_min, y_max)

ax.set_title("GDELT Supply-Chain Event Volume (2019–2024)\nFiltered by CAMEO codes: 13, 14, 17, 20 + economic disruption codes")
ax.set_xlabel("Month")
ax.set_ylabel("Number of Events")
ax.legend(loc="upper left", fontsize=9)
ax.set_xlim(pd.Timestamp("2019-01-01"), pd.Timestamp("2024-12-31"))

# Shade COVID period
ax.axvspan(pd.Timestamp("2020-03-01"), pd.Timestamp("2020-06-30"),
           alpha=0.08, color="red", label="COVID peak")
ax.axvspan(pd.Timestamp("2022-02-24"), pd.Timestamp("2022-06-30"),
           alpha=0.08, color="orange", label="Ukraine war")

plt.tight_layout()
out1 = os.path.join(FIGURES_DIR, "fig1_gdelt_monthly_volume.png")
plt.savefig(out1, bbox_inches="tight")
plt.close()
print(f"  Saved → {out1}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — GSCPI Index with Disruption Overlays
# ══════════════════════════════════════════════════════════════════════════════
print("Plotting Figure 2: GSCPI index...")

fig, ax = plt.subplots(figsize=(14, 5))

# Fill above/below zero
ax.fill_between(gscpi["date"], gscpi["gscpi"], 0,
                where=gscpi["gscpi"] >= 0,
                color="#e63946", alpha=0.25, label="Above normal pressure")
ax.fill_between(gscpi["date"], gscpi["gscpi"], 0,
                where=gscpi["gscpi"] < 0,
                color="#2a9d8f", alpha=0.25, label="Below normal pressure")

ax.plot(gscpi["date"], gscpi["gscpi"],
        color="#1d3557", linewidth=2, zorder=4)
ax.axhline(0, color="black", linewidth=0.8, linestyle="-", alpha=0.5)
ax.axhline(1.5, color="#e63946", linewidth=0.8, linestyle=":",
           alpha=0.6, label="High-pressure threshold (z=1.5)")
ax.axhline(-1.5, color="#2a9d8f", linewidth=0.8, linestyle=":",
           alpha=0.6, label="Low-pressure threshold (z=-1.5)")

y_min = gscpi["gscpi"].min() - 0.5
y_max = gscpi["gscpi"].max() + 0.8
ax.set_ylim(y_min, y_max)
draw_disruptions(ax, y_min, y_max)

ax.set_title("NY Fed Global Supply Chain Pressure Index (GSCPI) 2019–2024\nStandardized index: 0 = historical average, positive = above-average pressure")
ax.set_xlabel("Month")
ax.set_ylabel("GSCPI (standard deviations)")
ax.legend(loc="upper right", fontsize=9)
ax.set_xlim(pd.Timestamp("2019-01-01"), pd.Timestamp("2024-12-31"))

plt.tight_layout()
out2 = os.path.join(FIGURES_DIR, "fig2_gscpi_index.png")
plt.savefig(out2, bbox_inches="tight")
plt.close()
print(f"  Saved → {out2}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — Heatmap: Event Volume by Country and Month
# ══════════════════════════════════════════════════════════════════════════════
print("Plotting Figure 3: Country × Month heatmap...")

# Use ActionGeo_CountryCode column
country_col = None
for c in ["ActionGeo_CountryCode", "Actor1Code", "Actor2Code"]:
    if c in gdelt.columns:
        country_col = c
        break

if country_col:
    # Top 15 countries by total event count
    top_countries = (gdelt[country_col]
                     .dropna()
                     .value_counts()
                     .head(15)
                     .index.tolist())

    heat_df = gdelt[gdelt[country_col].isin(top_countries)].copy()
    heat_df["month_label"] = heat_df["date"].dt.strftime("%Y-%m")

    pivot = (heat_df.groupby([country_col, "month_label"])
             .size()
             .unstack(fill_value=0))

    # Sort columns (months) chronologically
    pivot = pivot.reindex(sorted(pivot.columns), axis=1)

    # Keep only months we have data for
    pivot = pivot.loc[:, pivot.sum() > 0]

    # Thin out x-axis: show every 3rd month label
    all_months = list(pivot.columns)
    xtick_labels = [m if i % 3 == 0 else "" for i, m in enumerate(all_months)]

    fig, ax = plt.subplots(figsize=(16, 6))
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd", interpolation="nearest")

    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=9)
    ax.set_xticks(range(len(all_months)))
    ax.set_xticklabels(xtick_labels, rotation=90, fontsize=7)

    plt.colorbar(im, ax=ax, label="Event count", shrink=0.8)

    # Draw disruption lines on heatmap
    for i, (date_str, label, _) in enumerate(DISRUPTIONS):
        dt_label = pd.to_datetime(date_str).strftime("%Y-%m")
        if dt_label in all_months:
            x_pos = all_months.index(dt_label)
            ax.axvline(x_pos, color=DISRUPT_COLORS[i % 2],
                       linewidth=1.5, linestyle="--", alpha=0.8)

    ax.set_title("Supply-Chain Event Volume Heatmap by Country and Month (2019–2024)\nDashed lines = known disruption events")
    ax.set_xlabel("Month")
    ax.set_ylabel("Country Code")

    plt.tight_layout()
    out3 = os.path.join(FIGURES_DIR, "fig3_country_month_heatmap.png")
    plt.savefig(out3, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {out3}")
else:
    print("  ⚠ No country column found — skipping heatmap")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — CAMEO Event Code Distribution
# ══════════════════════════════════════════════════════════════════════════════
print("Plotting Figure 4: CAMEO event code distribution...")

CAMEO_LABELS = {
    "13": "13 Threaten", "130": "130 Threaten (gen)",
    "131": "131 Military threat", "14": "14 Protest",
    "140": "140 Protest (gen)", "141": "141 Demonstrate",
    "145": "145 Violent protest", "17": "17 Coerce",
    "170": "170 Coerce (gen)", "172": "172 Admin sanctions",
    "173": "173 Embargo/boycott", "174": "174 Halt negot.",
    "20": "20 Assault", "200": "200 Assault (gen)",
    "1211": "1211 Econ sanctions", "1221": "1221 Embargo",
    "1222": "1222 Boycott",
}

code_counts = (gdelt["EventCode"]
               .astype(str)
               .value_counts()
               .reset_index())
code_counts.columns = ["code", "count"]
code_counts["label"] = code_counts["code"].map(CAMEO_LABELS).fillna(code_counts["code"])
code_counts = code_counts.sort_values("count", ascending=True).tail(20)

fig, ax = plt.subplots(figsize=(10, 7))
bars = ax.barh(code_counts["label"], code_counts["count"],
               color="#457b9d", alpha=0.85, edgecolor="white")

# Add value labels
for bar, val in zip(bars, code_counts["count"]):
    ax.text(bar.get_width() + code_counts["count"].max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{val:,}", va="center", fontsize=8)

ax.set_title("Distribution of CAMEO Event Codes in GDELT Supply-Chain Dataset\n(Filtered events 2019–2024)")
ax.set_xlabel("Number of Events")
ax.set_ylabel("CAMEO Code")
ax.set_xlim(0, code_counts["count"].max() * 1.15)

plt.tight_layout()
out4 = os.path.join(FIGURES_DIR, "fig4_cameo_distribution.png")
plt.savefig(out4, bbox_inches="tight")
plt.close()
print(f"  Saved → {out4}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 5 — GDELT vs GSCPI Correlation
# ══════════════════════════════════════════════════════════════════════════════
print("Plotting Figure 5: GDELT volume vs GSCPI correlation...")

# Merge monthly GDELT counts with GSCPI
monthly_merge = monthly[["year_month", "event_count"]].copy()
gscpi["year_month"] = gscpi["date"].dt.strftime("%Y-%m")
merged = monthly_merge.merge(gscpi[["year_month", "gscpi"]], on="year_month", how="inner")

fig, ax = plt.subplots(figsize=(7, 6))
sc = ax.scatter(merged["event_count"], merged["gscpi"],
                c=pd.to_datetime(merged["year_month"]).astype(np.int64),
                cmap="viridis", alpha=0.8, s=60, edgecolors="white", linewidth=0.5)

# Trend line
z = np.polyfit(merged["event_count"], merged["gscpi"], 1)
p = np.poly1d(z)
x_line = np.linspace(merged["event_count"].min(), merged["event_count"].max(), 100)
ax.plot(x_line, p(x_line), color="#e63946", linewidth=1.5,
        linestyle="--", label=f"Trend (slope={z[0]:.4f})")

corr = merged["event_count"].corr(merged["gscpi"])
ax.set_title(f"GDELT Monthly Event Volume vs GSCPI\nPearson r = {corr:.3f}")
ax.set_xlabel("Monthly GDELT Supply-Chain Event Count")
ax.set_ylabel("GSCPI (standard deviations)")
ax.legend(fontsize=9)

plt.colorbar(sc, ax=ax, label="Time (earlier → later)")
plt.tight_layout()
out5 = os.path.join(FIGURES_DIR, "fig5_gdelt_vs_gscpi.png")
plt.savefig(out5, bbox_inches="tight")
plt.close()
print(f"  Saved → {out5}")


# ══════════════════════════════════════════════════════════════════════════════
# PRINT SUMMARY FINDINGS
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("EDA SUMMARY — Share these findings with Member B")
print("="*60)
print(f"\nTotal supply-chain events (2019-2024): {len(gdelt):,}")
print(f"Months covered: {gdelt['year_month'].nunique()}")
print(f"\nTop 5 months by event volume:")
print(monthly.nlargest(5, "event_count")[["year_month","event_count"]].to_string(index=False))
print(f"\nGSCPI peak month: {gscpi.loc[gscpi['gscpi'].idxmax(), 'year_month']} "
      f"(value={gscpi['gscpi'].max():.2f})")
print(f"GSCPI trough month: {gscpi.loc[gscpi['gscpi'].idxmin(), 'year_month']} "
      f"(value={gscpi['gscpi'].min():.2f})")
print(f"\nGDELT vs GSCPI correlation: r = {corr:.3f}")
if corr > 0.5:
    print("  → STRONG positive correlation — hypothesis supported!")
elif corr > 0.3:
    print("  → MODERATE correlation — hypothesis partially supported")
else:
    print("  → WEAK correlation — may need feature engineering")
print(f"\nAll figures saved to: {FIGURES_DIR}/")
print("  fig1_gdelt_monthly_volume.png")
print("  fig2_gscpi_index.png")
print("  fig3_country_month_heatmap.png")
print("  fig4_cameo_distribution.png")
print("  fig5_gdelt_vs_gscpi.png")