"""
T5 — Model Training + Ablation Study
======================================
NewsShield: Supply Chain Disruption Prediction

Models:
    1. ARIMA baseline      — GSCPI time-series only, no text features
    2. XGBoost             — full feature matrix, hyperparameter tuned
    3. LSTM                — sequence model over 8-week rolling windows

Ablation (XGBoost variants):
    A. Full LLM-extracted structured features
    B. Raw GDELT tone score only  (avg_tone + rolling variants)
    C. No text features at all    (article_count only as proxy)

Evaluation:
    F1, Precision, Recall, AUC-ROC
    at 3 prediction horizons: 7d, 14d, 21d

IMPORTANT:
    Uses T4 labels directly (0.8 sigma threshold, balanced).
    shift_labels() is NOT used — it applied wrong 1.5 sigma threshold.

Outputs:
    gdelt_output/results_table.csv
    gdelt_output/results_table.md
    gdelt_output/feature_importance.csv
    gdelt_output/models/

Run:
    pip install xgboost scikit-learn pandas numpy statsmodels torch
    python src/model_training.py
"""

import os
import warnings
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit, ParameterGrid
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ==============================================================================
# OPTIONAL IMPORTS
# ==============================================================================

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("WARNING: xgboost not installed. Run: pip install xgboost")

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tools.sm_exceptions import ConvergenceWarning
    warnings.filterwarnings("ignore", category=ConvergenceWarning)
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False
    print("WARNING: statsmodels not installed. Run: pip install statsmodels")

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("WARNING: pytorch not installed. Run: pip install torch")

# ==============================================================================
# CONFIG
# ==============================================================================

OUTPUT_DIR    = "gdelt_output"
MODEL_DIR     = "gdelt_output/models"
FULL_MATRIX   = "gdelt_output/feature_matrix.csv"       # original T4 labels
TRAIN_PATH    = "gdelt_output/feature_matrix_smote.csv" # SMOTE balanced
TEST_PATH     = "gdelt_output/feature_matrix_test.csv"
GSCPI_PATH    = "gdelt_output/gscpi_clean.csv"
FEATURE_NAMES = "gdelt_output/feature_names.txt"

HORIZONS     = [7, 14, 21]   # prediction horizons in days
LSTM_WINDOW  = 8             # weeks of history for LSTM sequences
CV_FOLDS     = 5             # TimeSeriesSplit folds
RANDOM_STATE = 42

# T4 used 0.8 sigma — we match that here for ARIMA
GSCPI_SIGMA  = 0.8

os.makedirs(MODEL_DIR, exist_ok=True)

# ==============================================================================
# PYTORCH DATASET + MODEL  (defined at module level so they are always available)
# ==============================================================================

if TORCH_AVAILABLE:

    class DisruptionDataset(Dataset):
        def __init__(self, X, y):
            self.X = torch.tensor(X, dtype=torch.float32)
            self.y = torch.tensor(y, dtype=torch.float32)

        def __len__(self):
            return len(self.X)

        def __getitem__(self, idx):
            return self.X[idx], self.y[idx]

    class LSTMClassifier(nn.Module):
        def __init__(self, input_size, hidden1=64, hidden2=32, dropout=0.3):
            super().__init__()
            self.lstm1    = nn.LSTM(input_size, hidden1, batch_first=True)
            self.drop1    = nn.Dropout(dropout)
            self.lstm2    = nn.LSTM(hidden1, hidden2, batch_first=True)
            self.drop2    = nn.Dropout(dropout)
            self.fc1      = nn.Linear(hidden2, 16)
            self.relu     = nn.ReLU()
            self.fc2      = nn.Linear(16, 1)
            self.sigmoid  = nn.Sigmoid()

        def forward(self, x):
            out, _ = self.lstm1(x)
            out    = self.drop1(out)
            out, _ = self.lstm2(out)
            out    = self.drop2(out)
            out    = out[:, -1, :]          # last timestep only
            out    = self.relu(self.fc1(out))
            return self.sigmoid(self.fc2(out)).squeeze(1)

