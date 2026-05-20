"""Technical indicator calculations."""

from __future__ import annotations

import pandas as pd


def compute_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    close = data["close"]
    high = data["high"]
    low = data["low"]
    volume = data["volume"]

    data["ema3"] = close.ewm(span=3, adjust=False).mean()
    data["ema8"] = close.ewm(span=8, adjust=False).mean()
    data["ema17"] = close.ewm(span=17, adjust=False).mean()
    data["ema20"] = close.ewm(span=20, adjust=False).mean()
    data["ema50"] = close.ewm(span=50, adjust=False).mean()
    data["ema200"] = close.ewm(span=200, adjust=False).mean()

    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = losses.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    data["rsi14"] = 100 - (100 / (1 + rs))
    data["rsi14"] = data["rsi14"].fillna(50)

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    data["macd"] = ema12 - ema26
    data["macd_signal"] = data["macd"].ewm(span=9, adjust=False).mean()
    data["macd_histogram"] = data["macd"] - data["macd_signal"]

    rolling_mean = close.rolling(window=20, min_periods=20).mean()
    rolling_std = close.rolling(window=20, min_periods=20).std(ddof=0)
    data["bb_middle"] = rolling_mean
    data["bb_upper"] = rolling_mean + (rolling_std * 2)
    data["bb_lower"] = rolling_mean - (rolling_std * 2)
    data["bb_width"] = (data["bb_upper"] - data["bb_lower"]) / data["bb_middle"]

    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            (high - low),
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    data["atr14"] = true_range.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    data["volume_ma20"] = volume.rolling(window=20, min_periods=1).mean()

    return data
