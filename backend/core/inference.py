"""
Loads models from the flat models/ directory based on model_registry.json.
Supports 3 inference modes: ensemble_v2 | lgbm_only | lstm_only.

File layout (all flat in models/):
  lgbm_baseline.pkl    — LightGBM classifier
  lstm_best.pt         — LSTM state dict
  lstm_scaler.pkl      — StandardScaler fitted on LSTM input
  ensemble_meta.pkl    — Stacking meta-learner (takes 6 probs → 3 class probs)
  calibrator.pkl       — Platt/Isotonic probability calibrator
  feature_cols_v2.json — Ordered list of 85 feature column names
  model_registry.json  — Available modes + active mode
  inference_config.json — seq_len, thresholds, architecture params
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from core.config import settings

logger = logging.getLogger(__name__)

LABEL_INV = {0: "SHORT", 1: "FLAT", 2: "LONG"}


# ── LSTM Architecture (must match training) ───────────────────────────────────

class LSTMClassifier(nn.Module):
    def __init__(self, input_size: int = 85, hidden_size: int = 128,
                 num_layers: int = 2, num_classes: int = 3, dropout: float = 0.3):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers,
                            batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_size, num_classes)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :])
        return self.fc(out)


# ── Shared asset bundle (loaded once from flat directory) ─────────────────────

class _Assets:
    """All model files loaded once, shared across mode switches."""

    def __init__(self, models_dir: Path, cfg: dict, skip_lstm: bool = False):
        arch = cfg["model_architecture"]
        inf  = cfg["inference"]

        self.seq_len     = inf["seq_len"]
        self.n_features  = arch["n_features"]
        self.device = torch.device("cpu")
        self.lstm = None

        # Feature names
        feat_path = models_dir / cfg["model_files"]["features"]
        self.feature_names: list[str] = json.loads(feat_path.read_text())

        # SHAP ranking
        shap_path = models_dir / "shap_ranking.json"
        raw_shap = json.loads(shap_path.read_text()) if shap_path.exists() else {}
        if raw_shap and "ranking" in raw_shap:
            symbol = raw_shap.get("symbol", "GLOBAL")
            self.shap_ranking = {
                symbol: [{"feature": r["feature"], "importance": r["mean_abs_shap"]}
                         for r in raw_shap["ranking"]]
            }
        else:
            self.shap_ranking = raw_shap

        # LightGBM
        with open(models_dir / cfg["model_files"]["lgbm"], "rb") as f:
            self.lgbm = pickle.load(f)

        # Scaler, meta-learner, calibrator
        with open(models_dir / cfg["model_files"]["scaler"], "rb") as f:
            self.scaler = pickle.load(f)
        with open(models_dir / cfg["model_files"]["meta"], "rb") as f:
            self.meta = pickle.load(f)
        with open(models_dir / cfg["model_files"]["calibrator"], "rb") as f:
            self.calibrator = pickle.load(f)

        # LSTM — skip when running lgbm_only to save memory
        if not skip_lstm:
            self.lstm = LSTMClassifier(
                input_size=arch["n_features"],
                hidden_size=arch["lstm_hidden"],
                num_layers=arch["lstm_layers"],
                dropout=arch["lstm_dropout"],
            )
            state = torch.load(
                models_dir / cfg["model_files"]["lstm"],
                map_location="cpu",
                weights_only=True,
            )
            self.lstm.load_state_dict(state)
            self.lstm.eval()

        logger.info(f"Assets loaded: {self.n_features} features, skip_lstm={skip_lstm}")


# ── Model Manager ─────────────────────────────────────────────────────────────

class ModelManager:
    _instance: Optional["ModelManager"] = None

    def __init__(self):
        self._models_dir = Path(settings.MODELS_DIR)
        self._cfg: Optional[dict] = None
        self._registry: Optional[dict] = None
        self._assets: Optional[_Assets] = None
        self._active_mode: str = settings.ACTIVE_MODEL_VERSION

    @classmethod
    def get(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = ModelManager()
        return cls._instance

    def _load_config(self) -> dict:
        if self._cfg is None:
            cfg_path = self._models_dir / "inference_config.json"
            self._cfg = json.loads(cfg_path.read_text())
        return self._cfg

    def _load_registry(self) -> dict:
        if self._registry is None:
            reg_path = self._models_dir / "model_registry.json"
            self._registry = json.loads(reg_path.read_text())
        return self._registry

    def _ensure_assets(self) -> _Assets:
        if self._assets is None:
            cfg = self._load_config()
            skip_lstm = self._active_mode == "lgbm_only"
            self._assets = _Assets(self._models_dir, cfg, skip_lstm=skip_lstm)
        return self._assets

    # ── Discovery ──────────────────────────────────────────────────────────

    def list_available(self) -> list[dict]:
        """Return list of model modes from model_registry.json."""
        try:
            reg = self._load_registry()
            active = self._active_mode or reg.get("active", "ensemble_v2")
            cfg = self._load_config()
            backtest = cfg.get("backtest_summary", {})
            per_coin = cfg.get("backtest_per_coin", {})
            result = []
            for mode, info in reg.get("models", {}).items():
                result.append({
                    "version": mode,
                    "path": str(self._models_dir),
                    "lgbm_ready": (self._models_dir / cfg["model_files"]["lgbm"]).exists(),
                    "lstm_ready": (self._models_dir / cfg["model_files"]["lstm"]).exists(),
                    "is_active": mode == active,
                    "description": (
                        f"Type: {info.get('type','?').upper()} · "
                        f"WR: {info.get('winrate', backtest.get('mean_winrate', 0)):.1%} · "
                        f"v{info.get('version','?')}"
                    ),
                    "trained_at": info.get("trained_date", cfg.get("created_at", "")[:10]),
                    "num_features": cfg["model_architecture"]["n_features"],
                    "coins": cfg["monitor"]["pairs"],
                })
            return result
        except Exception as e:
            logger.warning(f"list_available failed: {e}")
            return []

    def set_active(self, mode: str):
        reg = self._load_registry()
        if mode not in reg.get("models", {}):
            raise FileNotFoundError(f"Model mode '{mode}' not in model_registry.json")
        self._ensure_assets()  # validate files load
        self._active_mode = mode
        logger.info(f"Active model mode → {mode}")

    # ── Prediction ─────────────────────────────────────────────────────────

    def predict(self, features_df: pd.DataFrame,
                mode: Optional[str] = None) -> dict:
        """
        features_df: shape (N_recent_candles, 85), sorted oldest→newest.
        Returns per-class probabilities + ensemble blend.
        """
        assets = self._ensure_assets()
        active_mode = mode or self._active_mode

        # Align + fill missing feature columns
        features_df = _align_features(features_df, assets.feature_names)
        values = features_df.values.astype(np.float32)

        # ── LightGBM (single latest row) ───────────────────────────────────
        latest_row = values[-1:, :]
        lgbm_probs = assets.lgbm.predict_proba(latest_row)[0]   # shape (3,)

        # ── LSTM (skipped in lgbm_only mode to save memory) ───────────────
        lstm_probs = np.array([1/3, 1/3, 1/3], dtype=np.float32)  # fallback
        if assets.lstm is not None:
            scaled = assets.scaler.transform(values)
            seq = scaled[-assets.seq_len:, :]
            if len(seq) < assets.seq_len:
                pad = np.zeros((assets.seq_len - len(seq), seq.shape[1]), dtype=np.float32)
                seq = np.vstack([pad, seq])
            tensor = torch.tensor(seq, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                logits = assets.lstm(tensor)
                lstm_probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]

        # ── Ensemble / mode selection ───────────────────────────────────────
        if active_mode == "lgbm_only" or assets.lstm is None:
            raw_probs = lgbm_probs
        elif active_mode == "lstm_only":
            raw_probs = lstm_probs
        else:  # ensemble_v2
            meta_input = np.concatenate([lgbm_probs, lstm_probs]).reshape(1, -1)
            raw_probs = assets.meta.predict_proba(meta_input)[0]

        # ── Calibration ────────────────────────────────────────────────────
        try:
            cal_input = raw_probs.reshape(1, -1)
            ensemble_probs = assets.calibrator.predict_proba(cal_input)[0]
        except Exception:
            ensemble_probs = raw_probs

        predicted_class = int(np.argmax(ensemble_probs))
        confidence = float(ensemble_probs[predicted_class])

        return {
            "predicted_class": predicted_class,   # 0=SHORT, 1=FLAT, 2=LONG
            "confidence": confidence,
            "ensemble_probs": {
                "SHORT": float(ensemble_probs[0]),
                "FLAT":  float(ensemble_probs[1]),
                "LONG":  float(ensemble_probs[2]),
            },
            "lgbm_probs": {
                "SHORT": float(lgbm_probs[0]),
                "FLAT":  float(lgbm_probs[1]),
                "LONG":  float(lgbm_probs[2]),
            },
            "lstm_probs": {
                "SHORT": float(lstm_probs[0]),
                "FLAT":  float(lstm_probs[1]),
                "LONG":  float(lstm_probs[2]),
            },
            "model_version": active_mode,
        }

    def get_shap_for_coin(self, coin: str) -> list[dict]:
        assets = self._ensure_assets()
        data = assets.shap_ranking
        # Try exact match, then case-insensitive, then return global/first available
        if coin in data:
            return data[coin]
        for k, v in data.items():
            if k.upper() == coin.upper():
                return v
        # fallback: first available (global ranking)
        if data:
            return next(iter(data.values()))
        return []


def _align_features(df: pd.DataFrame, feature_names: list[str]) -> pd.DataFrame:
    """Ensure DataFrame has exactly the expected feature columns in order."""
    missing = [f for f in feature_names if f not in df.columns]
    if missing:
        for col in missing:
            df[col] = 0.0
    extra = [c for c in df.columns if c not in feature_names]
    if extra:
        df = df.drop(columns=extra)
    return df[feature_names]