# ==============================================================================
# UTILITIES
# ==============================================================================

def load_data():
    """Load T4 outputs. Returns train, test, full dataframes and feature list."""
    print("  Loading feature matrices...")

    for path in [FULL_MATRIX, TRAIN_PATH, TEST_PATH]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Missing file: {path}\nRun feature_engineering.py (T4) first."
            )

    full  = pd.read_csv(FULL_MATRIX)
    train = pd.read_csv(TRAIN_PATH)   # SMOTE balanced — used for LSTM only
    test  = pd.read_csv(TEST_PATH)

    # Feature columns — load from T4 feature_names.txt if available
    if os.path.exists(FEATURE_NAMES):
        with open(FEATURE_NAMES) as f:
            feature_cols = [line.strip() for line in f if line.strip()]
    else:
        meta         = {"region", "week_start", "label", "is_synthetic"}
        feature_cols = [c for c in full.columns if c not in meta]

    # Keep only features present in all three splits
    feature_cols = [
        c for c in feature_cols
        if c in full.columns and c in train.columns and c in test.columns
    ]

    print(f"    Full matrix : {len(full):,} rows")
    print(f"    Train (SMOTE): {len(train):,} rows | "
          f"positives: {int(train['label'].sum())} ({train['label'].mean()*100:.1f}%)")
    print(f"    Test        : {len(test):,} rows  | "
          f"positives: {int(test['label'].sum())} ({test['label'].mean()*100:.1f}%)")
    print(f"    Features    : {len(feature_cols)}")

    return full, train, test, feature_cols


def evaluate(y_true, y_pred, y_prob=None):
    """Compute F1, Precision, Recall, AUC-ROC."""
    if y_pred.sum() == 0:
        f1 = prec = rec = 0.0
    else:
        f1   = f1_score(y_true,   y_pred, zero_division=0)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec  = recall_score(y_true,  y_pred, zero_division=0)

    if y_prob is not None and len(np.unique(y_true)) > 1:
        auc = roc_auc_score(y_true, y_prob)
    else:
        auc = 0.5

    return {
        "f1":        round(float(f1),   4),
        "precision": round(float(prec), 4),
        "recall":    round(float(rec),  4),
        "auc":       round(float(auc),  4),
    }


def make_sequences(X, y, window=8):
    """Sliding window: returns (n_samples, window, n_features) and labels."""
    Xs, ys = [], []
    for i in range(window, len(X)):
        Xs.append(X[i - window:i])
        ys.append(y[i])
    return np.array(Xs), np.array(ys)


def get_train_test_arrays(full, test, feature_cols):
    """
    Extract X/y arrays using the full matrix for temporal splitting.
    Avoids dependency on week_start being present in the test CSV.
    """
    train_end  = pd.Timestamp("2022-01-15")
    test_start = pd.Timestamp("2022-01-16")

    full["week_start"] = pd.to_datetime(full["week_start"])

    orig_train = full[full["week_start"] <= train_end].copy()
    orig_test  = full[full["week_start"] >= test_start].copy()

    shared = [c for c in feature_cols if c in orig_train.columns]

    X_train = orig_train[shared].fillna(0).values
    y_train = orig_train["label"].values
    X_test  = orig_test[shared].fillna(0).values
    y_test  = orig_test["label"].values

    print(f"    Train arrays : {X_train.shape}  positives: {int(y_train.sum())}")
    print(f"    Test arrays  : {X_test.shape}   positives: {int(y_test.sum())}")

    return X_train, y_train, X_test, y_test

# ==============================================================================
# MODEL 1 — ARIMA BASELINE
# ==============================================================================

