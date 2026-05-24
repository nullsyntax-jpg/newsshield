import json
import time
import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# =====================================================================
# API KEY SANITIZATION & DIAGNOSTICS
# =====================================================================
raw_key = os.getenv("GEMINI_API_KEY")

if not raw_key:
    print("❌ ERROR: No GEMINI_API_KEY found in your .env file!")
    api_key = ""
else:
    # Clean any accidental single quotes, double quotes, or spaces from copy-pasting
    api_key = raw_key.strip().strip("'").strip('"')
    print("\n=================== SYSTEM DIAGNOSTICS ===================")
    print(f"Loaded API Key Length : {len(api_key)} characters")
    print(f"Key Prefix Check      : {api_key[:6]}...{api_key[-4:] if len(api_key) > 4 else ''}")
    print("==========================================================\n")

# Initialize client
client = genai.Client(api_key=api_key)

# Your exact 100 headlines array
headlines = [
    "Taiwan semiconductor orders decline for third consecutive month amid geopolitical tensions",
    "Ever Given container ship runs aground blocking Suez Canal entirely",
    "Toyota halts US assembly lines as Japanese chip shortages reach North American plants",
    "Biden invokes Defense Production Act to accelerate domestic semiconductor manufacturing",
    "Suez Canal fully reopened as Ever Given refloated after six day blockage",
    "Dockworkers strike at LA port compounds already critical chip shortage for automakers",
    "Monsoon floods damage key rail links used to reroute cargo after Red Sea crisis",
    "TSMC Fab 14 forced to halt production after major fire destroys cleanroom",
    "Semiconductor lead times fall below 20 weeks for first time since 2020 chip crisis",
    "Red Sea shipping delays now hitting food retailers in West Africa UN warns",
    "China imposes export restrictions on rare earth minerals used in EV batteries",
    "Russian oil sanctions force European refineries to seek alternative suppliers",
    "Apple shifts iPhone production from China to India amid geopolitical tensions",
    "Global container shipping rates hit record high as demand surges post pandemic",
    "ASML restricts shipment of chip making equipment to China following US pressure",
    "Volkswagen announces closure of three German factories amid EV transition challenges",
    "Samsung Austin fab resumes production after Texas winter storm power outages",
    "India imposes export ban on wheat following domestic shortage concerns",
    "Maersk reroutes vessels around Cape of Good Hope avoiding Red Sea entirely",
    "Ukraine grain export corridor suspended following Russian withdrawal from deal",
    "BASF cuts chemical output by 25 percent due to European energy rationing",
    "Philippine typhoon disrupts electronics manufacturing in Clark economic zone",
    "US imposes 100 percent tariffs on Chinese electric vehicles effective immediately",
    "Lithium carbonate prices crash 80 percent disrupting battery supply chain planning",
    "Boeing 737 MAX grounded globally following second fatal crash in five months",
    "Shanghai port throughput falls 40 percent during two month COVID lockdown",
    "Panama Canal reduces daily transits by half due to historic drought water levels",
    "Houthi militants attack Maersk container vessel in Red Sea with missile strike",
    "UAW strikes Ford GM and Stellantis simultaneously for first time in history",
    "Key Bridge Baltimore collapse closes major US auto import port for months",
    "TSMC evacuates fabs temporarily following 7.4 magnitude Taiwan earthquake",
    "EU launches anti dumping investigation into Chinese solar panel imports",
    "Foxconn Zhengzhou iPhone factory output cut as worker protests intensify",
    "Japan restricts export of chipmaking chemicals to China following US lead",
    "Brazilian drought threatens soybean harvest and global food supply chains",
    "German pharmaceutical company halts API production due to gas supply cuts",
    "Mexico overtakes China as top US trading partner amid nearshoring trend",
    "Nordic semiconductor fab announces 6 month delay due to equipment shortages",
    "Australia halts lithium spodumene exports amid price collapse and oversupply",
    "Italian automotive supplier files bankruptcy amid EV transition difficulties",
    "South Korean battery maker LG Energy announces US gigafactory delay",
    "Taiwanese PCB manufacturers report order cancellations from US customers",
    "French port workers strike halts fuel distribution across northern France",
    "Bangladesh garment factory closures spike amid labor unrest and flooding",
    "Chilean copper mine strike enters third week threatening global supply",
    "Vietnam electronics exports fall sharply as Samsung shifts orders to India",
    "Canadian rail strike disrupts grain potash and auto parts shipments coast to coast",
    "Indonesia bans nickel ore exports to force domestic battery processing investment",
    "Myanmar coup disrupts garment supply chains for European fashion brands",
    "Turkish lira collapse forces auto parts suppliers to halt dollar denominated contracts",
    "Pfizer API supplier in India shuts down following FDA inspection failure",
    "Amazon warns of holiday season delays due to port congestion and driver shortage",
    "Qualcomm reports 6 month chip lead times as smartphone demand recovery stalls",
    "OPEC plus cuts oil production by 2 million barrels per day amid recession fears",
    "Greek shipping strike halts Mediterranean cargo operations for second week",
    "Pakistani floods destroy cotton crop threatening global textile supply chains",
    "Sri Lanka economic collapse disrupts tea and rubber export supply chains",
    "Morocco phosphate export disruption threatens global fertilizer availability",
    "Nigerian oil pipeline sabotage cuts production by 200000 barrels per day",
    "Taiwan Strait military exercises disrupt commercial shipping lane traffic",
    "South African port congestion reaches crisis levels amid infrastructure failures",
    "Japanese auto production cut due to legacy chip shortage from Malaysian fab fire",
    "US China chip war escalates as Beijing restricts gallium and germanium exports",
    "European steel mills shut down as energy costs make production unviable",
    "Indian pharmaceutical regulator bans 14 drug formulations citing quality issues",
    "Mexico avocado export disruption as cartel roadblocks cut Michoacan supply routes",
    "Kenyan flower exports collapse as cold chain logistics break down at Nairobi airport",
    "Singapore semiconductor equipment firm reports 18 month delivery backlog",
    "Dutch horticultural exports disrupted by trucker protest blocking highways",
    "Peru copper mine forced to suspend operations after community blockade",
    "Thailand auto parts exports fall as Japanese OEM orders cut amid chip shortage",
    "Romanian wheat harvest failure worsens European food supply concerns",
    "Taiwanese notebook makers shift final assembly to Vietnam amid China risk",
    "US West Coast dockworker contract talks collapse raising strike threat",
    "Chinese battery manufacturer CATL pauses European gigafactory investment",
    "Finnish pulp mill strike disrupts European packaging material supply",
    "Turkish steel exports surge as Russian supply cut from Western markets",
    "Colombian port strike disrupts coffee banana and coal export schedules",
    "Philippine semiconductor assembly plant damaged by flooding in Laguna province",
    "Swiss watchmaker Swatch reports movement component shortage from Asian suppliers",
    "Bangladeshi ready made garment exports drop as brands diversify to Vietnam",
    "Egyptian Suez Canal revenues surge as Red Sea crisis diverts traffic northward",
    "Indonesian palm oil export ban causes global food inflation concerns",
    "Kenyan tea auction suspended following drought and infrastructure collapse",
    "Cambodian garment factories close as European fast fashion brands cut orders",
    "Mexican auto exports hit record high as nearshoring accelerates post pandemic",
    "Norwegian salmon farming disrupted by sea lice outbreak affecting exports",
    "Ghanaian cocoa output falls sharply amid disease and climate stress",
    "US semiconductor CHIPS Act funding delays frustrate fab construction timelines",
    "European wind turbine supply chain faces steel and rare earth bottlenecks",
    "South Korean shipyard order backlog hits 3 year high amid vessel shortage",
    "Indian steel exports surge as China domestic demand weakens sharply",
    "Brazilian iron ore shipments disrupted by Vale dam safety inspection closure",
    "Moroccan automotive cluster faces wire harness shortage from Ukrainian suppliers",
    "Swedish EV battery startup Northvolt announces gigafactory production delays",
    "Japanese automakers cut production guidance citing ongoing semiconductor shortage",
    "US pharmaceutical supply chain audit reveals 80 percent API dependency on China",
    "Taiwanese display panel makers report inventory glut as consumer demand falls",
    "European chemical industry warns of deindustrialization risk amid energy costs"
]

