import json
from pydantic_settings import BaseSettings
from pydantic import field_validator

COINS = [
    "1000PEPEUSDT", "DOGEUSDT", "1000SHIBUSDT", "ADAUSDT",
    "TRXUSDT",      "ETHUSDT",  "POLUSDT",       "SUIUSDT",
    "LINKUSDT",     "SOLUSDT",  "XRPUSDT",       "DOTUSDT",
    "TONUSDT",      "ARBUSDT",  "AVAXUSDT",      "TAOUSDT",
    "NEARUSDT",     "BNBUSDT",
]

LABEL_MAP = {0: "SHORT", 1: "FLAT", 2: "LONG"}


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/tradingapp"

    TELEGRAM_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    BINANCE_API_KEY: str = ""
    BINANCE_SECRET: str = ""

    MODELS_DIR: str = "./models"
    # Mode: ensemble_v2 | lgbm_only | lstm_only
    ACTIVE_MODEL_VERSION: str = "ensemble_v2"

    CONFIDENCE_THRESHOLD: float = 0.60
    CONFIDENCE_FULL: float = 0.75

    # Di Railway: isi dengan URL frontend Railway Anda, contoh:
    # CORS_ORIGINS=["https://trading-frontend.up.railway.app","http://localhost:3000"]
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    COINS: list[str] = COINS

    # H4 candle count for swing point detection
    SWING_LOOKBACK: int = 20
    # ATR multiplier fallback for TP/SL
    ATR_TP_MULT: float = 2.0
    ATR_SL_MULT: float = 1.0

    class Config:
        env_file = ".env"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("COINS", mode="before")
    @classmethod
    def parse_coins(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


settings = Settings()
