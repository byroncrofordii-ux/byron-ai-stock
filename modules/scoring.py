"""B.Y.R.O.N. stock scoring and signal functions."""

import pandas as pd


def calculate_stock_score(
    current_price: float,
    average_20: float,
    average_50: float,
    rsi: float,
    recent_return: float,
) -> dict:
    """
    Calculate the B.Y.R.O.N. score, signal, confidence,
    and plain-English explanation.
    """

    score = 50
    reasons = []

    # Price compared with the 20-day average
    if current_price > average_20:
        score += 12
        reasons.append("the price is above its recent average")
    else:
        score -= 12
        reasons.append("the price is below its recent average")

    # Short-term trend compared with the longer trend
    if average_20 > average_50:
        score += 18
        reasons.append(
            "the short-term trend is stronger than the longer trend"
        )
    else:
        score -= 18
        reasons.append(
            "the short-term trend is weaker than the longer trend"
        )

    # RSI momentum
    if 50 <= rsi <= 70:
        score += 10
        reasons.append("momentum is currently positive")
    elif rsi > 75:
        score -= 8
        reasons.append("the stock may have risen too quickly")
    elif rsi < 35:
        score -= 5
        reasons.append("selling pressure has recently been high")

    # Five-day price movement
    if pd.notna(recent_return):
        if recent_return > 0.03:
            score += 10
            reasons.append("momentum has been positive this week")
        elif recent_return < -0.03:
            score -= 10
            reasons.append("momentum has been negative this week")

    score = int(max(0, min(100, round(score))))

    # Friendly signal
    if score >= 68:
        signal = "GO FOR IT"
        emoji = "🟢"
        card_class = "buy-card"
        action_message = (
            "This stock currently has positive price momentum. "
            "It may be worth watching for a possible opportunity."
        )
    elif score >= 43:
        signal = "WATCH"
        emoji = "🟡"
        card_class = "watch-card"
        action_message = (
            "The signals are mixed right now. Waiting for a clearer "
            "trend may be the safer move."
        )
    else:
        signal = "BE CAREFUL"
        emoji = "🔴"
        card_class = "avoid-card"
        action_message = (
            "The stock is currently showing weakness. It may be "
            "better to wait before making a move."
        )

    # Confidence measures how far the score is from neutral
    confidence = int(min(95, 55 + abs(score - 50)))

    if reasons:
        plain_reason = f"B.Y.R.O.N. noticed that {reasons[0]}"

        if len(reasons) > 1:
            plain_reason += f", and {reasons[1]}"

        plain_reason += "."
    else:
        plain_reason = "B.Y.R.O.N. found a mixed market trend."

    return {
        "score": score,
        "signal": signal,
        "emoji": emoji,
        "card_class": card_class,
        "action_message": action_message,
        "confidence": confidence,
        "reason": plain_reason,
        "reasons": reasons,
    }