prompt_template = """You are a supply chain risk analyst. Read the news headline and return ONLY a single JSON object with exactly these 6 fields. Do not include markdown formatting, no conversational intro, and no backticks.

Fields:
- disruption_category: one of [port, factory, geopolitical, weather, labor, trade_policy, none]
- affected_industry: one of [semiconductor, automotive, pharmaceutical, food, energy, logistics, general, none]
- region: country or region name string or unknown
- severity_score: integer 1-5 or 0 if not supply chain related
- propagation_risk: one of [local, regional, global, none]
- signal_type: one of [Precursor, Trigger, Amplifier, Propagation, Response, Recovery, none]

Headline: "{headline}"
JSON:"""

# =====================================================================
# STEP 1: LOAD EXISTING SUCCESSFUL DATA
# =====================================================================
processed_data = {}
if os.path.exists("extraction_100.json"):
    try:
        with open("extraction_100.json", "r", encoding="utf-8") as f:
            old_data = json.load(f)
            for item in old_data:
                if isinstance(item, dict) and item.get("status") == "success" and "headline" in item:
                    processed_data[item["headline"]] = item
        print(f"✨ Loaded {len(processed_data)} successful lines from your file. Skipping these...")
    except Exception as e:
        print(f"Note: Could not parse existing JSON ({e}). Starting fresh.")