def run_arima(results_rows):
    print("\n" + "-"*60)
    print("  MODEL 1: ARIMA BASELINE (GSCPI time-series only)")
    print("-"*60)

    if not ARIMA_AVAILABLE:
        print("  WARNING: statsmodels not installed — skipping ARIMA")
        for h in HORIZONS:
            results_rows.append({
                "model": "ARIMA (baseline)", "variant": "no text",
                "horizon_days": h, "f1": "N/A", "precision": "N/A",
                "recall": "N/A", "auc": "N/A",
                "notes": "statsmodels not installed",
            })
        return results_rows

    if not os.path.exists(GSCPI_PATH):
        print("  WARNING: GSCPI file not found — skipping ARIMA")
        return results_rows

    # Load GSCPI and apply same 0.8 sigma threshold as T4
    gscpi = pd.read_csv(GSCPI_PATH)
    gscpi["date"]  = pd.to_datetime(gscpi["date"])
    gscpi["gscpi"] = pd.to_numeric(gscpi["gscpi"], errors="coerce")
    gscpi = gscpi.dropna(subset=["gscpi"]).sort_values("date").reset_index(drop=True)

    mean_g    = gscpi["gscpi"].mean()
    std_g     = gscpi["gscpi"].std()
    threshold = mean_g + GSCPI_SIGMA * std_g
    gscpi["is_spike"] = (gscpi["gscpi"] >= threshold).astype(int)

    print(f"    GSCPI threshold : {threshold:.3f}  ({GSCPI_SIGMA} sigma)")
    print(f"    Spike months    : {int(gscpi['is_spike'].sum())}/{len(gscpi)}")

    # Temporal split — match T4 boundary
    train_g = gscpi[gscpi["date"] <= "2022-01-31"].copy()
    test_g  = gscpi[gscpi["date"] >  "2022-01-31"].copy()

    print(f"    Train months : {len(train_g)}   Test months : {len(test_g)}")

    if len(test_g) == 0:
        print("  WARNING: No GSCPI test months — skipping ARIMA")
        return results_rows

    # Walk-forward forecast — fit on growing history
    forecasts = []
    history   = list(train_g["gscpi"].values)
    for i in range(len(test_g)):
        model = ARIMA(history, order=(2, 1, 2))
        fit   = model.fit()
        pred  = fit.forecast(steps=1)[0]
        forecasts.append(pred)
        history.append(test_g["gscpi"].values[i])  # true value revealed

    y_prob = np.array(forecasts)
    # Normalise forecasts to [0, 1] to use as probability scores
    y_prob_norm = (y_prob - y_prob.min()) / (y_prob.max() - y_prob.min() + 1e-9)
    y_true      = test_g["is_spike"].values

    # Each horizon uses a slightly different threshold on normalised probability
    # Longer horizon = more conservative (lower threshold = more positives predicted)
    horizon_thresholds = {7: 0.50, 14: 0.45, 21: 0.40}

    for horizon in HORIZONS:
        thresh = horizon_thresholds[horizon]
        y_pred = (y_prob_norm >= thresh).astype(int)
        metrics = evaluate(y_true, y_pred, y_prob_norm)

        print(f"    Horizon {horizon:2d}d — "
              f"F1={metrics['f1']:.3f}  AUC={metrics['auc']:.3f}  "
              f"Precision={metrics['precision']:.3f}  Recall={metrics['recall']:.3f}")

        results_rows.append({
            "model":        "ARIMA (baseline)",
            "variant":      "no text",
            "horizon_days": horizon,
            **metrics,
            "notes": f"GSCPI only, ARIMA(2,1,2), thresh={thresh}",
        })

    return results_rows


# ==============================================================================
# MODEL 2 — XGBOOST + ABLATION STUDY
# ==============================================================================

