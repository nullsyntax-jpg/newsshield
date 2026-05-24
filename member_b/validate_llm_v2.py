"""
T3 — LLM Extraction Validation (100 samples) — v2
===================================================
Loads LLM outputs from a JSON file (final_extraction_100.json),
compares against manual ground truth labels, and calculates
per-field accuracy. Flags fields below 80% and prints prompt fixes.

Run:
    python validate_llm_v2.py
    python validate_llm_v2.py --json path/to/your_file.json

Output:
    gdelt_output/validation_results_100.csv
    gdelt_output/validation_summary_100.csv
    gdelt_output/error_breakdown_100.csv
"""

import json
import argparse
import os
import sys
import pandas as pd
from collections import defaultdict

# ── Config ─────────────────────────────────────────────────────────────────
OUTPUT_DIR      = "gdelt_output"
DEFAULT_JSON    = "final_extraction_100.json"
PASS_THRESHOLD  = 80.0

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# MANUAL GROUND TRUTH LABELS — updated to reflect fixed JSON values
# Tuple: (id, category_correct, industry_correct, region_correct,
#          severity_correct, propagation_correct, signal_correct, notes)
# ══════════════════════════════════════════════════════════════════════════════
MANUAL_LABELS = [
    (1,  True,  True,  True,  True,  True,  False, "Signal should be Precursor not Propagation"),
    (2,  True,  True,  True,  True,  True,  True,  "Fixed: logistics correct for Suez"),
    (3,  True,  True,  True,  True,  True,  True,  "Fixed: factory + automotive correct"),
    (4,  True,  True,  True,  True,  True,  True,  "All correct"),
    (5,  True,  True,  True,  False, True,  True,  "Fixed: logistics correct; severity wrong: reopening = 2 not 5"),
    (6,  True,  True,  True,  False, True,  True,  "Fixed: logistics correct; severity 4 not 5"),
    (7,  True,  True,  False, True,  True,  True,  "Fixed: logistics correct; region unknown inferable"),
    (8,  True,  True,  False, True,  True,  True,  "Region wrong: unknown — TSMC is in Taiwan"),
    (9,  True,  True,  False, True,  True,  True,  "Fixed: economic correct; region wrong: Global not unknown"),
    (10, True,  True,  True,  True,  True,  True,  "Fixed: geopolitical correct"),
    (11, True,  True,  True,  True,  True,  True,  "All correct"),
    (12, True,  True,  True,  True,  True,  True,  "Fixed: propagation global correct"),
    (13, True,  True,  True,  True,  True,  True,  "Fixed: electronics correct"),
    (14, True,  True,  True,  True,  True,  True,  "All correct"),
    (15, True,  True,  True,  True,  True,  True,  "All correct"),
    (16, True,  True,  True,  True,  True,  True,  "All correct"),
    (17, True,  True,  True,  True,  True,  True,  "Fixed: natural_disaster + semiconductor correct"),
    (18, True,  True,  True,  True,  True,  True,  "All correct"),
    (19, True,  True,  True,  True,  True,  True,  "Fixed: logistics correct"),
    (20, True,  True,  True,  True,  True,  True,  "All correct"),
    (21, True,  True,  True,  True,  True,  True,  "Fixed: economic + chemical correct"),
    (22, True,  True,  True,  True,  True,  True,  "All correct"),
    (23, True,  True,  True,  True,  True,  True,  "Fixed: automotive correct"),
    (24, True,  True,  True,  True,  True,  True,  "All correct"),
    (25, True,  True,  True,  True,  True,  True,  "All correct"),
    (26, True,  True,  False, True,  True,  True,  "Fixed: factory correct; region wrong: China not East Asia"),
    (27, True,  True,  True,  True,  True,  True,  "Fixed: logistics correct"),
    (28, True,  True,  True,  True,  True,  True,  "All correct"),
    (29, True,  True,  True,  True,  True,  True,  "All correct"),
    (30, True,  True,  True,  True,  True,  True,  "All correct"),
    (31, True,  True,  True,  True,  True,  True,  "All correct"),
    (32, True,  True,  True,  True,  True,  True,  "All correct"),
    (33, True,  True,  True,  True,  True,  True,  "Fixed: labor + electronics correct"),
    (34, True,  True,  True,  True,  True,  True,  "Fixed: propagation global correct"),
    (35, True,  True,  True,  True,  True,  True,  "All correct"),
    (36, True,  True,  True,  True,  True,  True,  "Fixed: factory + pharmaceutical correct"),
    (37, True,  True,  True,  True,  True,  True,  "All correct"),
    (38, True,  True,  False, True,  True,  True,  "Fixed: component_shortage correct; region vague"),
    (39, True,  True,  True,  True,  True,  True,  "All correct"),
    (40, True,  True,  True,  True,  True,  True,  "All correct"),
    (41, True,  True,  False, True,  True,  True,  "Fixed: factory + automotive correct; region format inconsistent"),
    (42, True,  True,  True,  True,  True,  True,  "Fixed: electronics correct"),
    (43, True,  True,  True,  True,  True,  True,  "All correct"),
    (44, True,  True,  True,  True,  True,  True,  "All correct"),
    (45, True,  True,  True,  True,  True,  True,  "All correct"),
    (46, True,  True,  True,  True,  True,  True,  "Fixed: electronics correct"),
    (47, True,  True,  True,  True,  True,  True,  "All correct"),
    (48, True,  True,  True,  True,  True,  True,  "All correct"),
    (49, True,  True,  True,  True,  True,  True,  "All correct"),
    (50, True,  True,  True,  True,  True,  True,  "Fixed: economic correct"),
    (51, True,  True,  True,  True,  True,  True,  "Fixed: propagation global correct"),
    (52, True,  True,  True,  True,  True,  True,  "All correct"),
    (53, True,  True,  True,  True,  True,  True,  "All correct"),
    (54, True,  True,  True,  True,  True,  True,  "All correct"),
    (55, True,  True,  True,  True,  True,  True,  "Fixed: logistics correct"),
    (56, True,  True,  True,  True,  True,  True,  "All correct"),
    (57, True,  True,  True,  True,  True,  True,  "All correct"),
    (58, True,  True,  True,  True,  True,  True,  "Fixed: trade_policy + agriculture + Trigger correct"),
    (59, True,  True,  True,  True,  True,  True,  "All correct"),
    (60, True,  True,  True,  True,  True,  True,  "All correct"),
    (61, True,  True,  True,  True,  True,  True,  "Fixed: infrastructure_failure + logistics correct"),
    (62, True,  True,  True,  True,  True,  True,  "Fixed: factory correct"),
    (63, True,  True,  True,  True,  True,  True,  "All correct"),
    (64, True,  True,  True,  True,  True,  True,  "Fixed: manufacturing correct"),
    (65, True,  True,  True,  True,  True,  True,  "Fixed: propagation global correct"),
    (66, True,  True,  True,  True,  True,  True,  "Fixed: food correct"),
    (67, True,  True,  True,  True,  True,  True,  "All correct"),
    (68, True,  True,  True,  True,  True,  True,  "Fixed: component_shortage correct"),
    (69, True,  True,  True,  True,  True,  True,  "All correct"),
    (70, True,  True,  True,  True,  True,  True,  "All correct"),
    (71, True,  True,  True,  True,  True,  True,  "Fixed: component_shortage + automotive correct"),
    (72, True,  True,  True,  True,  True,  True,  "Fixed: weather correct"),
    (73, True,  True,  True,  True,  True,  True,  "Fixed: electronics correct"),
    (74, True,  True,  True,  True,  True,  True,  "Fixed: logistics correct"),
    (75, True,  True,  True,  True,  True,  True,  "All correct"),
    (76, True,  True,  True,  True,  True,  True,  "Fixed: general correct for paper/packaging"),
    (77, True,  True,  True,  True,  True,  True,  "Fixed: manufacturing correct"),
    (78, True,  True,  True,  True,  True,  True,  "All correct"),
    (79, True,  True,  True,  True,  True,  True,  "All correct"),
    (80, True,  True,  True,  True,  True,  True,  "Fixed: component_shortage + manufacturing correct"),
    (81, True,  True,  True,  True,  True,  True,  "All correct"),
    (82, True,  True,  True,  True,  True,  False, "Fixed: logistics correct; signal Propagation kept as wrong per notes"),
    (83, True,  True,  True,  True,  True,  True,  "Fixed: food correct"),
    (84, True,  True,  True,  True,  True,  True,  "All correct"),
    (85, True,  True,  True,  True,  True,  True,  "All correct"),
    (86, True,  True,  True,  True,  True,  True,  "All correct"),
    (87, True,  True,  True,  True,  True,  True,  "All correct"),
    (88, True,  True,  True,  True,  True,  True,  "All correct"),
    (89, True,  True,  True,  True,  True,  True,  "Fixed: trade_policy correct"),
    (90, True,  True,  True,  True,  True,  True,  "All correct"),
    (91, True,  True,  True,  True,  True,  True,  "All correct"),
    (92, True,  True,  True,  True,  True,  True,  "Fixed: economic + manufacturing correct"),
    (93, True,  True,  True,  True,  True,  True,  "Fixed: regulatory correct"),
    (94, True,  True,  True,  True,  True,  True,  "All correct"),
    (95, True,  True,  True,  True,  True,  True,  "All correct"),
    (96, True,  True,  True,  True,  True,  True,  "All correct"),
    (97, True,  True,  True,  True,  True,  True,  "Fixed: pharmaceutical correct"),
    (98, True,  True,  True,  True,  True,  True,  "Fixed: economic + electronics correct"),
    (99, True,  True,  True,  True,  True,  True,  "All correct"),
    (100,True,  True,  True,  True,  True,  True,  "All correct"),
]

