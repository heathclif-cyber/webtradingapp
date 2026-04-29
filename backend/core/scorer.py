"""
Converts model probabilities + trend regime into a 1-100 score per coin.

Score breakdown:
  - Base confidence (0-70 pts): ensemble probability of predicted direction
  - Trend alignment (0-20 pts): how well the signal aligns with H1/H4 trend
  - Signal strength bonus (0-10 pts): LONG/SHORT get bonus vs FLAT
"""

import numpy as np


LABEL_MAP = {0: "SHORT", 1: "FLAT", 2: "LONG"}
DIRECTION_COLORS = {
    "LONG": "green",
    "SHORT": "red",
    "FLAT": "neutral",
}


def compute_score(
    ensemble_probs: dict,        # {"SHORT": float, "FLAT": float, "LONG": float}
    predicted_class: int,        # 0=SHORT, 1=FLAT, 2=LONG
    trend_strength: float = 0.5, # 0.0 (strong bear) → 1.0 (strong bull)
    regime: str = "NEUTRAL",     # "BULLISH" | "BEARISH" | "NEUTRAL"
) -> int:
    """Returns an integer score 1–100."""

    confidence = ensemble_probs[LABEL_MAP[predicted_class]]
    direction = LABEL_MAP[predicted_class]

    # Base: 0-70 pts from confidence
    base = confidence * 70

    # Trend alignment: 0-20 pts
    if direction == "LONG":
        trend_pts = trend_strength * 20
    elif direction == "SHORT":
        trend_pts = (1.0 - trend_strength) * 20
    else:  # FLAT
        neutrality = 1.0 - abs(trend_strength - 0.5) * 2
        trend_pts = neutrality * 10

    # Regime bonus: 0-10 pts
    regime_bonus = 0
    if (direction == "LONG" and regime == "BULLISH") or \
       (direction == "SHORT" and regime == "BEARISH"):
        regime_bonus = 10
    elif direction != "FLAT" and regime == "NEUTRAL":
        regime_bonus = 5

    raw = base + trend_pts + regime_bonus
    score = int(np.clip(round(raw), 1, 100))
    return score


def classify_score(score: int) -> str:
    """Human-readable tier for UI badge."""
    if score >= 80:
        return "STRONG"
    if score >= 60:
        return "MODERATE"
    if score >= 40:
        return "WEAK"
    return "FLAT"


def score_color(score: int, direction: str) -> str:
    if direction == "FLAT":
        return "neutral"
    if score >= 70:
        return "green" if direction == "LONG" else "red"
    if score >= 45:
        return "yellow"
    return "neutral"
