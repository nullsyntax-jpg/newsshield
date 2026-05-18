import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime

# ── 1. Load GSCPI data ────────────────────────────────────────────────────────
print("Loading GSCPI data...")
gscpi_raw = pd.read_excel(
    'gscpi_data.xls',
    sheet_name='GSCPI Monthly Data',
    header=None,
    skiprows=5  # skip the header rows
)

# Keep only Date and GSCPI columns
gscpi = gscpi_raw[[0, 1]].copy()
gscpi.columns = ['date', 'gscpi']
gscpi = gscpi.dropna(subset=['date', 'gscpi'])
gscpi['date'] = pd.to_datetime(gscpi['date'])
gscpi = gscpi.sort_values('date').reset_index(drop=True)

print(f"GSCPI data loaded: {len(gscpi)} monthly records")
print(f"Date range: {gscpi['date'].min().strftime('%b %Y')} to {gscpi['date'].max().strftime('%b %Y')}")
print()

# ── 2. Load extracted signals from T3 ────────────────────────────────────────
print("Loading extracted signals from T3...")
with open('test_extraction.json', 'r') as f:
    signals = json.load(f)

# Filter successful extractions only
signals = [s for s in signals if s.get('status') == 'success']
print(f"Loaded {len(signals)} successful signal extractions")
print()

# ── 3. Show GSCPI around key disruption events ───────────────────────────────
# These are the 3 case study events from your roadmap
disruption_events = {
    'COVID-19 Factory Shutdowns': '2020-03-01',
    'Suez Canal Blockage':        '2021-03-23',
    'Red Sea Shipping Crisis':    '2023-11-01',
}

print("=" * 60)
print("GSCPI VALUES AROUND KEY DISRUPTION EVENTS")
print("=" * 60)

for event_name, event_date in disruption_events.items():
    event_dt = pd.to_datetime(event_date)

    # Get GSCPI 3 months before and 3 months after the event
    mask = (gscpi['date'] >= event_dt - pd.DateOffset(months=3)) & \
           (gscpi['date'] <= event_dt + pd.DateOffset(months=3))
    window = gscpi[mask].copy()

    print(f"\n{event_name} (Event date: {event_dt.strftime('%b %Y')})")
    print("-" * 40)
    for _, row in window.iterrows():
        marker = " ← EVENT MONTH" if abs((row['date'] - event_dt).days) < 35 else ""
        print(f"  {row['date'].strftime('%b %Y')}: GSCPI = {row['gscpi']:+.3f}{marker}")

# ── 4. Plot GSCPI timeline with disruption markers ───────────────────────────
print("\nGenerating GSCPI timeline plot...")

fig, ax = plt.subplots(figsize=(14, 6))

# Filter to 2019-2024 for the paper
mask = (gscpi['date'] >= '2019-01-01') & (gscpi['date'] <= '2024-12-31')
gscpi_plot = gscpi[mask]

ax.plot(gscpi_plot['date'], gscpi_plot['gscpi'],
        color='#2563EB', linewidth=2, label='GSCPI Index')
ax.fill_between(gscpi_plot['date'], gscpi_plot['gscpi'], 0,
                where=gscpi_plot['gscpi'] > 0,
                alpha=0.15, color='#DC2626', label='Positive pressure (disruption)')
ax.fill_between(gscpi_plot['date'], gscpi_plot['gscpi'], 0,
                where=gscpi_plot['gscpi'] < 0,
                alpha=0.15, color='#16A34A', label='Negative pressure (recovery)')

# Mark disruption events
colors = ['#DC2626', '#D97706', '#7C3AED']
for i, (event_name, event_date) in enumerate(disruption_events.items()):
    ax.axvline(pd.to_datetime(event_date), color=colors[i],
               linestyle='--', linewidth=1.5, alpha=0.8)
    ax.text(pd.to_datetime(event_date), ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 3,
            event_name.replace(' ', '\n'), fontsize=7.5,
            color=colors[i], ha='left', va='top',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

ax.axhline(0, color='black', linewidth=0.8, linestyle='-', alpha=0.4)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('GSCPI Value (standard deviations)', fontsize=12)
ax.set_title('Global Supply Chain Pressure Index (GSCPI) 2019–2024\nwith Key Disruption Events Marked',
             fontsize=13, fontweight='bold')
ax.legend(loc='upper left', fontsize=9)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('gscpi_timeline.png', dpi=150, bbox_inches='tight')
plt.show()
print("Plot saved as: gscpi_timeline.png")

# ── 5. Signal summary from T3 extraction ─────────────────────────────────────
print("\n" + "=" * 60)
print("SIGNAL EXTRACTION SUMMARY (from T3)")
print("=" * 60)

signal_types   = [s.get('signal_type') for s in signals]
industries     = [s.get('affected_industry') for s in signals]
severities     = [s.get('severity_score') for s in signals]
categories     = [s.get('disruption_category') for s in signals]

print(f"\nSignal type distribution:")
for st in set(signal_types):
    print(f"  {st}: {signal_types.count(st)}")

print(f"\nAffected industries:")
for ind in set(industries):
    print(f"  {ind}: {industries.count(ind)}")

print(f"\nAverage severity score: {np.mean(severities):.2f} / 5.0")
print(f"Max severity score:     {max(severities)}")

print("\nNote: Full lead time analysis will run after GDELT batch")
print("      processing produces weekly aggregated risk scores.")
print("\nT4 setup complete! GSCPI data is clean and ready.")