# =====================================================================
# STEP 2: RUN THE LOOP WITH SELF-HEALING RETRIES
# =====================================================================
# STEP 2: RUN THE LOOP WITH TRACKING RESETS & INCREASED PACING
# =====================================================================
final_results = []

for i, h in enumerate(headlines):
    if h in processed_data:
        final_results.append(processed_data[h])
        continue
        
    max_retries = 3
    delay = 20
    parsed_json = None
    last_error = ""

    for attempt in range(max_retries):
        # CRITICAL FIX: Explicitly kill any old response text from previous loops
        response = None 
        
        try:
            clean_headline = str(h).replace('"', '').replace("'", "").strip()
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    "You are a supply chain risk analyst. Read the news headline and return ONLY a single JSON object with exactly these 6 fields: disruption_category, affected_industry, region, severity_score, propagation_risk, signal_type. Do not include markdown formatting like ```json, no conversational intro, and no backticks.",
                    f"Headline to analyze: {clean_headline}"
                ]
            )
            
            raw_text = response.text.strip()
            if "```" in raw_text:
                raw_text = raw_text.replace("```json", "").replace("```", "")
            raw_text = raw_text.strip()
            
            parsed_json = json.loads(raw_text)
            break 
            
        except Exception as e:
            err_str = str(e)
            last_error = err_str
            
            # Diagnostic flag showing if the crash happened before or after the server responded
            resp_state = "No response object created" if response is None else "Server replied with text"
            
            if "429" in err_str or "LIMIT" in err_str.upper() or "RESOURCE_EXHAUSTED" in err_str:
                sleep_time = delay * (2 ** attempt) + 30
                print(f"⚠️ Rate limited (429). State: {resp_state}. Pausing {sleep_time}s... (Attempt {attempt+1}/{max_retries})")
            elif "503" in err_str or "UNAVAILABLE" in err_str.upper():
                sleep_time = delay * (2 ** attempt)
                print(f"⚠️ Server Overloaded (503). Retrying in {sleep_time}s...")
            else:
                sleep_time = 15
                print(f"⚠️ API/Formatting Error. Retrying in {sleep_time}s...")
                
            time.sleep(sleep_time)

    if parsed_json is not None:
        result = parsed_json
        result["headline"] = h
        result["status"] = "success"
        print(f"[{i+1}/100] OK  — {h[:45]}...")
        final_results.append(result)
        
        # Save progress instantly
        with open("extraction_100.json", "w", encoding="utf-8") as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False)
    else:
        # If a row fails entirely, we do NOT want to skip it forever on the next run!
        print(f"[{i+1}/100] SKIPPED — Key exhausted. Will retry this row fresh next run.")
        break # Hard stop the script so it stops burning attempts when the key is totally dead

    # Increased delay buffer to 20 seconds to protect free tier RPM limits
    time.subplots = time.sleep(20) 

print("\nTask paused cleanly. Run the script again to resume from the last completed row!")