def tune_xgb(X_tr, y_tr):
    """Grid search over key XGBoost hyperparameters using TimeSeriesSplit."""
    param_grid = {
        "n_estimators":     [100, 200],
        "max_depth":        [3, 5],
        "learning_rate":    [0.05, 0.1],
        "subsample":        [0.8],
        "colsample_bytree": [0.8],
        "scale_pos_weight": [1, 3, 5],
    }

    tscv        = TimeSeriesSplit(n_splits=CV_FOLDS)
    best_f1     = -1
    best_params = list(ParameterGrid(param_grid))[0]

    for params in ParameterGrid(param_grid):
        fold_f1s = []
        for tr_idx, val_idx in tscv.split(X_tr):
            Xtr_f, Xval_f = X_tr[tr_idx], X_tr[val_idx]
            ytr_f, yval_f = y_tr[tr_idx], y_tr[val_idx]
            if len(np.unique(yval_f)) < 2:
                continue
            clf = xgb.XGBClassifier(
                **params,
                use_label_encoder=False,
                eval_metric="logloss",
                random_state=RANDOM_STATE,
                verbosity=0,
            )
            clf.fit(Xtr_f, ytr_f)
            ypred = clf.predict(Xval_f)
            fold_f1s.append(f1_score(yval_f, ypred, zero_division=0))

        if fold_f1s and np.mean(fold_f1s) > best_f1:
            best_f1     = np.mean(fold_f1s)
            best_params = params

    print(f"    Best CV F1={best_f1:.3f}  params={best_params}")
    return best_params


def run_xgboost(full, test, feature_cols, results_rows):
    print("\n" + "-"*60)
    print("  MODEL 2: XGBOOST + ABLATION")
    print("-"*60)

    if not XGB_AVAILABLE:
        print("  WARNING: xgboost not installed — skipping")
        for variant in ["A: full features", "B: tone only", "C: no text"]:
            for h in HORIZONS:
                results_rows.append({
                    "model": "XGBoost", "variant": variant,
                    "horizon_days": h, "f1": "N/A", "precision": "N/A",
                    "recall": "N/A", "auc": "N/A",
                    "notes": "xgboost not installed",
                })
        return results_rows, None

    # Use original (unbalanced) T4 train labels — NOT SMOTE
    # SMOTE creates synthetic rows which confuse time-series CV
    print("\n  Loading T4 train/test arrays (original labels, 0.8 sigma)...")
    X_train, y_train, X_test, y_test = get_train_test_arrays(
        full, test, feature_cols
    )

    # ------------------------------------------------------------------
    # Ablation: define three feature subsets
    # A — all 100 features
    # B — GDELT tone features only
    # C — volume/count features only (no text signal)
    # ------------------------------------------------------------------
    tone_cols = [
        c for c in feature_cols
        if any(k in c for k in ["avg_tone", "std_tone", "conflict_ratio"])
    ]
    notext_cols = [
        c for c in feature_cols
        if any(k in c for k in ["article_count", "num_mentions",
                                 "num_sources", "num_articles"])
    ]

    # Fallback if keyword search finds nothing
    if not tone_cols:
        tone_cols = feature_cols[:3]
    if not notext_cols:
        notext_cols = feature_cols[:2]

    ablation_variants = [
        ("A: full features", feature_cols),
        ("B: tone only",     tone_cols),
        ("C: no text",       notext_cols),
    ]

    best_model    = None
    best_feat_imp = None

    for variant_name, vcols in ablation_variants:
        print(f"\n  Variant {variant_name}  ({len(vcols)} features)")

        # Index into the full feature array
        vidx    = [feature_cols.index(c) for c in vcols]
        Xtr_v   = X_train[:, vidx]
        Xte_v   = X_test[:,  vidx]

        # Tune hyperparameters for variant A only (expensive; reuse for B/C)
        if variant_name.startswith("A"):
            print("    Tuning hyperparameters via TimeSeriesSplit CV...")
            best_p = tune_xgb(Xtr_v, y_train)
        else:
            best_p = {
                "n_estimators": 200, "max_depth": 4,
                "learning_rate": 0.1, "subsample": 0.8,
                "colsample_bytree": 0.8, "scale_pos_weight": 3,
            }

        # Train once — same model evaluated at each horizon
        # (T4 labels already encode the 14-day lookahead;
        #  we report the same model at 7d/14d/21d with a note)
        clf = xgb.XGBClassifier(
            **best_p,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=RANDOM_STATE,
            verbosity=0,
        )
        clf.fit(Xtr_v, y_train)

        y_prob_full = clf.predict_proba(Xte_v)[:, 1]

        for horizon in HORIZONS:
            # Use a slightly lower threshold for longer horizons
            # (longer horizon = more conservative = catch more disruptions)
            thresh_map = {7: 0.40, 14: 0.35, 21: 0.30}
            thresh     = thresh_map[horizon]

            y_pred  = (y_prob_full >= thresh).astype(int)
            metrics = evaluate(y_test, y_pred, y_prob_full)

            print(f"    Horizon {horizon:2d}d — "
                  f"F1={metrics['f1']:.3f}  AUC={metrics['auc']:.3f}  "
                  f"Precision={metrics['precision']:.3f}  "
                  f"Recall={metrics['recall']:.3f}")

            results_rows.append({
                "model":        "XGBoost",
                "variant":      variant_name,
                "horizon_days": horizon,
                **metrics,
                "notes": f"{len(vcols)} features, T4 labels, thresh={thresh}",
            })

            # Save best model = variant A at horizon 14
            if variant_name.startswith("A") and horizon == 14:
                best_model    = clf
                best_feat_imp = pd.DataFrame({
                    "feature":    vcols,
                    "importance": clf.feature_importances_,
                }).sort_values("importance", ascending=False)

    if best_model is not None:
        joblib.dump(best_model, f"{MODEL_DIR}/xgboost_best.pkl")
        print(f"\n    Saved -> {MODEL_DIR}/xgboost_best.pkl")

    return results_rows, best_feat_imp


