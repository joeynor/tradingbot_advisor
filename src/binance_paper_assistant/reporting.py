"""Structured market report generation."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _float(value: Any) -> float:
    return round(float(value), 4)


def _trend_condition(last: pd.Series) -> str:
    if last["close"] > last["ema20"] > last["ema50"] > last["ema200"]:
        return "Strong uptrend"
    if last["close"] < last["ema20"] < last["ema50"] < last["ema200"]:
        return "Strong downtrend"
    if last["close"] > last["ema50"] and last["ema20"] > last["ema50"]:
        return "Bullish but not fully aligned"
    if last["close"] < last["ema50"] and last["ema20"] < last["ema50"]:
        return "Bearish but not fully aligned"
    return "Mixed / range-bound"


def _momentum_condition(last: pd.Series) -> str:
    bullish = last["rsi14"] >= 55 and last["macd_histogram"] >= 0
    bearish = last["rsi14"] <= 45 and last["macd_histogram"] <= 0
    if bullish:
        return "Bullish momentum"
    if bearish:
        return "Bearish momentum"
    return "Neutral momentum"


def _volatility_condition(last: pd.Series) -> str:
    atr_percent = (last["atr14"] / last["close"]) * 100 if last["close"] else 0
    if atr_percent >= 4:
        return "High volatility"
    if atr_percent >= 2:
        return "Moderate volatility"
    return "Low volatility"


def _support_resistance(data: pd.DataFrame) -> tuple[float, float]:
    recent = data.tail(30)
    support = recent["low"].min()
    resistance = recent["high"].max()
    return _float(support), _float(resistance)


def _trade_idea(last: pd.Series, support: float, resistance: float) -> dict[str, Any] | None:
    current_price = float(last["close"])
    atr = float(last["atr14"])
    trend = _trend_condition(last)
    momentum = _momentum_condition(last)

    if "Bullish" in momentum and "uptrend" in trend.lower():
        entry = max(current_price - (0.3 * atr), support + (0.1 * atr))
        stop = support - (0.6 * atr)
        risk = entry - stop
        take_profit = max(resistance, entry + (risk * 2))
        rr = (take_profit - entry) / risk if risk > 0 else 0
        side = "long"
    elif "Bearish" in momentum and "downtrend" in trend.lower():
        entry = min(current_price + (0.3 * atr), resistance - (0.1 * atr))
        stop = resistance + (0.6 * atr)
        risk = stop - entry
        take_profit = min(support, entry - (risk * 2))
        rr = (entry - take_profit) / risk if risk > 0 else 0
        side = "short"
    else:
        return None

    if rr < 2:
        return None

    return {
        "side": side,
        "label": "Educational / paper trading only",
        "entry_zone": [_float(entry * 0.9975), _float(entry * 1.0025)],
        "stop_loss": _float(stop),
        "take_profit": _float(take_profit),
        "invalidation_level": _float(stop),
        "risk_reward_ratio": round(rr, 2),
    }


def generate_market_report(data: pd.DataFrame, symbol: str, interval: str) -> dict[str, Any]:
    last = data.iloc[-1]
    support, resistance = _support_resistance(data)
    trade_idea = _trade_idea(last, support, resistance)
    reasons_not_to_trade = [
        "This is educational analysis only and not financial advice.",
        "Market structure may change quickly around macro news or low-liquidity hours.",
        "Public candle-based indicators lag price and can fail in chop.",
        "If invalidation is too wide for your risk tolerance, skip the setup.",
    ]

    if trade_idea is None:
        reasons_not_to_trade.append("No setup met the minimum 1:2 risk/reward filter.")

    return {
        "symbol": symbol,
        "interval": interval,
        "educational_only": True,
        "risk_warning": "For decision support and paper trading only. Do not execute live trades from this report.",
        "snapshot": {
            "last_close": _float(last["close"]),
            "ema20": _float(last["ema20"]),
            "ema50": _float(last["ema50"]),
            "ema200": _float(last["ema200"]),
            "rsi14": _float(last["rsi14"]),
            "macd": _float(last["macd"]),
            "macd_signal": _float(last["macd_signal"]),
            "atr14": _float(last["atr14"]),
            "volume": _float(last["volume"]),
            "volume_ma20": _float(last["volume_ma20"]),
        },
        "trend_condition": _trend_condition(last),
        "momentum_condition": _momentum_condition(last),
        "volatility_condition": _volatility_condition(last),
        "support_resistance_estimate": {
            "support": support,
            "resistance": resistance,
        },
        "bullish_scenario": f"If price holds above {support} and reclaims momentum, continuation toward {resistance} is possible.",
        "bearish_scenario": f"If price loses {support}, downside expansion could test lower liquidity below recent structure.",
        "possible_trade_idea": trade_idea,
        "reasons_not_to_trade": reasons_not_to_trade,
    }

