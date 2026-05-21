"""
T3 — LLM Extraction Validation — v3
=====================================
Ground truth labels are stored in a CSV (ground_truth_labels.csv).
Just drop in a new JSON from Member B and re-run — no manual edits needed.

First run (exports labels to CSV):
    python validate_llm_v3.py --export-labels

Every subsequent run (compare new JSON against labels):
    python validate_llm_v3.py --json gdelt_output/final_extraction_100.json

Output:
    gdelt_output/validation_results.csv
    gdelt_output/validation_summary.csv
    gdelt_output/error_breakdown.csv
"""

import json
import argparse
import os
import sys
import pandas as pd

# ── Config ──────────────────────────────────────────────────────────────────
OUTPUT_DIR      = "gdelt_output"
LABELS_CSV      = "gdelt_output/ground_truth_labels.csv"
DEFAULT_JSON    = "gdelt_output/final_extraction_100.json"
PASS_THRESHOLD  = 80.0

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# GROUND TRUTH LABELS (used only to export once — after that, CSV is master)
# ══════════════════════════════════════════════════════════════════════════════
MANUAL_LABELS = [
    (1,  True,  True,  True,  True,  True,  False, "Signal should be Precursor not Propagation"),
    (2,  True,  False, True,  True,  True,  True,  "Industry wrong: Suez = logistics not automotive"),
    (3,  False, False, True,  True,  False, False, "Category wrong: factory/labor; industry: automotive not semiconductor; signal: Trigger"),
    (4,  True,  True,  True,  True,  True,  True,  "All correct"),
    (5,  True,  False, True,  False, True,  True,  "Industry wrong: logistics not automotive; severity: 2 not 5"),
    (6,  True,  False, True,  False, True,  True,  "Industry wrong: logistics not semiconductor; severity: 4 not 5"),
    (7,  True,  False, False, True,  True,  True,  "Industry wrong: logistics not automotive; region: unknown inferable as South/SE Asia"),
    (8,  True,  True,  False, True,  True,  True,  "Region wrong: unknown — TSMC is in Taiwan"),
    (9,  False, True,  False, True,  True,  True,  "Category wrong: Recovery not factory; region: Global not unknown"),
    (10, False, True,  True,  True,  True,  True,  "Category wrong: geopolitical not port"),
    (11, True,  True,  True,  True,  True,  True,  "All correct"),
    (12, True,  True,  True,  True,  False, True,  "Propagation wrong: global not regional"),
    (13, True,  False, True,  True,  True,  True,  "Industry wrong: electronics not general"),
    (14, True,  True,  True,  True,  True,  True,  "All correct"),
    (15, True,  True,  True,  True,  True,  True,  "All correct"),
    (16, True,  True,  True,  True,  True,  True,  "All correct"),
    (17, False, False, True,  True,  True,  True,  "Category: natural_disaster not weather; industry: semiconductor not energy"),
    (18, True,  True,  True,  True,  True,  True,  "All correct"),
    (19, True,  False, True,  True,  True,  True,  "Industry wrong: logistics not general"),
    (20, True,  True,  True,  True,  True,  True,  "All correct"),
    (21, False, False, True,  True,  True,  True,  "Category: economic not geopolitical; industry: chemical not energy"),
    (22, True,  True,  True,  True,  True,  True,  "All correct"),
    (23, True,  False, True,  True,  True,  True,  "Industry wrong: automotive not general"),
    (24, True,  True,  True,  True,  True,  True,  "All correct"),
    (25, True,  True,  True,  True,  True,  True,  "All correct"),
    (26, False, True,  False, True,  True,  True,  "Category: factory/pandemic; region: China not East Asia"),
    (27, True,  False, True,  True,  True,  True,  "Industry wrong: logistics not automotive"),
    (28, True,  True,  True,  True,  True,  True,  "All correct"),
    (29, True,  True,  True,  True,  True,  True,  "All correct"),
    (30, True,  True,  True,  True,  True,  True,  "All correct"),
    (31, True,  True,  True,  True,  True,  True,  "All correct"),
    (32, True,  True,  True,  True,  True,  True,  "All correct"),
    (33, False, False, True,  True,  True,  True,  "Category: labor not geopolitical; industry: electronics not general"),
    (34, True,  True,  True,  True,  False, True,  "Propagation wrong: global not regional"),
    (35, True,  True,  True,  True,  True,  True,  "All correct"),
    (36, False, False, True,  True,  True,  True,  "Category: factory; industry: pharmaceutical not energy"),
    (37, True,  True,  True,  True,  True,  True,  "All correct"),
    (38, False, True,  False, True,  True,  True,  "Category: component_shortage not factory; region: Nordic needs country"),
    (39, True,  True,  True,  True,  True,  True,  "All correct"),
    (40, True,  True,  True,  True,  True,  True,  "All correct"),
    (41, False, False, False, True,  True,  True,  "Industry: automotive not energy; region format inconsistent"),
    (42, True,  False, True,  True,  True,  True,  "Industry wrong: electronics not semiconductor"),
    (43, True,  True,  True,  True,  True,  True,  "All correct"),
    (44, True,  True,  True,  True,  True,  True,  "All correct"),
    (45, True,  True,  True,  True,  True,  True,  "All correct"),
    (46, True,  False, True,  True,  True,  True,  "Industry wrong: electronics not semiconductor"),
    (47, True,  True,  True,  True,  True,  True,  "All correct"),
    (48, True,  True,  True,  True,  True,  True,  "All correct"),
    (49, True,  True,  True,  True,  True,  True,  "All correct"),
    (50, False, True,  True,  True,  True,  True,  "Category wrong: economic not infrastructure_failure"),
    (51, True,  True,  True,  True,  False, True,  "Propagation wrong: global not local"),
    (52, True,  True,  True,  True,  True,  True,  "All correct"),
    (53, True,  True,  True,  True,  True,  True,  "All correct"),
    (54, True,  True,  True,  True,  True,  True,  "All correct"),
    (55, True,  False, True,  True,  True,  True,  "Industry wrong: logistics not automotive"),
    (56, True,  True,  True,  True,  True,  True,  "All correct"),
    (57, True,  True,  True,  True,  True,  True,  "All correct"),
    (58, False, False, True,  True,  True,  False, "Category: trade_policy; industry: agriculture not mining; signal: Precursor not Trigger"),
    (59, True,  True,  True,  True,  True,  True,  "All correct"),
    (60, True,  True,  True,  True,  True,  True,  "All correct"),
    (61, False, False, True,  True,  True,  True,  "Category: infrastructure_failure; industry: logistics not automotive"),
    (62, False, True,  True,  True,  True,  True,  "Category wrong: component_shortage not factory"),
    (63, True,  True,  True,  True,  True,  True,  "All correct"),
    (64, True,  False, True,  True,  True,  True,  "Industry wrong: manufacturing not energy"),
    (65, True,  True,  True,  True,  False, True,  "Propagation wrong: global not regional"),
    (66, True,  False, True,  True,  True,  True,  "Industry wrong: food not automotive"),
    (67, True,  True,  True,  True,  True,  True,  "All correct"),
    (68, False, True,  True,  True,  True,  True,  "Category wrong: component_shortage not port"),
    (69, True,  True,  True,  True,  True,  True,  "All correct"),
    (70, True,  True,  True,  True,  True,  True,  "All correct"),
    (71, False, False, True,  True,  True,  True,  "Industry wrong: automotive not semiconductor"),
    (72, False, True,  True,  True,  True,  True,  "Category wrong: weather not economic"),
    (73, True,  False, True,  True,  True,  True,  "Industry wrong: electronics not general"),
    (74, True,  False, True,  True,  True,  True,  "Industry wrong: logistics not general"),
    (75, True,  True,  True,  True,  True,  True,  "All correct"),
    (76, True,  False, True,  True,  True,  True,  "Industry wrong: manufacturing/packaging not general"),
    (77, True,  False, True,  True,  True,  True,  "Industry wrong: manufacturing not logistics"),
    (78, True,  True,  True,  True,  True,  True,  "All correct"),
    (79, True,  True,  True,  True,  True,  True,  "All correct"),
    (80, False, False, True,  True,  True,  True,  "Category: component_shortage; industry: electronics not logistics"),
    (81, True,  True,  True,  True,  True,  True,  "All correct"),
    (82, True,  False, True,  True,  True,  False, "Industry: logistics not automotive; signal: keep Propagation"),
    (83, True,  False, True,  True,  True,  True,  "Industry wrong: food not energy"),
    (84, True,  True,  True,  True,  True,  True,  "All correct"),
    (85, True,  True,  True,  True,  True,  True,  "All correct"),
    (86, True,  True,  True,  True,  True,  True,  "All correct"),
    (87, True,  True,  True,  True,  True,  True,  "All correct"),
    (88, True,  True,  True,  True,  True,  True,  "All correct"),
    (89, False, True,  True,  True,  True,  True,  "Category wrong: trade_policy not factory"),
    (90, True,  True,  True,  True,  True,  True,  "All correct"),
    (91, True,  True,  True,  True,  True,  True,  "All correct"),
    (92, False, False, True,  True,  True,  True,  "Category: economic; industry: manufacturing not logistics"),
    (93, False, True,  True,  True,  True,  True,  "Category wrong: regulatory not factory"),
    (94, True,  True,  True,  True,  True,  True,  "All correct"),
    (95, True,  True,  True,  True,  True,  True,  "All correct"),
    (96, True,  True,  True,  True,  True,  True,  "All correct"),
    (97, True,  False, True,  True,  True,  True,  "Industry wrong: pharmaceutical not automotive"),
    (98, False, False, True,  True,  True,  True,  "Category: economic; industry: electronics not logistics"),
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

COL_MAP = {
    "disruption_category": "llm_category",
    "affected_industry":   "llm_industry",
    "region":              "llm_region",
    "severity_score":      "llm_severity",
    "propagation_risk":    "llm_propagation",
    "signal_type":         "llm_signal",
}

PROMPT_FIXES = """
  PROMPT FIXES FOR MEMBER B:
  ──────────────────────────────────────────────────────────
  1. DISRUPTION_CATEGORY — use strict enum:
     geopolitical | trade_policy | labor | weather | factory | port |
     pandemic | regulatory | economic | infrastructure_failure |
     natural_disaster | component_shortage | cyber | none

  2. AFFECTED_INDUSTRY — use strict enum:
     semiconductor | automotive | logistics | food | energy |
     pharmaceutical | apparel | agriculture | electronics |
     chemical | manufacturing | mining | aerospace | general | none
     → port/shipping events   = logistics  (NOT automotive)
     → garment/textile        = apparel    (NOT general)
     → steel/chemical plant   = manufacturing (NOT energy)
     → iPhone/laptop/notebook = electronics (NOT general)
     → copper/lithium/ore     = mining     (NOT general)

  3. REGION — always infer from context.
     Only use 'unknown' if headline has zero geographic info.

  4. SIGNAL_TYPE — definitions:
     Precursor=early warning | Trigger=direct cause |
     Amplifier=worsens disruption | Propagation=downstream effect |
     Response=policy/corporate reaction | Recovery=improving
"""

# ══════════════════════════════════════════════════════════════════════════════
# EXPORT LABELS TO CSV
# ══════════════════════════════════════════════════════════════════════════════

def export_labels():
    rows = []
    for lbl in MANUAL_LABELS:
        sid, cat_ok, ind_ok, reg_ok, sev_ok, prop_ok, sig_ok, notes = lbl
        rows.append({
            "sample_id":           sid,
            "category_correct":    cat_ok,
            "industry_correct":    ind_ok,
            "region_correct":      reg_ok,
            "severity_correct":    sev_ok,
            "propagation_correct": prop_ok,
            "signal_correct":      sig_ok,
            "notes":               notes,
        })
    df = pd.DataFrame(rows)
    df.to_csv(LABELS_CSV, index=False)
    print(f"\n  ✅ Ground truth labels exported to: {LABELS_CSV}")
    print(f"     Edit this CSV directly to update any label.\n")


# ══════════════════════════════════════════════════════════════════════════════
# LOAD FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("JSON must be a list of extraction objects.")
    # assign IDs if missing
    if data and "id" not in data[0]:
        for i, r in enumerate(data, start=1):
            r["id"] = i
    else:
        data = sorted(data, key=lambda r: int(r["id"]))
    return data


def load_labels():
    if not os.path.exists(LABELS_CSV):
        print(f"\n  ⚠  Labels CSV not found. Generating from built-in labels...")
        export_labels()
    return pd.read_csv(LABELS_CSV)


# ══════════════════════════════════════════════════════════════════════════════
# BUILD DATAFRAMES
# ══════════════════════════════════════════════════════════════════════════════

def build_results(llm_records, labels_df):
    label_map = labels_df.set_index("sample_id").to_dict("index")
    rows = []
    for rec in llm_records:
        sid = int(rec.get("id", 0))
        if sid not in label_map:
            print(f"  ⚠  Sample ID {sid} not in labels — skipping.")
            continue
        lbl = label_map[sid]
        rows.append({
            "sample_id":           sid,
            "headline":            rec.get("headline", ""),
            "llm_category":        rec.get("disruption_category", ""),
            "llm_industry":        rec.get("affected_industry", ""),
            "llm_region":          rec.get("region", ""),
            "llm_severity":        rec.get("severity_score", ""),
            "llm_propagation":     rec.get("propagation_risk", ""),
            "llm_signal":          rec.get("signal_type", ""),
            "category_correct":    bool(lbl["category_correct"]),
            "industry_correct":    bool(lbl["industry_correct"]),
            "region_correct":      bool(lbl["region_correct"]),
            "severity_correct":    bool(lbl["severity_correct"]),
            "propagation_correct": bool(lbl["propagation_correct"]),
            "signal_correct":      bool(lbl["signal_correct"]),
            "notes":               lbl["notes"],
        })
    return pd.DataFrame(rows).sort_values("sample_id").reset_index(drop=True)


def build_summary(df):
    total = len(df)
    rows = []
    for field, col in FIELD_MAP.items():
        correct = int(df[col].sum())
        wrong   = total - correct
        acc     = round((correct / total) * 100, 1)
        rows.append({
            "field":        field,
            "correct":      correct,
            "wrong":        wrong,
            "total":        total,
            "accuracy_pct": acc,
            "status":       "PASS" if acc >= PASS_THRESHOLD else "FAIL",
        })
    return pd.DataFrame(rows)


def build_error_breakdown(df):
    rows = []
    for field, col in FIELD_MAP.items():
        for _, r in df[df[col] == False].iterrows():
            rows.append({
                "field":      field,
                "sample_id":  r["sample_id"],
                "headline":   r["headline"][:80],
                "llm_value":  r[COL_MAP[field]],
                "notes":      r["notes"],
            })
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════════
# PRINT REPORT
# ══════════════════════════════════════════════════════════════════════════════

def print_report(summary, df):
    total   = len(df)
    overall = round(df[list(FIELD_MAP.values())].values.mean() * 100, 1)

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


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json",          default=DEFAULT_JSON,
                        help="Path to LLM JSON output file")
    parser.add_argument("--export-labels", action="store_true",
                        help="Export ground truth labels to CSV and exit")
    args = parser.parse_args()

    if args.export_labels:
        export_labels()
        return

    if not os.path.exists(args.json):
        print(f"\n  ❌ JSON file not found: {args.json}\n")
        sys.exit(1)

    print(f"\n  Loading LLM outputs from : {args.json}")
    llm_records = load_json(args.json)
    print(f"  Loaded {len(llm_records)} records.")

    print(f"  Loading ground truth from: {LABELS_CSV}")
    labels_df = load_labels()

    df      = build_results(llm_records, labels_df)
    summary = build_summary(df)
    errors  = build_error_breakdown(df)

    results_path = f"{OUTPUT_DIR}/validation_results.csv"
    summary_path = f"{OUTPUT_DIR}/validation_summary.csv"
    errors_path  = f"{OUTPUT_DIR}/error_breakdown.csv"

    df.to_csv(results_path,  index=False)
    summary.to_csv(summary_path, index=False)
    errors.to_csv(errors_path,   index=False)

    print_report(summary, df)

    print(f"\n  Saved → {results_path}")
    print(f"  Saved → {summary_path}")
    print(f"  Saved → {errors_path}\n")


if __name__ == "__main__":
    main()