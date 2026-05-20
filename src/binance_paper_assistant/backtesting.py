"""Simple strategy backtesting."""

from __future__ import annotations

import pandas as pd

from .schemas import BacktestResult


def _max_drawdown(equity_curve: pd.Series) -> float:
    running_max = equity_curve.cummax()
    drawdown = (equity_curve / running_max) - 1
    return float(drawdown.min()) * 100


def _build_strategy_signals(frame: pd.DataFrame, strategy_name: str) -> tuple[pd.Series, pd.Series, list[str]]:
    notes = [
        "Educational backtest only. Slippage, fees, spread, and taxes are not modeled.",
        "This simple strategy can underperform badly in sideways markets.",
    ]

    if strategy_name == "ema20_ema50":
        long_entries = (frame["ema20"] > frame["ema50"]) & (frame["ema20"].shift(1) <= frame["ema50"].shift(1))
        short_entries = (frame["ema20"] < frame["ema50"]) & (frame["ema20"].shift(1) >= frame["ema50"].shift(1))
        notes.append("EMA20/EMA50 crossover mode: long-only, exits on bearish crossover.")
        return long_entries, short_entries, notes

    if strategy_name == "ema20_ema50_rsi":
        long_entries = (
            (frame["ema20"] > frame["ema50"])
            & (frame["ema20"].shift(1) <= frame["ema50"].shift(1))
            & (frame["rsi14"] > 50)
        )
        short_entries = (frame["ema20"] < frame["ema50"]) & (frame["ema20"].shift(1) >= frame["ema50"].shift(1))
        notes.extend(
            [
                "EMA20/EMA50 crossover mode: long-only, exits on bearish crossover.",
                "RSI filter enabled: entries only occur when RSI14 is above 50.",
            ]
        )
        return long_entries, short_entries, notes

    long_entries = (
        (frame["ema3"] > frame["ema8"])
        & (frame["ema3"].shift(1) <= frame["ema8"].shift(1))
        & (frame["ema8"] > frame["ema17"])
        & (frame["rsi14"] > 50)
        & (frame["macd"] > frame["macd_signal"])
    )
    short_entries = (
        (frame["ema3"] < frame["ema8"])
        & (frame["ema3"].shift(1) >= frame["ema8"].shift(1))
        & (frame["ema8"] < frame["ema17"])
        & (frame["rsi14"] < 50)
        & (frame["macd"] < frame["macd_signal"])
    )
    notes.extend(
        [
            "EMA3/EMA8/EMA17 crossover mode: long and short entries use the EMA3 vs EMA8 cross.",
            "Trend filter enabled: longs require EMA8 above EMA17, shorts require EMA8 below EMA17.",
            "Momentum filters enabled: longs require RSI14 > 50 and MACD above signal; shorts require RSI14 < 50 and MACD below signal.",
            "Exits occur on the opposite crossover.",
        ]
    )
    return long_entries, short_entries, notes


def _close_trade(position: int, entry_price: float, exit_price: float) -> float:
    if position == 1:
        return (exit_price / entry_price) - 1
    return (entry_price / exit_price) - 1


def backtest_ema_crossover(
    data: pd.DataFrame,
    symbol: str,
    interval: str,
    strategy_name: str,
) -> BacktestResult:
    frame = data.copy()
    frame["signal"] = 0
    long_entries, short_entries, notes = _build_strategy_signals(frame, strategy_name)
    frame.loc[long_entries, "signal"] = 1
    frame.loc[short_entries, "signal"] = -1

    position = 0
    entry_price = 0.0
    trades: list[float] = []
    strategy_returns: list[float] = [0.0]

    closes = frame["close"].tolist()
    signals = frame["signal"].tolist()

    for index in range(1, len(frame)):
        signal = signals[index]
        current_close = closes[index]
        previous_close = closes[index - 1]

        if strategy_name in {"ema20_ema50", "ema20_ema50_rsi"}:
            if signal == 1 and position == 0:
                position = 1
                entry_price = current_close
            elif signal == -1 and position == 1:
                trades.append(_close_trade(position, entry_price, current_close))
                position = 0
                entry_price = 0.0
        else:
            if signal == 1:
                if position == -1:
                    trades.append(_close_trade(position, entry_price, current_close))
                    position = 0
                    entry_price = 0.0
                if position == 0:
                    position = 1
                    entry_price = current_close
            elif signal == -1:
                if position == 1:
                    trades.append(_close_trade(position, entry_price, current_close))
                    position = 0
                    entry_price = 0.0
                if position == 0:
                    position = -1
                    entry_price = current_close

        bar_return = (current_close / previous_close) - 1
        if position == 1:
            strategy_returns.append(bar_return)
        elif position == -1:
            strategy_returns.append(-bar_return)
        else:
            strategy_returns.append(0.0)

    if position != 0:
        trades.append(_close_trade(position, entry_price, closes[-1]))

    frame["strategy_returns"] = strategy_returns
    frame["equity_curve"] = (1 + frame["strategy_returns"]).cumprod()
    total_return = (frame["equity_curve"].iloc[-1] - 1) * 100
    buy_hold_return = ((frame["close"].iloc[-1] / frame["close"].iloc[0]) - 1) * 100
    wins = sum(1 for item in trades if item > 0)
    win_rate = (wins / len(trades) * 100) if trades else 0.0

    return BacktestResult(
        symbol=symbol,
        interval=interval,
        strategy_name=strategy_name,
        trade_count=len(trades),
        win_rate=round(win_rate, 2),
        total_return_percent=round(total_return, 2),
        max_drawdown_percent=round(_max_drawdown(frame["equity_curve"]), 2),
        buy_and_hold_return_percent=round(buy_hold_return, 2),
        notes=notes,
    )