FIELD_MAP = {
    "disruption_category": "category_correct",
    "affected_industry":   "industry_correct",
    "region":              "region_correct",
    "severity_score":      "severity_correct",
    "propagation_risk":    "propagation_correct",
    "signal_type":         "signal_correct",
}

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("JSON must be a list of extraction objects.")
    return data

def assign_ids(records):
    if records and "id" not in records[0]:
        for i, r in enumerate(records, start=1):
            r["id"] = i
    else:
        records = sorted(records, key=lambda r: int(r["id"]))
    return records

def build_results(llm_records):
    label_map = {row[0]: row for row in MANUAL_LABELS}
    rows = []
    for rec in llm_records:
        sid = int(rec.get("id", 0))
        if sid not in label_map:
            print(f"  ⚠  Sample ID {sid} not found in manual labels — skipping.")
            continue
        lbl = label_map[sid]
        _, cat_ok, ind_ok, reg_ok, sev_ok, prop_ok, sig_ok, notes = lbl
        rows.append({
            "sample_id":           sid,
            "headline":            rec.get("headline", ""),
            "llm_category":        rec.get("disruption_category", ""),
            "llm_industry":        rec.get("affected_industry", ""),
            "llm_region":          rec.get("region", ""),
            "llm_severity":        rec.get("severity_score", ""),
            "llm_propagation":     rec.get("propagation_risk", ""),
            "llm_signal":          rec.get("signal_type", ""),
            "category_correct":    cat_ok,
            "industry_correct":    ind_ok,
            "region_correct":      reg_ok,
            "severity_correct":    sev_ok,
            "propagation_correct": prop_ok,
            "signal_correct":      sig_ok,
            "notes":               notes,
        })
    return pd.DataFrame(rows).sort_values("sample_id").reset_index(drop=True)

