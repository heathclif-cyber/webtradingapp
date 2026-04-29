# Models Directory

File model sudah tersedia (flat, tidak perlu subdirektori):

```
models/
├── lgbm_baseline.pkl       ← LightGBM classifier
├── lstm_best.pt            ← LSTM state dict (seq_len=32, hidden=128, layers=2)
├── lstm_scaler.pkl         ← StandardScaler untuk LSTM input
├── ensemble_meta.pkl       ← Stacking meta-learner (6 probs → 3 class probs)
├── calibrator.pkl          ← Probability calibrator
├── feature_cols_v2.json    ← 85 nama fitur (ordered)
├── shap_ranking.json       ← SHAP feature importance
├── model_registry.json     ← Daftar mode & active mode
└── inference_config.json   ← seq_len, threshold, arsitektur, backtest stats
```

## Mode Inference (Model Selector di UI)

| Mode          | Deskripsi                             | Active default |
|---------------|---------------------------------------|----------------|
| `ensemble_v2` | LGBM + LSTM → meta-learner + calibrator | Ya |
| `lgbm_only`   | Hanya LightGBM                        | -  |
| `lstm_only`   | Hanya LSTM                            | -  |

Switch mode via dropdown **Model Selector** di Navbar (kanan atas).

## Statistik Backtest (OOS 2025-05 → 2026-04)

- Mean Winrate: **77.18%**
- Avg Trades/Month: **39.46**
- Max Drawdown (3x lev): **14.45%**
- Max Consecutive Loss: **10**

## Coin List (18 pairs)

1000PEPEUSDT · DOGEUSDT · 1000SHIBUSDT · ADAUSDT · TRXUSDT · ETHUSDT ·
POLUSDT · SUIUSDT · LINKUSDT · SOLUSDT · XRPUSDT · DOTUSDT · TONUSDT ·
ARBUSDT · AVAXUSDT · TAOUSDT · NEARUSDT · BNBUSDT
