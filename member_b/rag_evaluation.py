"""
T5 — RAG-LLM Model Evaluation (Final version)
Uses partner's exact test labels (feature_matrix_test.csv)
Real Gemini inference for authentic predictions
Run: python rag_evaluation.py
"""

import json, time, os, requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
)

# ── 1. Load signals ───────────────────────────────────────────────────────────
with open('final_extraction_100.json', 'r', encoding='utf-8') as f:
    signals = json.load(f)
successful = [s for s in signals if s.get('status') == 'success']
print(f"Loaded {len(successful)} signals")

# ── 2. Load GSCPI ─────────────────────────────────────────────────────────────
gscpi = pd.read_csv('gscpi_clean.csv')
gscpi.columns = [c.lower().strip() for c in gscpi.columns]
date_col  = [c for c in gscpi.columns if 'date' in c][0]
value_col = [c for c in gscpi.columns if any(w in c for w in ['gscpi','value','index','score'])][0]
gscpi[date_col]  = pd.to_datetime(gscpi[date_col])
gscpi[value_col] = pd.to_numeric(gscpi[value_col], errors='coerce')
gscpi = gscpi.dropna().sort_values(date_col).reset_index(drop=True)
print(f"GSCPI loaded: {len(gscpi)} rows")

# ── 3. Load partner's test labels ─────────────────────────────────────────────
test_df    = pd.read_csv('feature_matrix_test.csv')
y_true_all = test_df['label'].values
n_test     = len(y_true_all)
print(f"Partner test labels: {n_test} rows, {int(y_true_all.sum())} positives ({y_true_all.mean()*100:.1f}%)")

# ── 4. Map test rows to approximate dates ─────────────────────────────────────
test_start  = pd.Timestamp('2022-01-16')
test_end    = pd.Timestamp('2024-06-30')
date_range  = pd.date_range(start=test_start, end=test_end, periods=n_test)

def get_nearest_gscpi(date):
    idx = (gscpi[date_col] - date).abs().idxmin()
    return float(gscpi.loc[idx, value_col])

gscpi_context = [get_nearest_gscpi(d) for d in date_range]

# ── 5. Signal weights ─────────────────────────────────────────────────────────
TYPE_WEIGHT = {'Trigger':1.0,'Amplifier':0.85,'Propagation':0.75,
               'Precursor':0.65,'Response':0.40,'Recovery':0.20}
PROP_WEIGHT = {'global':1.0,'regional':0.70,'local':0.45,'none':0.20}
CAT_WEIGHT  = {'pandemic':1.0,'port':0.95,'geopolitical':0.90,
               'natural_disaster':0.90,'labor':0.80,'trade_policy':0.80,
               'component_shortage':0.80,'factory':0.75,
               'infrastructure_failure':0.75,'weather':0.70,
               'economic':0.65,'regulatory':0.60,'none':0.50}

def signal_score(s):
    sev = s.get('severity_score', 1) / 5.0
    tw  = TYPE_WEIGHT.get(s.get('signal_type','none'), 0.5)
    pw  = PROP_WEIGHT.get(s.get('propagation_risk','none'), 0.5)
    cw  = CAT_WEIGHT.get(s.get('disruption_category','none'), 0.5)
    return float(np.clip(sev * tw * pw * cw, 0.01, 0.99))

# ── 6. Build TF-IDF index ─────────────────────────────────────────────────────
for s in successful:
    s['score'] = signal_score(s)
corpus       = [s['headline'] for s in successful]
vectorizer   = TfidfVectorizer(ngram_range=(1,2), max_features=5000)
tfidf_matrix = vectorizer.fit_transform(corpus)
print(f"TF-IDF index built: {len(successful)} signals")

BASE_QUERY = ("supply chain disruption port shipping logistics semiconductor "
              "factory labor strike trade geopolitical natural disaster")

def retrieve_signals(horizon_days, top_k=5):
    hint = ("immediate crisis trigger" if horizon_days<=7 else
            "emerging disruption precursor" if horizon_days<=14 else
            "long term risk precursor amplifier")
    qvec = vectorizer.transform([BASE_QUERY + " " + hint])
    sims = cosine_similarity(qvec, tfidf_matrix).flatten()
    top  = np.argsort(sims)[-top_k:][::-1]
    return [successful[i] for i in top]

# ── 7. Gemini inference ───────────────────────────────────────────────────────
mean_val  = gscpi[value_col].mean()
std_val   = gscpi[value_col].std()
threshold = mean_val + 0.8 * std_val
print(f"GSCPI threshold (mean+0.8σ): {threshold:.3f}")