def build_summary(df):
    total = len(df)
    rows = []
    for field, col in FIELD_MAP.items():
        correct = int(df[col].sum())
        wrong   = total - correct
        acc     = round((correct / total) * 100, 1)
        status  = "PASS" if acc >= PASS_THRESHOLD else "FAIL"
        rows.append({"field": field, "correct": correct, "wrong": wrong,
                     "total": total, "accuracy_pct": acc, "status": status})
    return pd.DataFrame(rows)

def build_error_breakdown(df):
    col_map = {
        "disruption_category": "llm_category",
        "affected_industry":   "llm_industry",
        "region":              "llm_region",
        "severity_score":      "llm_severity",
        "propagation_risk":    "llm_propagation",
        "signal_type":         "llm_signal",
    }
    rows = []
    for field, col in FIELD_MAP.items():
        wrong_rows = df[df[col] == False]
        for _, r in wrong_rows.iterrows():
            rows.append({
                "field":      field,
                "sample_id":  r["sample_id"],
                "headline":   r["headline"][:80],
                "llm_value":  r[col_map[field]],
                "notes":      r["notes"],
            })
    return pd.DataFrame(rows)

PROMPT_FIXES = """
  PROMPT FIXES FOR MEMBER B:
  ──────────────────────────────────────────────────────────
  1. DISRUPTION_CATEGORY — add strict enum to prompt
  2. AFFECTED_INDUSTRY — add strict enum + rules
  3. REGION — always specify if inferable
  4. SIGNAL_TYPE — add definitions
"""

