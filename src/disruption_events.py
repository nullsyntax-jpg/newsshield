"""
Ground Truth Supply Chain Disruption Events (2019–2024)
========================================================
25 documented events with start date, industry, region, severity.
Severity scale: 1 (minor) → 5 (catastrophic / global)
 
Run:  python disruption_events.py
Output: disruption_ground_truth.csv
"""
 
import pandas as pd
import os
 
OUTPUT_DIR = "gdelt_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
 
DISRUPTION_EVENTS = [
    # ── 2019 ─────────────────────────────────────────────────────────────────
    {
        "event_id": "D001",
        "event_name": "US-China Trade War Tariff Escalation",
        "start_date": "2019-05-10",
        "end_date": "2020-01-15",
        "industry": "Electronics, Agriculture, Manufacturing",
        "region": "Global (US–China)",
        "country_codes": "USA,CHN",
        "severity": 3,
        "description": "US raised tariffs to 25% on $200B of Chinese goods; China retaliated. Major reshoring pressure on electronics and consumer goods supply chains.",
        "source": "USTR, WTO",
        "cameo_codes_expected": "13,17,172,1211",
    },
    {
        "event_id": "D002",
        "event_name": "Boeing 737 MAX Global Grounding",
        "start_date": "2019-03-13",
        "end_date": "2020-11-18",
        "industry": "Aerospace, Aviation",
        "region": "Global",
        "country_codes": "USA,EU,CHN",
        "severity": 3,
        "description": "All 737 MAX aircraft grounded following two fatal crashes. Cascading supplier shutdowns and $20B+ in lost orders across aerospace supply chains.",
        "source": "FAA, Boeing earnings",
        "cameo_codes_expected": "14,17",
    },
    # ── 2020 ─────────────────────────────────────────────────────────────────
    {
        "event_id": "D003",
        "event_name": "COVID-19 Wuhan Factory Shutdowns",
        "start_date": "2020-01-23",
        "end_date": "2020-03-10",
        "industry": "Electronics, Automotive, PPE",
        "region": "China (Hubei Province)",
        "country_codes": "CHN",
        "severity": 5,
        "description": "Wuhan and Hubei province locked down. Factories supplying auto parts, electronics components, and pharmaceutical precursors halted production.",
        "source": "Caixin, Reuters",
        "cameo_codes_expected": "14,20,145",
    },
    {
        "event_id": "D004",
        "event_name": "COVID-19 Global Lockdowns — Manufacturing Halt",
        "start_date": "2020-03-15",
        "end_date": "2020-06-01",
        "industry": "Automotive, Apparel, Consumer Goods",
        "region": "Global",
        "country_codes": "ITA,ESP,IND,USA,BRA",
        "severity": 5,
        "description": "Italy, Spain, India, US all halted non-essential manufacturing. Global PPE shortage. Toilet paper, hand sanitizer demand spikes caused retail supply chaos.",
        "source": "ILO, IMF",
        "cameo_codes_expected": "14,17,20,145",
    },
    {
        "event_id": "D005",
        "event_name": "US West Coast Port Congestion (COVID demand surge)",
        "start_date": "2020-10-01",
        "end_date": "2022-01-01",
        "industry": "Retail, Consumer Electronics, Furniture",
        "region": "North America (LA/Long Beach)",
        "country_codes": "USA",
        "severity": 4,
        "description": "Massive e-commerce surge created unprecedented port backlogs. Container ships queued for weeks off Los Angeles. Freight rates rose 10x from pre-COVID levels.",
        "source": "Port of Los Angeles, Freightos",
        "cameo_codes_expected": "14,17",
    },
    # ── 2021 ─────────────────────────────────────────────────────────────────
    {
        "event_id": "D006",
        "event_name": "Suez Canal Blockage — Ever Given",
        "start_date": "2021-03-23",
        "end_date": "2021-03-29",
        "industry": "Shipping, Oil, Consumer Goods",
        "region": "Middle East (Suez Canal, Egypt)",
        "country_codes": "EGY",
        "severity": 4,
        "description": "MV Ever Given ran aground, blocking the Suez Canal for 6 days. ~$9.6B/day in trade halted. Oil price spike. 400+ vessels diverted around Cape of Good Hope.",
        "source": "Lloyd's List, Suez Canal Authority",
        "cameo_codes_expected": "17,14",
    },
    {
        "event_id": "D007",
        "event_name": "Taiwan Semiconductor Drought",
        "start_date": "2021-05-01",
        "end_date": "2022-06-01",
        "industry": "Semiconductors, Automotive, Consumer Electronics",
        "region": "Asia-Pacific (Taiwan)",
        "country_codes": "TWN,JPN,KOR",
        "severity": 4,
        "description": "Severe drought reduced hydroelectric power at TSMC fabs. Combined with COVID demand surge, global chip shortage hit auto and electronics industries hard.",
        "source": "TSMC earnings, IEA",
        "cameo_codes_expected": "13,17",
    },
    {
        "event_id": "D008",
        "event_name": "Yantian Port COVID Closure (Shenzhen)",
        "start_date": "2021-05-21",
        "end_date": "2021-06-24",
        "industry": "Electronics, Consumer Goods, Retail",
        "region": "China (Guangdong)",
        "country_codes": "CHN",
        "severity": 3,
        "description": "COVID outbreak at Yantian port (world's 4th busiest) caused partial closure for 5 weeks. Created massive backlogs equivalent to a Suez-level disruption for electronics exporters.",
        "source": "Flexport, Reuters",
        "cameo_codes_expected": "17,14,20",
    },
    {
        "event_id": "D009",
        "event_name": "Texas Winter Storm Uri — Energy & Petrochemical",
        "start_date": "2021-02-10",
        "end_date": "2021-02-20",
        "industry": "Petrochemicals, Plastics, Semiconductors",
        "region": "North America (Texas, US)",
        "country_codes": "USA",
        "severity": 3,
        "description": "Unprecedented winter storm knocked out Texas power grid. Shut Samsung Austin fab, major plastics plants, and petrochemical hubs. Caused months-long resin and plastics shortages.",
        "source": "ERCOT, IHS Markit",
        "cameo_codes_expected": "14,20",
    },
    {
        "event_id": "D010",
        "event_name": "Ningbo-Zhoushan Port Partial Closure",
        "start_date": "2021-08-11",
        "end_date": "2021-08-26",
        "industry": "General Shipping, Electronics, Auto Parts",
        "region": "China (Zhejiang)",
        "country_codes": "CHN",
        "severity": 3,
        "description": "Single COVID case triggered closure of Meishan terminal at world's 3rd busiest port. Two-week closure added weeks of delays to trans-Pacific shipping schedules.",
        "source": "Bloomberg, Flexport",
        "cameo_codes_expected": "17,14",
    },
    # ── 2022 ─────────────────────────────────────────────────────────────────
    {
        "event_id": "D011",
        "event_name": "Russia-Ukraine War — Energy & Commodity Sanctions",
        "start_date": "2022-02-24",
        "end_date": "2024-12-31",
        "industry": "Energy, Agriculture, Steel, Fertilizer",
        "region": "Europe (Ukraine, Russia)",
        "country_codes": "RUS,UKR,EU",
        "severity": 5,
        "description": "Russia invaded Ukraine. Immediate Western sanctions on Russian oil, gas, metals, and fertilizers. Wheat and sunflower oil exports halted. European energy crisis ensued.",
        "source": "EU Council, USDA",
        "cameo_codes_expected": "13,17,20,1211,1221,172",
    },
    {
        "event_id": "D012",
        "event_name": "Shanghai COVID Lockdown",
        "start_date": "2022-04-01",
        "end_date": "2022-06-01",
        "industry": "Electronics, Automotive, Logistics",
        "region": "China (Shanghai)",
        "country_codes": "CHN",
        "severity": 5,
        "description": "Shanghai (China's largest port city) locked down for 2 months under Zero-COVID. Tesla, SAIC, major semiconductor assembly plants halted. Shanghai port throughput fell 40%.",
        "source": "Caixin, Port of Shanghai",
        "cameo_codes_expected": "14,17,20,145",
    },
    {
        "event_id": "D013",
        "event_name": "European Energy Crisis — Natural Gas Rationing",
        "start_date": "2022-07-01",
        "end_date": "2023-03-01",
        "industry": "Chemicals, Fertilizer, Aluminum, Glass",
        "region": "Europe",
        "country_codes": "DEU,FRA,ITA,NLD",
        "severity": 4,
        "description": "Russian gas cutoffs forced European industry to ration energy. BASF and major chemical plants reduced output. Fertilizer production halved. Aluminum smelters shut across continent.",
        "source": "IEA, Eurostat",
        "cameo_codes_expected": "13,17,1222,172",
    },
    {
        "event_id": "D014",
        "event_name": "China Xinjiang Cotton / Forced Labor Bans",
        "start_date": "2022-06-21",
        "end_date": "2024-12-31",
        "industry": "Apparel, Textiles, Solar Panels",
        "region": "China (Xinjiang)",
        "country_codes": "CHN,USA",
        "severity": 3,
        "description": "US Uyghur Forced Labor Prevention Act (UFLPA) blocked all Xinjiang cotton imports. Solar panel polysilicon imports also affected. Massive sourcing restructuring required.",
        "source": "US CBP, CSIS",
        "cameo_codes_expected": "17,1221,172",
    },
    {
        "event_id": "D015",
        "event_name": "Taiwan Strait Tensions — TSMC Risk",
        "start_date": "2022-08-02",
        "end_date": "2022-08-10",
        "industry": "Semiconductors, Electronics",
        "region": "Asia-Pacific (Taiwan Strait)",
        "country_codes": "TWN,CHN,USA",
        "severity": 3,
        "description": "Chinese military exercises around Taiwan following Pelosi visit created acute semiconductor supply risk. Markets priced in potential blockade scenarios.",
        "source": "Reuters, TSMC",
        "cameo_codes_expected": "13,17,131",
    },
    # ── 2023 ─────────────────────────────────────────────────────────────────
    {
        "event_id": "D016",
        "event_name": "US-EU Chip Export Controls on China",
        "start_date": "2023-10-17",
        "end_date": "2024-12-31",
        "industry": "Semiconductors, AI Hardware",
        "region": "Global",
        "country_codes": "USA,NLD,JPN,CHN",
        "severity": 3,
        "description": "US expanded chip export controls; Netherlands (ASML) and Japan joined. Blocked sale of advanced AI chips and chipmaking equipment to China. Huawei workarounds emerged.",
        "source": "BIS, Reuters",
        "cameo_codes_expected": "17,1221,1211,172",
    },
    {
        "event_id": "D017",
        "event_name": "Panama Canal Drought — Water Level Crisis",
        "start_date": "2023-08-01",
        "end_date": "2024-02-01",
        "industry": "Shipping, LNG, Grain, Consumer Goods",
        "region": "Central America (Panama)",
        "country_codes": "PAN",
        "severity": 4,
        "description": "Severe El Niño drought reduced canal water levels to historic lows. Daily transits cut from 36 to 18. LNG carriers, grain ships diverted to Suez or Cape Horn.",
        "source": "Panama Canal Authority, Bloomberg",
        "cameo_codes_expected": "17,14",
    },
    {
        "event_id": "D018",
        "event_name": "Houthi Red Sea Shipping Attacks",
        "start_date": "2023-12-08",
        "end_date": "2024-12-31",
        "industry": "Shipping, Oil, Retail, Automotive",
        "region": "Middle East (Red Sea, Bab el-Mandeb)",
        "country_codes": "YEM",
        "severity": 5,
        "description": "Houthi missiles and drones targeted commercial ships in Red Sea, citing Gaza conflict. Major carriers (Maersk, MSC, CMA CGM) rerouted around Cape of Good Hope, adding 10-14 days and $1M+ per voyage.",
        "source": "Lloyd's, Drewry",
        "cameo_codes_expected": "13,20,17,131",
    },
    {
        "event_id": "D019",
        "event_name": "UAW Auto Strike — Detroit Three",
        "start_date": "2023-09-15",
        "end_date": "2023-10-30",
        "industry": "Automotive",
        "region": "North America (USA)",
        "country_codes": "USA",
        "severity": 3,
        "description": "United Auto Workers struck Ford, GM, and Stellantis simultaneously for the first time. ~50,000 workers walked out. Supplier layoffs cascaded. ~$9.3B estimated economic loss.",
        "source": "UAW, Anderson Economic Group",
        "cameo_codes_expected": "14,140,141",
    },
    {
        "event_id": "D020",
        "event_name": "Key Bridge Baltimore Port Collapse",
        "start_date": "2024-03-26",
        "end_date": "2024-07-01",
        "industry": "Automotive, Coal, Sugar, Agriculture",
        "region": "North America (Baltimore, USA)",
        "country_codes": "USA",
        "severity": 3,
        "description": "MV Dali cargo ship struck the Francis Scott Key Bridge, causing its collapse and closing Port of Baltimore. US's top auto import port shut for months. Coal and sugar exports also disrupted.",
        "source": "USACE, Port of Baltimore",
        "cameo_codes_expected": "20,17,14",
    },
    # ── 2024 ─────────────────────────────────────────────────────────────────
    {
        "event_id": "D021",
        "event_name": "Taiwan Earthquake — TSMC Production Impact",
        "start_date": "2024-04-03",
        "end_date": "2024-04-15",
        "industry": "Semiconductors",
        "region": "Asia-Pacific (Taiwan)",
        "country_codes": "TWN",
        "severity": 2,
        "description": "7.4 magnitude earthquake struck Hualien. TSMC evacuated fabs temporarily. Wafer damage estimated at hundreds of millions. Short disruption but markets reacted sharply.",
        "source": "TSMC, CNA",
        "cameo_codes_expected": "20",
    },
    {
        "event_id": "D022",
        "event_name": "US-China EV Tariff Escalation",
        "start_date": "2024-05-14",
        "end_date": "2024-12-31",
        "industry": "Electric Vehicles, Batteries, Solar",
        "region": "Global (US–China)",
        "country_codes": "USA,CHN,EU",
        "severity": 3,
        "description": "Biden administration raised EV tariffs on China from 25% to 100%. Battery tariffs to 25%, solar cells to 50%. EU launched parallel investigations. Triggered major supply chain restructuring in EV sector.",
        "source": "USTR, Reuters",
        "cameo_codes_expected": "17,1211,1221",
    },
    {
        "event_id": "D023",
        "event_name": "German Auto Industry Crisis — VW Plant Closures",
        "start_date": "2024-09-02",
        "end_date": "2024-12-31",
        "industry": "Automotive",
        "region": "Europe (Germany)",
        "country_codes": "DEU",
        "severity": 3,
        "description": "Volkswagen announced potential closure of 3 German factories for first time in 87-year history. IG Metall strikes followed. EV transition, Chinese competition, and energy costs cited.",
        "source": "VW AG, Der Spiegel",
        "cameo_codes_expected": "14,141,17",
    },
    {
        "event_id": "D024",
        "event_name": "India Pharmaceutical Export Restrictions",
        "start_date": "2024-01-15",
        "end_date": "2024-06-01",
        "industry": "Pharmaceuticals, Healthcare",
        "region": "South Asia (India)",
        "country_codes": "IND",
        "severity": 2,
        "description": "India imposed export controls on certain drug formulations and APIs (active pharmaceutical ingredients) following domestic shortage concerns. Affected paracetamol, antibiotics supply to Africa and SE Asia.",
        "source": "DGFT India, Reuters",
        "cameo_codes_expected": "17,172,1221",
    },
    {
        "event_id": "D025",
        "event_name": "Lithium Price Crash — Battery Supply Chain Restructure",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "industry": "Battery, EV, Mining",
        "region": "Global (Australia, Chile, China)",
        "country_codes": "AUS,CHL,CHN",
        "severity": 2,
        "description": "Lithium carbonate prices fell 80%+ from 2022 peaks. Australian spodumene miners shut operations. Chilean producers curtailed. Paradoxically disrupted battery supply chains that had built inventory assumptions around high prices.",
        "source": "Fastmarkets, Mining.com",
        "cameo_codes_expected": "14,17",
    },
]
 
 
def build_ground_truth_csv():
    df = pd.DataFrame(DISRUPTION_EVENTS)
 
    # Derived columns
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])
    df["duration_days"] = (df["end_date"] - df["start_date"]).dt.days
    df["year"] = df["start_date"].dt.year
 
    # Severity label
    severity_map = {1: "Minor", 2: "Moderate", 3: "Significant", 4: "Severe", 5: "Catastrophic"}
    df["severity_label"] = df["severity"].map(severity_map)
 
    out_path = os.path.join(OUTPUT_DIR, "disruption_ground_truth.csv")
    df.to_csv(out_path, index=False)
    print(f"✓ Saved {len(df)} events → {out_path}")
 
    # Summary by year
    print("\n── Event count by year ──")
    print(df.groupby("year").size().to_string())
 
    print("\n── Severity distribution ──")
    print(df["severity_label"].value_counts().to_string())
 
    return df
 
 
if __name__ == "__main__":
    df = build_ground_truth_csv()
    print("\n── First 5 events ──")
    print(df[["event_id","event_name","start_date","region","severity_label"]].head().to_string(index=False))
