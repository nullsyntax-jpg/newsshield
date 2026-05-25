"""
app/core/model_loader.py
------------------------
Loads XGBoost and LSTM models once at startup and caches them.
"""

import joblib
import torch
import torch.nn as nn
from pathlib import Path
from functools import lru_cache
from app.core.config import settings

# ── LSTM Architecture (must match training code) ─────────────────────────────
class LSTMModel(nn.Module):
    def __init__(self, input_size=100, hidden_size=64, num_layers=2, output_size=1):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return self.sigmoid(out)


@lru_cache(maxsize=1)
def load_xgboost():
    path = Path(settings.MODEL_DIR) / "models" / "xgboost_best.pkl"
    if not path.exists():
        raise FileNotFoundError(f"XGBoost model not found at {path}")
    return joblib.load(path)


@lru_cache(maxsize=3)
def load_lstm(horizon: int):
    """Load LSTM model for a specific horizon (7, 14, or 21 days)."""
    path = Path(settings.MODEL_DIR) / "models" / f"lstm_h{horizon}.pt"
    if not path.exists():
        raise FileNotFoundError(f"LSTM model not found at {path}")
    model = LSTMModel(input_size=100)
    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()
    return model


def invalidate_model_cache():
    load_xgboost.cache_clear()
    load_lstm.cache_clear()