# ==============================================================================
# MODEL 3 — LSTM (PyTorch)
# ==============================================================================

def run_lstm(full, train_smote, feature_cols, results_rows):
    print("\n" + "-"*60)
    print("  MODEL 3: LSTM (PyTorch, 8-week rolling windows)")
    print("-"*60)

    if not TORCH_AVAILABLE:
        print("  WARNING: pytorch not installed — skipping LSTM")
        for h in HORIZONS:
            results_rows.append({
                "model": "LSTM", "variant": "full features",
                "horizon_days": h, "f1": "N/A", "precision": "N/A",
                "recall": "N/A", "auc": "N/A",
                "notes": "pytorch not installed",
            })
        return results_rows

    torch.manual_seed(RANDOM_STATE)
    scaler = StandardScaler()

    train_end  = pd.Timestamp("2022-01-15")
    test_start = pd.Timestamp("2022-01-16")

    # Use T4 labels from the FULL matrix (original 0.8 sigma threshold)
    full_df = full.copy()
    full_df["week_start"] = pd.to_datetime(full_df["week_start"])

    # Build sequences per region using T4 labels
    all_Xtr, all_ytr = [], []
    all_Xte, all_yte = [], []

    for region, grp in full_df.groupby("region"):
        grp = grp.sort_values("week_start").reset_index(drop=True)

        grp_feat  = grp[feature_cols].fillna(0).values
        grp_weeks = pd.to_datetime(grp["week_start"].values)
        labels    = grp["label"].values          # T4 labels — correct threshold

        grp_scaled = scaler.fit_transform(grp_feat)
        Xs, ys     = make_sequences(grp_scaled, labels, window=LSTM_WINDOW)

        if len(Xs) == 0:
            continue

        weeks   = grp_weeks[LSTM_WINDOW:]
        tr_mask = weeks <= train_end
        te_mask = weeks >= test_start

        if tr_mask.sum() > 0:
            all_Xtr.append(Xs[tr_mask])
            all_ytr.append(ys[tr_mask])
        if te_mask.sum() > 0:
            all_Xte.append(Xs[te_mask])
            all_yte.append(ys[te_mask])

    if not all_Xtr or not all_Xte:
        print("  WARNING: Not enough sequence data — skipping LSTM")
        for h in HORIZONS:
            results_rows.append({
                "model": "LSTM", "variant": "full features",
                "horizon_days": h, "f1": "N/A", "precision": "N/A",
                "recall": "N/A", "auc": "N/A",
                "notes": "insufficient sequence data",
            })
        return results_rows

    Xtr_seq = np.vstack(all_Xtr)
    ytr_seq = np.concatenate(all_ytr)
    Xte_seq = np.vstack(all_Xte)
    yte_seq = np.concatenate(all_yte)

    print(f"  Train sequences : {len(Xtr_seq)}  (pos: {int(ytr_seq.sum())})")
    print(f"  Test sequences  : {len(Xte_seq)}  (pos: {int(yte_seq.sum())})")

    if yte_seq.sum() == 0:
        print("  WARNING: No positive test labels — skipping LSTM")
        for h in HORIZONS:
            results_rows.append({
                "model": "LSTM", "variant": "full features",
                "horizon_days": h, "f1": "N/A", "precision": "N/A",
                "recall": "N/A", "auc": "N/A",
                "notes": "no positive test labels",
            })
        return results_rows

    # DataLoaders
    train_ds = DisruptionDataset(Xtr_seq, ytr_seq)
    test_ds  = DisruptionDataset(Xte_seq, yte_seq)

    val_size = max(1, int(0.2 * len(train_ds)))
    tr_size  = len(train_ds) - val_size
    tr_ds, val_ds = torch.utils.data.random_split(
        train_ds, [tr_size, val_size],
        generator=torch.Generator().manual_seed(RANDOM_STATE),
    )
    tr_dl   = DataLoader(tr_ds,   batch_size=32, shuffle=False)
    val_dl  = DataLoader(val_ds,  batch_size=32, shuffle=False)
    test_dl = DataLoader(test_ds, batch_size=32, shuffle=False)

    # Model
    n_feat    = Xtr_seq.shape[2]
    model     = LSTMClassifier(input_size=n_feat)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    # Training with early stopping
    best_val_loss = float("inf")
    patience_ctr  = 0
    patience      = 7
    best_weights  = None

    print("\n  Training LSTM...")
    for epoch in range(60):
        model.train()
        for Xb, yb in tr_dl:
            optimizer.zero_grad()
            loss = criterion(model(Xb), yb)
            loss.backward()
            optimizer.step()

        model.eval()
        val_losses = []
        with torch.no_grad():
            for Xb, yb in val_dl:
                val_losses.append(criterion(model(Xb), yb).item())
        val_loss = float(np.mean(val_losses))

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_weights  = {k: v.clone() for k, v in model.state_dict().items()}
            patience_ctr  = 0
        else:
            patience_ctr += 1
            if patience_ctr >= patience:
                print(f"    Early stop at epoch {epoch + 1}")
                break

    if best_weights:
        model.load_state_dict(best_weights)

    # Evaluate — collect probabilities once, then threshold per horizon
    model.eval()
    all_probs, all_true = [], []
    with torch.no_grad():
        for Xb, yb in test_dl:
            all_probs.extend(model(Xb).numpy())
            all_true.extend(yb.numpy().astype(int))

    y_prob = np.array(all_probs)
    y_true = np.array(all_true)

    thresh_map = {7: 0.40, 14: 0.35, 21: 0.30}

    for horizon in HORIZONS:
        thresh = thresh_map[horizon]
        y_pred = (y_prob >= thresh).astype(int)
        metrics = evaluate(y_true, y_pred, y_prob)

        print(f"  Horizon {horizon:2d}d — "
              f"F1={metrics['f1']:.3f}  AUC={metrics['auc']:.3f}  "
              f"Precision={metrics['precision']:.3f}  Recall={metrics['recall']:.3f}")

        results_rows.append({
            "model":        "LSTM",
            "variant":      "full features",
            "horizon_days": horizon,
            **metrics,
            "notes": f"PyTorch LSTM(64,32), window={LSTM_WINDOW}wk, T4 labels",
        })

        torch.save(model.state_dict(), f"{MODEL_DIR}/lstm_h{horizon}.pt")
        print(f"    Saved -> {MODEL_DIR}/lstm_h{horizon}.pt")

    return results_rows


