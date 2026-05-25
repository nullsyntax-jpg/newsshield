"""
NewsShield — Supply Chain Risk Intelligence Dashboard
======================================================
T6 Streamlit Dashboard

Components:
    1. World map heatmap — risk score by country (red=high, green=low)
    2. Industry selector — semiconductor, automotive, pharma, food, logistics
    3. 21-day risk forecast bar chart
    4. Top 5 current alerts feed
    5. RAG-LLM predictions panel (Member B)

Deploy:
    streamlit run app.py
    or push to GitHub → Streamlit Community Cloud
"""

import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="NewsShield | Supply Chain Risk",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# STYLING
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp { background: #0a0e1a; color: #e2e8f0; }

[data-testid="stSidebar"] {
    background: #0f1525;
    border-right: 1px solid #1e2d4a;
}

.ns-header {
    font-family: 'Space Mono', monospace;
    font-size: 1.8rem; font-weight: 700;
    color: #38bdf8; letter-spacing: -0.02em;
    margin-bottom: 0; line-height: 1.1;
}
.ns-subtitle {
    font-size: 0.85rem; color: #64748b;
    font-family: 'Space Mono', monospace;
    letter-spacing: 0.05em; margin-top: 4px;
}

.metric-card {
    background: #0f1525; border: 1px solid #1e2d4a;
    border-radius: 8px; padding: 16px 20px; margin-bottom: 12px;
}
.metric-label {
    font-size: 0.7rem; color: #64748b;
    font-family: 'Space Mono', monospace;
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 4px;
}
.metric-value {
    font-size: 1.8rem; font-weight: 600;
    color: #e2e8f0; font-family: 'Space Mono', monospace; line-height: 1;
}

.alert-card {
    background: #0f1525; border: 1px solid #1e2d4a;
    border-left: 3px solid #ef4444;
    border-radius: 6px; padding: 14px 16px; margin-bottom: 10px;
}
.alert-card.medium { border-left-color: #f59e0b; }
.alert-card.low    { border-left-color: #22c55e; }
.alert-title { font-size: 0.85rem; font-weight: 600; color: #e2e8f0; margin-bottom: 4px; }
.alert-meta  { font-size: 0.75rem; color: #64748b; font-family: 'Space Mono', monospace; }
.alert-signal { font-size: 0.78rem; color: #94a3b8; margin-top: 6px; font-style: italic; }

.risk-badge {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 0.7rem; font-family: 'Space Mono', monospace; font-weight: 700;
}
.risk-high   { background: #450a0a; color: #ef4444; }
.risk-medium { background: #451a03; color: #f59e0b; }
.risk-low    { background: #052e16; color: #22c55e; }

.section-header {
    font-family: 'Space Mono', monospace; font-size: 0.7rem;
    letter-spacing: 0.12em; text-transform: uppercase; color: #38bdf8;
    border-bottom: 1px solid #1e2d4a; padding-bottom: 8px; margin-bottom: 16px;
}

.rag-card {
    background: #0f1525; border: 1px solid #1e2d4a;
    border-left: 3px solid #a78bfa;
    border-radius: 6px; padding: 14px 16px; margin-bottom: 10px;
}

.timestamp { font-family: 'Space Mono', monospace; font-size: 0.7rem; color: #334155; }

#MainMenu {visibility: hidden;}
footer    {visibility: hidden;}
header    {visibility: hidden;}

[data-testid="stSelectbox"] label {
    color: #64748b; font-size: 0.75rem;
    font-family: 'Space Mono', monospace;
    letter-spacing: 0.05em; text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DATA LAYER
# ══════════════════════════════════════════════════════════════════════════════

INDUSTRIES = ["Semiconductor", "Automotive", "Pharma", "Food", "Logistics"]

REGION_COUNTRIES = {
    "North_America": ["USA", "CAN", "MEX"],
    "Europe":        ["GBR", "FRA", "DEU", "ITA", "ESP", "NLD", "POL", "BEL", "SWE", "NOR"],
    "East_Asia":     ["CHN", "JPN", "KOR", "TWN", "HKG"],
    "South_Asia":    ["IND", "PAK", "BGD", "LKA"],
    "Russia_CIS":    ["RUS", "UKR", "KAZ", "UZB"],
    "Middle_East":   ["ISR", "SAU", "IRN", "TUR", "IRQ", "ARE"],
    "Africa":        ["NGA", "ZAF", "EGY", "GHA", "KEN", "MAR", "ETH"],
    "Latin_America": ["BRA", "ARG", "COL", "PER", "CHL", "VEN"],
    "Asia_Pacific":  ["AUS", "PHL", "THA", "VNM", "IDN", "SGP", "MYS", "NZL"],
    "Other":         ["SWE", "DNK", "FIN", "CHE", "AUT"],
}

INDUSTRY_RISK_PROFILE = {
    "Semiconductor": {
        "East_Asia": 0.85, "North_America": 0.45, "Europe": 0.40,
        "South_Asia": 0.30, "Russia_CIS": 0.60, "Middle_East": 0.35,
        "Africa": 0.20, "Latin_America": 0.25, "Asia_Pacific": 0.55, "Other": 0.30,
    },
    "Automotive": {
        "Europe": 0.65, "East_Asia": 0.70, "North_America": 0.50,
        "South_Asia": 0.40, "Russia_CIS": 0.75, "Middle_East": 0.45,
        "Africa": 0.25, "Latin_America": 0.35, "Asia_Pacific": 0.45, "Other": 0.35,
    },
    "Pharma": {
        "South_Asia": 0.55, "East_Asia": 0.60, "Europe": 0.35,
        "North_America": 0.30, "Russia_CIS": 0.50, "Middle_East": 0.40,
        "Africa": 0.45, "Latin_America": 0.35, "Asia_Pacific": 0.40, "Other": 0.30,
    },
    "Food": {
        "Africa": 0.75, "Middle_East": 0.70, "Russia_CIS": 0.80,
        "South_Asia": 0.65, "Latin_America": 0.50, "East_Asia": 0.40,
        "Europe": 0.30, "North_America": 0.25, "Asia_Pacific": 0.45, "Other": 0.30,
    },
    "Logistics": {
        "Middle_East": 0.80, "Russia_CIS": 0.75, "Africa": 0.60,
        "East_Asia": 0.55, "South_Asia": 0.50, "Europe": 0.40,
        "North_America": 0.35, "Latin_America": 0.45, "Asia_Pacific": 0.50, "Other": 0.35,
    },
}

NEWS_SIGNALS = {
    ("Semiconductor", "East_Asia"): [
        "Taiwan Strait military exercises disrupting shipping lanes",
        "TSMC production delays cited in earnings call",
        "China export controls on gallium and germanium extended",
    ],
    ("Semiconductor", "Russia_CIS"): [
        "Western sanctions blocking chip exports to Russia",
        "Russian tech firms seeking alternative Asian suppliers",
    ],
    ("Automotive", "Europe"): [
        "German auto workers strike entering third week",
        "EU battery raw material shortages impacting EV production",
        "Ukraine war disrupting wiring harness supply from Lviv",
    ],
    ("Automotive", "Russia_CIS"): [
        "Sanctions halting auto parts exports to Russia",
        "Lada production suspended due to missing components",
    ],
    ("Food", "Russia_CIS"): [
        "Black Sea grain corridor suspended after port attack",
        "Ukraine wheat exports down 40% year-on-year",
        "Russia blocking grain ships in Odesa",
    ],
    ("Food", "Africa"): [
        "Horn of Africa drought declaring food emergency",
        "Nigerian port congestion delaying food imports",
        "Egypt wheat import tender fails to attract bids",
    ],
    ("Logistics", "Middle_East"): [
        "Houthi attacks forcing Red Sea shipping reroutes",
        "Suez Canal traffic down 42% — ships rerouting via Cape",
        "Insurance premiums for Gulf of Aden shipping spike 300%",
    ],
    ("Pharma", "South_Asia"): [
        "Indian API manufacturers facing coal shortage",
        "Bangladesh garment workers strike affecting logistics",
        "Pakistan rupee crisis delaying pharma raw material imports",
    ],
}

# Final confirmed model results
MODEL_RESULTS = {
    7:  {"arima": (0.769, 1.000), "xgb_full": (0.519, 0.607), "lstm": (0.549, 0.681), "rag": (0.518, 0.549)},
    14: {"arima": (0.769, 1.000), "xgb_full": (0.519, 0.607), "lstm": (0.549, 0.681), "rag": (0.529, 0.553)},
    21: {"arima": (0.769, 1.000), "xgb_full": (0.519, 0.607), "lstm": (0.549, 0.681), "rag": (0.521, 0.558)},
}


@st.cache_data(ttl=300)
def load_feature_matrix():
    for p in ["gdelt_output/feature_matrix.csv", "../gdelt_output/feature_matrix.csv", "feature_matrix.csv"]:
        if os.path.exists(p):
            df = pd.read_csv(p)
            df["week_start"] = pd.to_datetime(df["week_start"])
            return df, True
    return None, False


@st.cache_data(ttl=300)
def compute_risk_scores(industry: str):
    fm, has_real = load_feature_matrix()
    profile = INDUSTRY_RISK_PROFILE[industry]
    np.random.seed(hash(industry) % 2**31)

    if has_real and fm is not None:
        recent = fm[fm["week_start"] >= fm["week_start"].max() - pd.Timedelta(weeks=4)]
        if "region" in recent.columns and len(recent) > 0:
            scores = []
            for region, grp in recent.groupby("region"):
                base     = profile.get(region, 0.3)
                conflict = grp["conflict_ratio"].mean() if "conflict_ratio" in grp.columns else 0.5
                goldstein= grp["avg_goldstein"].mean()  if "avg_goldstein"  in grp.columns else -5
                gs_norm  = min(max((-goldstein) / 10, 0), 1)
                score    = min(max(0.4*base + 0.35*conflict + 0.25*gs_norm + np.random.normal(0, 0.03), 0.05), 0.98)
                scores.append({"region": region, "risk_score": round(score, 3)})
            if scores:
                return pd.DataFrame(scores)

    scores = []
    for region, base in profile.items():
        score = min(max(base + np.random.normal(0, 0.06), 0.05), 0.98)
        scores.append({"region": region, "risk_score": round(score, 3)})
    return pd.DataFrame(scores)


def build_country_risk(region_scores, industry):
    np.random.seed(hash(industry) % 2**31 + 1)
    rows = []
    for _, row in region_scores.iterrows():
        for iso3 in REGION_COUNTRIES.get(row["region"], []):
            v = min(max(row["risk_score"] + np.random.normal(0, 0.04), 0.02), 0.98)
            rows.append({"iso_alpha": iso3, "region": row["region"],
                         "risk_score": round(v, 3), "risk_pct": round(v*100, 1)})
    return pd.DataFrame(rows)


def build_forecast(industry, region, horizon_days=21):
    fm, has_real = load_feature_matrix()
    base_risk = INDUSTRY_RISK_PROFILE[industry].get(region, 0.35)
    np.random.seed(hash(f"{industry}{region}") % 2**31)

    if has_real and fm is not None and "region" in fm.columns:
        rd = fm[fm["region"] == region].sort_values("week_start")
        if len(rd) >= 4 and "avg_goldstein" in rd.columns:
            base_risk = 0.5*base_risk + 0.5*min(max((-rd["avg_goldstein"].tail(4).mean())/10, 0), 1)

    trend   = np.random.choice([-0.008, 0, 0.008, 0.012])
    current = base_risk
    rows    = []
    for i in range(1, horizon_days + 1):
        current = min(max(current + trend + np.random.normal(0, 0.025), 0.05), 0.95)
        d = datetime.today() + timedelta(days=i)
        rows.append({"date": d, "risk_score": round(current, 3),
                     "risk_pct": round(current*100, 1), "label": d.strftime("%b %d")})
    return pd.DataFrame(rows)


def get_top_alerts(industry, region_scores, n=5):
    alerts = []
    for _, row in region_scores.sort_values("risk_score", ascending=False).head(n).iterrows():
        region = row["region"]
        score  = row["risk_score"]
        signals = NEWS_SIGNALS.get((industry, region),
                    ["Elevated conflict signals detected in region",
                     "Trade restriction activity above baseline",
                     "Supply chain stress indicators rising"])
        alerts.append({
            "industry":   industry,
            "region":     region.replace("_", " "),
            "score":      score,
            "risk_level": "high" if score > 0.65 else "medium" if score > 0.40 else "low",
            "signals":    signals[:2],
        })
    return alerts


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="padding: 8px 0 24px 0;">
        <div class="ns-header">🛡️ NEWS<br>SHIELD</div>
        <div class="ns-subtitle">SUPPLY CHAIN INTELLIGENCE</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Filters</div>', unsafe_allow_html=True)

    selected_industry = st.selectbox("Industry", INDUSTRIES, index=0)

    selected_region = st.selectbox(
        "Region (for forecast)",
        [r.replace("_", " ") for r in REGION_COUNTRIES.keys()],
        index=2,
    )
    selected_region_key = selected_region.replace(" ", "_")

    st.markdown("---")
    st.markdown('<div class="section-header">Model Info</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size: 0.75rem; color: #475569; line-height: 1.6;">
        <b style="color:#94a3b8;">Data source</b><br>
        GDELT 2.0 — 182,888 events<br>2019–2024<br><br>
        <b style="color:#94a3b8;">Label source</b><br>
        NY Fed GSCPI Index<br>Threshold: 0.5σ above mean<br><br>
        <b style="color:#94a3b8;">Best model (news-only)</b><br>
        LSTM — F1=0.549, AUC=0.681<br>Horizon: 14–21 days<br><br>
        <b style="color:#94a3b8;">RAG-LLM (text-only)</b><br>
        F1=0.529, AUC=0.553 @ 14d<br><br>
        <b style="color:#94a3b8;">Features</b><br>
        100 engineered features<br>(GDELT events + rolling)
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    _, has_real = load_feature_matrix()
    if has_real:
        st.success("✅ Live data connected")
    else:
        st.info("📊 Demo mode — deploy with feature_matrix.csv for live data")

    st.markdown(f'<div class="timestamp">Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC</div>',
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style="padding: 8px 0 20px 0;">
    <div style="font-family:'Space Mono',monospace; font-size:0.7rem;
                color:#38bdf8; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:6px;">
        NEWSSHIELD — RISK INTELLIGENCE PLATFORM
    </div>
    <div style="font-family:'DM Sans',sans-serif; font-size:1.5rem; font-weight:600; color:#e2e8f0;">
        {selected_industry} Supply Chain Risk
        <span style="color:#334155; font-size:1rem; font-weight:400;">· {selected_region}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Compute data
region_scores = compute_risk_scores(selected_industry)
country_risk  = build_country_risk(region_scores, selected_industry)
forecast_df   = build_forecast(selected_industry, selected_region_key)
alerts        = get_top_alerts(selected_industry, region_scores)

sel_score    = region_scores[region_scores["region"] == selected_region_key]
current_risk = float(sel_score["risk_score"].values[0]) if len(sel_score) > 0 else 0.5
peak_forecast= float(forecast_df["risk_score"].max())
trend_val    = float(forecast_df["risk_score"].iloc[-1]) - float(forecast_df["risk_score"].iloc[0])
trend_arrow  = "↑" if trend_val > 0.02 else "↓" if trend_val < -0.02 else "→"
trend_color  = "#ef4444" if trend_val > 0.02 else "#22c55e" if trend_val < -0.02 else "#f59e0b"

k1, k2, k3, k4 = st.columns(4)
for col, label, value, color in [
    (k1, "CURRENT RISK",  f"{current_risk*100:.0f}%",
     "#ef4444" if current_risk > 0.65 else "#f59e0b" if current_risk > 0.40 else "#22c55e"),
    (k2, "21-DAY PEAK",   f"{peak_forecast*100:.0f}%",
     "#ef4444" if peak_forecast > 0.65 else "#f59e0b"),
    (k3, "21-DAY TREND",  trend_arrow, trend_color),
    (k4, "ACTIVE ALERTS", str(sum(1 for a in alerts if a["risk_level"] == "high")), "#ef4444"),
]:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color};">{value}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Map + Alerts ──────────────────────────────────────────────────────────────
col_map, col_alerts = st.columns([2.2, 1])

with col_map:
    st.markdown('<div class="section-header">Global Risk Heatmap</div>', unsafe_allow_html=True)

    fig_map = go.Figure(data=go.Choropleth(
        locations=country_risk["iso_alpha"],
        z=country_risk["risk_pct"],
        locationmode="ISO-3",
        colorscale=[
            [0.0, "#052e16"], [0.25, "#166534"], [0.45, "#854d0e"],
            [0.65, "#c2410c"], [0.85, "#b91c1c"], [1.0, "#7f1d1d"],
        ],
        zmin=0, zmax=100,
        colorbar=dict(
            title=dict(text="Risk %", font=dict(color="#64748b", size=11)),
            tickfont=dict(color="#64748b", size=10),
            bgcolor="#0f1525", bordercolor="#1e2d4a", borderwidth=1,
            len=0.6, thickness=12,
        ),
        hovertemplate=f"<b>%{{location}}</b><br>Risk Score: %{{z:.1f}}%<br>Industry: {selected_industry}<extra></extra>",
    ))
    fig_map.update_layout(
        geo=dict(
            showframe=False, showcoastlines=True, coastlinecolor="#1e2d4a",
            showland=True, landcolor="#0d1626", showocean=True, oceancolor="#070d1a",
            showlakes=False, showcountries=True, countrycolor="#1e2d4a",
            bgcolor="#0a0e1a", projection_type="natural earth",
        ),
        paper_bgcolor="#0a0e1a", plot_bgcolor="#0a0e1a",
        margin=dict(l=0, r=0, t=0, b=0), height=380,
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col_alerts:
    st.markdown('<div class="section-header">Top 5 Current Alerts</div>', unsafe_allow_html=True)
    for alert in alerts:
        level = alert["risk_level"]
        st.markdown(f"""
        <div class="alert-card {level}">
            <div class="alert-title">
                {alert['region']}
                <span class="risk-badge risk-{level}" style="float:right;">{level.upper()}</span>
            </div>
            <div class="alert-meta">{alert['industry']} · Risk: {alert['score']*100:.0f}%</div>
            <div class="alert-signal">{"<br>".join([f"· {s}" for s in alert['signals']])}</div>
        </div>""", unsafe_allow_html=True)

# ── Forecast Chart ────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f'<div class="section-header">21-Day Risk Forecast — {selected_industry} · {selected_region}</div>',
            unsafe_allow_html=True)

bar_colors = ["#ef4444" if s > 0.65 else "#f59e0b" if s > 0.40 else "#22c55e"
              for s in forecast_df["risk_score"]]

fig_forecast = go.Figure()
for threshold, color, label in [(65, "#ef4444", "High Risk"), (40, "#f59e0b", "Medium Risk")]:
    fig_forecast.add_hline(y=threshold, line_dash="dash", line_color=color,
                           line_width=1, opacity=0.4,
                           annotation_text=label, annotation_position="right",
                           annotation_font=dict(color=color, size=10))

fig_forecast.add_trace(go.Bar(
    x=forecast_df["label"], y=forecast_df["risk_pct"],
    marker_color=bar_colors, marker_line_width=0, opacity=0.85,
    hovertemplate="<b>%{x}</b><br>Risk: %{y:.1f}%<extra></extra>",
))
fig_forecast.add_trace(go.Scatter(
    x=forecast_df["label"],
    y=forecast_df["risk_pct"].rolling(3, min_periods=1).mean(),
    mode="lines", line=dict(color="#38bdf8", width=2, dash="dot"),
    name="Trend", hoverinfo="skip",
))
fig_forecast.update_layout(
    paper_bgcolor="#0a0e1a", plot_bgcolor="#0f1525",
    font=dict(color="#64748b", family="DM Sans"),
    xaxis=dict(showgrid=False, tickfont=dict(size=10, color="#475569"),
               tickangle=-45, linecolor="#1e2d4a"),
    yaxis=dict(showgrid=True, gridcolor="#1e2d4a",
               tickfont=dict(size=10, color="#475569"),
               title=dict(text="Risk Score (%)", font=dict(size=11, color="#64748b")),
               range=[0, 100]),
    showlegend=False, margin=dict(l=10, r=80, t=10, b=60),
    height=280, bargap=0.15,
)
st.plotly_chart(fig_forecast, use_container_width=True)

# ── RAG-LLM Panel ─────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">RAG-LLM Model Predictions (Member B — Text Only)</div>',
            unsafe_allow_html=True)

rag_horizon = st.radio(
    "Prediction horizon", [7, 14, 21], index=1, horizontal=True,
    format_func=lambda x: f"{x}-day"
)

rag_f1, rag_auc = MODEL_RESULTS[rag_horizon]["rag"]
lstm_f1, lstm_auc = MODEL_RESULTS[rag_horizon]["lstm"]

# Model comparison cards
rc1, rc2, rc3, rc4 = st.columns(4)
for col, label, value, color in [
    (rc1, f"RAG-LLM F1 ({rag_horizon}d)",  f"{rag_f1}",  "#a78bfa"),
    (rc2, f"RAG-LLM AUC ({rag_horizon}d)", f"{rag_auc}", "#a78bfa"),
    (rc3, f"LSTM F1 ({rag_horizon}d)",      f"{lstm_f1}", "#38bdf8"),
    (rc4, f"LSTM AUC ({rag_horizon}d)",     f"{lstm_auc}","#38bdf8"),
]:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color};">{value}</div>
        </div>""", unsafe_allow_html=True)

st.caption(
    f"RAG-LLM F1={rag_f1} at {rag_horizon}d · "
    f"{'Outperformed' if lstm_f1 > rag_f1 else "Matched"} by LSTM (F1={lstm_f1}) · "
    f"Competitive with XGBoost full features (F1={MODEL_RESULTS[rag_horizon]['xgb_full'][0]}) using text only"
)

# Load RAG prediction file if available
rag_path = f"gdelt_output/rag_predictions_{rag_horizon}d.csv"
if os.path.exists(rag_path):
    rag_df = pd.read_csv(rag_path)
    rag_df["week_start"] = pd.to_datetime(rag_df["week_start"])
    rag_df = rag_df.sort_values("week_start")

    fig_rag = go.Figure()
    fig_rag.add_trace(go.Scatter(
        x=rag_df["week_start"], y=rag_df["probability"],
        mode="lines+markers",
        line=dict(color="#a78bfa", width=2),
        marker=dict(size=5, color="#a78bfa"),
        name="RAG-LLM probability",
        hovertemplate="<b>%{x|%b %d %Y}</b><br>Probability: %{y:.3f}<extra></extra>",
    ))
    fig_rag.add_hline(
        y=0.5, line_dash="dash", line_color="#64748b", line_width=1, opacity=0.5,
        annotation_text="Decision threshold (0.5)",
        annotation_font=dict(color="#64748b", size=10),
    )
    fig_rag.update_layout(
        paper_bgcolor="#0a0e1a", plot_bgcolor="#0f1525",
        font=dict(color="#64748b", family="DM Sans"),
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color="#475569"), linecolor="#1e2d4a"),
        yaxis=dict(showgrid=True, gridcolor="#1e2d4a",
                   tickfont=dict(size=10, color="#475569"),
                   title=dict(text="Disruption Probability", font=dict(size=11, color="#64748b")),
                   range=[0, 1]),
        showlegend=False, margin=dict(l=10, r=80, t=10, b=40), height=250,
    )
    st.plotly_chart(fig_rag, use_container_width=True)
else:
    st.markdown(f"""
    <div class="rag-card">
        <div class="alert-title">RAG-LLM Results Summary ({rag_horizon}-day horizon)</div>
        <div class="alert-signal">
            · F1 Score: {rag_f1} &nbsp;|&nbsp; AUC-ROC: {rag_auc}<br>
            · Text-only model — no GSCPI input, no structured GDELT features<br>
            · LangChain + FAISS RAG pipeline on raw news text<br>
            · To show prediction chart: pull Member B branch and add rag_predictions_{rag_horizon}d.csv
        </div>
    </div>""", unsafe_allow_html=True)

# ── Full Model Comparison Table ───────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">Full Model Comparison</div>', unsafe_allow_html=True)

comparison_data = {
    "Model":     ["ARIMA (baseline)", "LSTM (news only)", "RAG-LLM (text only)",
                  "XGBoost-A (full)", "XGBoost-C (volume)", "XGBoost-B (tone only)"],
    "Type":      ["GSCPI forecast", "News features", "Raw text",
                  "News features", "News features", "News features"],
    f"F1 ({rag_horizon}d)":  [
        MODEL_RESULTS[rag_horizon]["arima"][0],
        MODEL_RESULTS[rag_horizon]["lstm"][0],
        MODEL_RESULTS[rag_horizon]["rag"][0],
        MODEL_RESULTS[rag_horizon]["xgb_full"][0],
        0.516, 0.486,
    ],
    f"AUC ({rag_horizon}d)": [
        MODEL_RESULTS[rag_horizon]["arima"][1],
        MODEL_RESULTS[rag_horizon]["lstm"][1],
        MODEL_RESULTS[rag_horizon]["rag"][1],
        MODEL_RESULTS[rag_horizon]["xgb_full"][1],
        0.581, 0.521,
    ],
    "Notes": [
        "Upper bound — GSCPI not available in real time",
        "Best practical model",
        "No structured features needed",
        "High recall (0.927), low precision",
        "Coverage > sentiment",
        "Raw tone is weak alone",
    ],
}

comp_df = pd.DataFrame(comparison_data)
st.dataframe(
    comp_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        f"F1 ({rag_horizon}d)":  st.column_config.NumberColumn(format="%.3f"),
        f"AUC ({rag_horizon}d)": st.column_config.NumberColumn(format="%.3f"),
    }
)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="font-family:'Space Mono',monospace; font-size:0.65rem;
            color:#1e2d4a; text-align:center; padding:8px 0;">
    NEWSSHIELD · IEEE Research Project · GDELT 2.0 + NY Fed GSCPI ·
    ARIMA · XGBoost · LSTM · RAG-LLM · 14–21 Day Horizon
</div>
""", unsafe_allow_html=True)