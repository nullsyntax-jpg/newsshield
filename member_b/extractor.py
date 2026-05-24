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

Fields:
- disruption_category: one of [port, factory, geopolitical, weather, labor, trade_policy, none]
- affected_industry: one of [semiconductor, automotive, pharmaceutical, food, energy, logistics, general, none]
- region: country or region name as a string (e.g. "Taiwan", "Southeast Asia"), or "unknown"
- severity_score: integer from 1 (minor) to 5 (catastrophic), or 0 if not supply chain related
- propagation_risk: one of [local, regional, global, none]
- signal_type: one of [Precursor, Trigger, Amplifier, Propagation, Response, Recovery, none]

Signal type definitions:
- Precursor: early warning signs before a crisis
- Trigger: the actual event causing disruption
- Amplifier: factors worsening an existing disruption
- Propagation: disruption spreading to other regions or industries
- Response: government or company actions taken
- Recovery: signs the situation is improving
- none: article is not related to supply chain

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
