# Project Scaffold & Architecture

This file contains the core scaffolding and architecture of the Web Trading App. **All coding agents must read and understand this structure before making changes.**

## Struktur
`webtradingapp/`
├── `backend/`           (22 file Python)
│   ├── `main.py`                   FastAPI app + lifespan
│   ├── `core/`
│   │   ├── `config.py`             18 koin, thresholds dari inference_config
│   │   ├── `inference.py`  ★       Disesuaikan dgn model asli Anda
│   │   ├── `scorer.py`             Skor 1-100 dari probs + regime
│   │   ├── `paper_trader.py`       Open/close trade + PnL
│   │   └── `tp_sl_calculator.py`   H4 Swing Points / ATR fallback
│   ├── `db/`                       SQLAlchemy async + 4 tabel
│   ├── `api/routes.py`             14 endpoints + WebSocket
│   ├── `scheduler/cron.py`         APScheduler H1 inference cycle
│   ├── `ws/binance_monitor.py`     Live TP/SL monitor
│   └── `bot/telegram.py`           Alert signal + trade closed
│
├── `frontend/`          (21 file TypeScript/TSX)
│   ├── `pages/`
│   │   ├── `index.tsx`             Dashboard grid 18 koin + WS live
│   │   ├── `portfolio.tsx`         Stats + PnL chart + trade tables
│   │   └── `coin/[symbol].tsx`     Detail + prob bars + SHAP chart
│   └── `components/`
│       ├── `ModelSelector.tsx`  ★  Dropdown 3 mode (ensemble/lgbm/lstm)
│       ├── `CoinCard.tsx`          Score ring + badge + TP/SL
│       ├── `ShapChart.tsx`         Bar chart SHAP importance
│       └── `PnLChart.tsx`          Cumulative PnL area chart
│
├── `models/`            (file model Anda sudah ada ✓)
└── `docker-compose.yml`

## Model Selector (yang diminta)
Tersedia di Navbar kanan atas — menampilkan 3 mode:
- `ensemble_v2` — LGBM + LSTM → meta-learner + calibrator (default)
- `lgbm_only` — hanya LightGBM
- `lstm_only` — hanya LSTM

## Instruksi Penting (Satu-satunya yang perlu Anda lakukan)
Di `scheduler/cron.py` baris 46, sambungkan fungsi `engineer_features()` ke pipeline `03_engineer.py` Anda:
```python
# Ganti baris ini:
from pipeline.engineer import build_features
features_df = build_features(h1_df)
```

## Cara Jalankan

**1. Start PostgreSQL**
```bash
docker-compose up db -d
```

**2. Backend**
```bash
cd backend
cp .env.example .env  # isi DATABASE_URL, TELEGRAM_TOKEN, dll.
pip install -r requirements.txt
uvicorn main:app --reload
```

**3. Frontend**
```bash
cd frontend
npm install
npm run dev
```
