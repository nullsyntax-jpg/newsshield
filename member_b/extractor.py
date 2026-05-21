import os
import json
import time
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from google import genai

# ── Load API key from .env file ──────────────────────────────────────────────
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ── Prompt template ──────────────────────────────────────────────────────────

def build_prompt(headline: str) -> str:
    return f"""You are a supply chain risk analyst. Read the news headline below and extract structured risk information.

Return ONLY a valid JSON object with exactly these 6 fields. No explanation, no markdown, just raw JSON.

EXTRACTION RULES:

DISRUPTION_CATEGORY — pick the single best fit:
  geopolitical        = war, sanctions, political instability, military action
  trade_policy        = tariffs, export bans, import restrictions, regulations
  labor               = strikes, protests, worker shortages
  weather             = storms, drought, floods (climate-driven)
  natural_disaster    = earthquakes, typhoons, tsunamis (sudden geophysical)
  factory             = plant fires, explosions, production halts, fab delays
  port                = port congestion, canal blockages, shipping route closure
  pandemic            = disease outbreaks, lockdowns, health crises
  regulatory          = government inspections, safety bans, compliance failures
  economic            = price crashes, currency collapse, bankruptcy, demand shifts
  infrastructure_failure = power outages, pipeline breaks, bridge collapse
  component_shortage  = parts/material scarcity, lead time spikes, supply gaps
  cyber               = cyberattacks, ransomware, data breaches
  none                = no disruption present

AFFECTED_INDUSTRY — pick the single most directly impacted:
  semiconductor   = chips, fabs, wafers, PCBs, chip equipment
  automotive      = cars, EVs, auto parts, OEMs
  logistics       = shipping, ports, freight, rail, trucking
  food            = agriculture, crops, food processing, beverages
  energy          = oil, gas, power, renewables, utilities
  pharmaceutical  = drugs, APIs, biotech, medical devices
  apparel         = garments, textiles, fast fashion
  agriculture     = raw crops, fertilizers, farming (pre-processing)
  electronics     = consumer electronics, phones, laptops, displays
  chemical        = industrial chemicals, petrochemicals, specialty chemicals
  manufacturing   = general industrial production, steel, packaging
  mining          = metals, minerals, copper, lithium, iron ore extraction
  aerospace       = aircraft, defense, satellites, aviation
  general         = ONLY if truly no specific industry applies
  none            = no industry impact

SEVERITY_SCORE — integer 1 to 5:
  1 = minimal, localized, temporary
  2 = minor disruption, limited geographic impact
  3 = moderate disruption, some supply chain effect
  4 = major disruption, significant regional/global effect
  5 = critical, systemic, multi-sector or prolonged global impact

PROPAGATION_RISK:
  local    = impact stays within a city/facility
  regional = impact spreads within one country or sub-region
  global   = impact crosses multiple regions or affects world markets
  none     = no propagation expected

SIGNAL_TYPE:
  Precursor   = early warning, risk building but disruption not yet occurred
  Trigger     = direct cause or onset of a disruption event
  Amplifier   = worsens or extends an already active disruption
  Propagation = downstream effect spreading to a new sector or region
  Response    = policy, corporate, or government reaction to a disruption
  Recovery    = situation improving, returning toward normal
  none        = not a supply chain signal

REGION:
  - Always name the specific country or region (e.g. "Taiwan", "West Africa", "North America")
  - If multiple regions affected, list them comma-separated (e.g. "China, United States")
  - Only use "unknown" if the headline contains zero geographic information

Headline: "{headline}"

JSON:"""


# ── Extract one headline ─────────────────────────────────────────────────────
def extract_signal(headline: str) -> dict:
    try:
        response = client.models.generate_content(model="gemini-2.5-flash",contents=build_prompt(headline))
        raw = response.text.strip()
        

        # Clean up if Gemini wraps in markdown code block
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)
        result["headline"] = headline
        result["status"] = "success"
        return result

    except json.JSONDecodeError:
        return {
            "headline": headline,
            "status": "parse_error",
            "raw_response": response.text if "response" in dir() else "no response"
        }
    except Exception as e:
        return {
            "headline": headline,
            "status": "error",
            "error_message": str(e)
        }

# ── Batch process a list of headlines ────────────────────────────────────────
def batch_extract(headlines: list, output_file: str = "extracted_signals.json") -> list:
    results = []

    for headline in tqdm(headlines, desc="Extracting signals"):
        result = extract_signal(headline)
        results.append(result)

        # Rate limiting — Gemini free tier allows ~60 requests per minute
        time.sleep(13)

    # Save all results to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nDone! {len(results)} headlines processed.")
    print(f"Results saved to: {output_file}")

    # Quick summary
    success = sum(1 for r in results if r.get("status") == "success")
    errors  = len(results) - success
    print(f"Successful extractions: {success}")
    print(f"Errors: {errors}")

    return results

# ── Test on 10 sample headlines ───────────────────────────────────────────────
if __name__ == "__main__":
    sample_headlines = [
        "Taiwan semiconductor orders decline for third consecutive month amid geopolitical tensions",
        "Ever Given container ship runs aground, blocking Suez Canal entirely",
        "Toyota halts US assembly lines as Japanese chip shortages reach North American plants",
        "Biden invokes Defense Production Act to accelerate domestic semiconductor manufacturing",
        "Suez Canal fully reopened as Ever Given refloated after six-day blockage",
        "Dockworkers strike at LA port compounds already critical chip shortage for automakers",
        "Monsoon floods damage key rail links used to reroute cargo after Red Sea crisis",
        "TSMC Fab 14 forced to halt production after major fire destroys cleanroom",
        "Semiconductor lead times fall below 20 weeks for first time since 2020 chip crisis",
        "Red Sea shipping delays now hitting food retailers in West Africa, UN warns"
    ]

    print("Running T3 extraction pipeline on 10 sample headlines...\n")
    results = batch_extract(sample_headlines, output_file="test_extraction.json")

    print("\nSample result:")
    print(json.dumps(results[0], indent=2))