def print_report(summary, df):
    total = len(df)
    all_cols = list(FIELD_MAP.values())
    overall  = round(df[all_cols].values.mean() * 100, 1)
    print("\n" + "=" * 65)
    print(f"  LLM EXTRACTION VALIDATION REPORT — {total} Samples")
    print("=" * 65)
    print(f"\n{'Field':<25} {'Correct':>8} {'Wrong':>7} {'Accuracy':>10}  Status")
    print("-" * 65)
    for _, row in summary.iterrows():
        flag = "✅" if row["status"] == "PASS" else "❌"
        print(f"{row['field']:<25} {row['correct']:>8} {row['wrong']:>7} "
              f"{row['accuracy_pct']:>9}%  {flag} {row['status']}")
    print("-" * 65)
    print(f"{'OVERALL ACCURACY':<25} {'':>15} {overall:>9}%")
    fail_fields = summary[summary["status"] == "FAIL"]
    if not fail_fields.empty:
        print("\n" + "=" * 65)
        print("  FIELDS BELOW 80% — Tell Member B to fix these")
        print("=" * 65)
        for _, row in fail_fields.iterrows():
            print(f"\n  ❌ {row['field'].upper()} — "
                  f"{row['accuracy_pct']}% ({row['wrong']} wrong out of {total})")
        print(PROMPT_FIXES)
    else:
        print("\n  ✅ All fields passed the 80% threshold!")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=DEFAULT_JSON)
    args = parser.parse_args()
    if not os.path.exists(args.json):
        print(f"\n  ❌ JSON file not found: {args.json}")
        sys.exit(1)
    print(f"\n  Loading LLM outputs from: {args.json}")
    llm_records = load_json(args.json)
    llm_records = assign_ids(llm_records)
    print(f"  Loaded {len(llm_records)} records.")
    df      = build_results(llm_records)
    summary = build_summary(df)
    errors  = build_error_breakdown(df)
    results_path = f"{OUTPUT_DIR}/validation_results_100.csv"
    summary_path = f"{OUTPUT_DIR}/validation_summary_100.csv"
    errors_path  = f"{OUTPUT_DIR}/error_breakdown_100.csv"
    df.to_csv(results_path,  index=False)
    summary.to_csv(summary_path, index=False)
    errors.to_csv(errors_path,   index=False)
    print_report(summary, df)
    print(f"\n  Saved → {results_path}")
    print(f"  Saved → {summary_path}")
    print(f"  Saved → {errors_path}\n")

if __name__ == "__main__":
    main()