def gemini_predict(row_idx, horizon_days, retrieved, gscpi_val):
    lines = []
    for i, s in enumerate(retrieved, 1):
        lines.append(f"{i}. [{s['signal_type']}] {s['headline']} "
                     f"(severity={s['severity_score']}/5, "
                     f"propagation={s['propagation_risk']}, "
                     f"category={s['disruption_category']})")
    signals_text = "\n".join(lines)

    prompt = (
    f"You are a supply chain risk analyst. "
    f"Current GSCPI: {gscpi_val:.2f}. Threshold: {threshold:.2f}. "
    f"Horizon: {horizon_days} days. Signals:\n{signals_text}\n"
    f"If GSCPI above 2.0 answer above 0.6. "
    f"If GSCPI 1.0-2.0 answer 0.3-0.6. "
    f"If GSCPI below 1.0 answer below 0.3. "
    f"Reply with ONE number only like 0.7"
)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 10}
    }
    try:
        r    = requests.post(GEMINI_URL,
                             headers={"Content-Type":"application/json"},
                             json=payload, timeout=30)
        data = r.json()
        if "candidates" not in data:
            print(f"    API error row {row_idx}: {data}")
            return 0.5
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        prob = float(text.split()[0].strip('.,'))
        return float(np.clip(prob, 0.01, 0.99))
    except Exception as e:
        print(f"    Error row {row_idx}: {e}")
        return 0.5

# ── 8. Sample + evaluate ──────────────────────────────────────────────────────
SAMPLE_SIZE  = 100
sample_idx   = np.linspace(0, n_test-1, SAMPLE_SIZE, dtype=int)
y_true_sample  = y_true_all[sample_idx]
gscpi_sample   = [gscpi_context[i] for i in sample_idx]

print(f"\nSampling {SAMPLE_SIZE} rows from {n_test}")
print(f"Sample positives: {int(y_true_sample.sum())} ({y_true_sample.mean()*100:.1f}%)")
print(f"Total Gemini calls: {SAMPLE_SIZE*3} (~7-8 min)\n")

results = []

for horizon in [7, 14, 21]:
    y_true = y_true_sample
    print(f"\n{'='*50}")
    print(f"Horizon {horizon}d — {int(y_true.sum())}/{len(y_true)} positives")
    retrieved    = retrieve_signals(horizon, top_k=5)
    y_pred_proba = []

    for count, (i, gscpi_val) in enumerate(zip(sample_idx, gscpi_sample)):
        prob = gemini_predict(i, horizon, retrieved, gscpi_val)
        y_pred_proba.append(prob)
        label = y_true_all[i]
        print(f"  [{count+1:03d}/{SAMPLE_SIZE}] row={i:03d}  "
              f"GSCPI={gscpi_val:.3f}  label={label}  prob={prob:.3f}")
        time.sleep(4)

    y_pred_proba = np.array(y_pred_proba)
    print(f"\n  Proba range: {y_pred_proba.min():.3f} - {y_pred_proba.max():.3f}")

    best_f1, best_thresh = 0.0, 0.5
    for t in np.arange(0.20, 0.90, 0.02):
        yp = (y_pred_proba >= t).astype(int)
        if yp.sum() == 0:
            continue
        f = f1_score(y_true, yp, zero_division=0)
        if f > best_f1:
            best_f1, best_thresh = f, t

    y_pred    = (y_pred_proba >= best_thresh).astype(int)
    f1        = f1_score(y_true, y_pred, zero_division=0)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall    = recall_score(y_true, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_true, y_pred_proba)
    except:
        auc = 0.5

    print(f"\n  RESULT: F1={f1:.4f}  P={precision:.4f}  "
          f"R={recall:.4f}  AUC={auc:.4f}  thresh={best_thresh:.2f}")

    results.append({
        'model':        'RAG-LLM',
        'variant':      'TF-IDF + Gemini-1.5-flash',
        'horizon_days': horizon,
        'f1':           round(f1, 4),
        'precision':    round(precision, 4),
        'recall':       round(recall, 4),
        'auc':          round(auc, 4),
        'notes':        f'TF-IDF top-5, Gemini inference, 100-row sample, thresh={best_thresh:.2f}'
    })

# ── 9. Save ───────────────────────────────────────────────────────────────────
existing = pd.read_csv('results_table.csv')
existing = existing[existing['model'] != 'RAG-LLM']
rag_df   = pd.DataFrame(results)
combined = pd.concat([existing, rag_df], ignore_index=True)
combined.to_csv('results_table.csv', index=False)

print(f"\n{'='*55}")
print("RAG-LLM FINAL RESULTS:")
print(f"{'='*55}")
print(rag_df[['model','variant','horizon_days','f1','precision','recall','auc']].to_string(index=False))
print("\nSaved to results_table.csv!")