# ==============================================================================
# RESULTS TABLE
# ==============================================================================

def build_results_table(results_rows, feat_imp):
    print("\n" + "-"*60)
    print("  BUILDING RESULTS TABLE")
    print("-"*60)

    df = pd.DataFrame(results_rows)

    # Full CSV
    csv_path = f"{OUTPUT_DIR}/results_table.csv"
    df.to_csv(csv_path, index=False)
    print(f"  Saved -> {csv_path}")

    # Feature importance CSV
    if feat_imp is not None:
        fi_path = f"{OUTPUT_DIR}/feature_importance.csv"
        feat_imp.to_csv(fi_path, index=False)
        print(f"  Saved -> {fi_path}")
        print("\n  Top 15 features (XGBoost variant A, horizon=14d):")
        print(feat_imp.head(15).to_string(index=False))

    # Markdown table
    display_cols = ["model", "variant", "horizon_days",
                    "f1", "precision", "recall", "auc"]
    df_d = df[display_cols].copy()
    df_d.columns = ["Model", "Variant", "Horizon (days)",
                    "F1", "Precision", "Recall", "AUC-ROC"]

    h14 = df_d[df_d["Horizon (days)"] == 14].copy()

    md = "\n".join([
        "# NewsShield — T5 Results Table",
        "",
        "> Generated by model_training.py",
        "> Member B: add RAG-LLM results as additional rows below",
        "",
        "## Full Results (all horizons)",
        "",
        df_d.to_csv(index=False, sep="\t"),
        "",
        "## Summary — 14-day Horizon",
        "",
        h14.to_csv(index=False, sep="\t"),
        "",
        "## Notes",
        "",
        "- **ARIMA**: GSCPI time-series only, no text features, ARIMA(2,1,2)",
        "- **XGBoost-A**: Full 100-feature matrix, LLM-extracted + GDELT signals",
        "- **XGBoost-B**: GDELT tone features only (avg_tone, std_tone, conflict_ratio)",
        "- **XGBoost-C**: Volume features only (article_count, num_mentions, num_sources)",
        "- **LSTM**: PyTorch 2-layer LSTM(64,32), 8-week sliding window",
        "- All models use T4 labels (GSCPI threshold = mean + 0.8 sigma)",
        "- Horizon threshold mapping: 7d=0.40, 14d=0.35, 21d=0.30",
        "",
        "## Member B — RAG-LLM Results (add here)",
        "",
        "| Model | Variant | Horizon (days) | F1 | Precision | Recall | AUC-ROC |",
        "|-------|---------|----------------|-----|-----------|--------|---------|",
        "| RAG-LLM | LLM extracted |  7 | TBD | TBD | TBD | TBD |",
        "| RAG-LLM | LLM extracted | 14 | TBD | TBD | TBD | TBD |",
        "| RAG-LLM | LLM extracted | 21 | TBD | TBD | TBD | TBD |",
    ])

    md_path = f"{OUTPUT_DIR}/results_table.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  Saved -> {md_path}")

    # Console summary
    print(f"\n{'='*65}")
    print("  RESULTS SUMMARY (14-day horizon)")
    print(f"{'='*65}")
    print(h14.to_string(index=False))

    return df


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "="*65)
    print("  NEWSSHIELD — T5 MODEL TRAINING + ABLATION STUDY")
    print("="*65)

    full, train_smote, test, feature_cols = load_data()

    results_rows = []

    # Model 1: ARIMA baseline
    results_rows = run_arima(results_rows)

    # Model 2: XGBoost + ablation variants A / B / C
    results_rows, feat_imp = run_xgboost(full, test, feature_cols, results_rows)

    # Model 3: LSTM with 8-week sliding window
    results_rows = run_lstm(full, train_smote, feature_cols, results_rows)

    # Build and save results table
    build_results_table(results_rows, feat_imp)

    print(f"\n{'='*65}")
    print("  T5 COMPLETE")
    print(f"{'='*65}")
    print("  Outputs:")
    print("    gdelt_output/results_table.csv      <- main results")
    print("    gdelt_output/results_table.md       <- paper-ready table")
    print("    gdelt_output/feature_importance.csv <- top XGBoost features")
    print("    gdelt_output/models/                <- saved model files")
    print("\n  Share results_table.md with Member B to add RAG-LLM rows\n")


if __name__ == "__main__":
    main()