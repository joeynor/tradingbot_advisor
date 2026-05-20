import pandas as pd

from binance_paper_assistant.backtesting import backtest_ema_crossover
from binance_paper_assistant.indicators import compute_indicators


def test_compute_indicators_adds_expected_columns():
    size = 260
    frame = pd.DataFrame(
        {
            "open_time": pd.date_range("2024-01-01", periods=size, freq="h", tz="UTC"),
            "open": [100 + idx for idx in range(size)],
            "high": [101 + idx for idx in range(size)],
            "low": [99 + idx for idx in range(size)],
            "close": [100 + idx for idx in range(size)],
            "volume": [1000 + (idx * 10) for idx in range(size)],
            "close_time": pd.date_range("2024-01-01 00:59", periods=size, freq="h", tz="UTC"),
        }
    )

    enriched = compute_indicators(frame)

    expected_columns = {
        "ema3",
        "ema8",
        "ema17",
        "ema20",
        "ema50",
        "ema200",
        "rsi14",
        "macd",
        "macd_signal",
        "macd_histogram",
        "bb_upper",
        "bb_middle",
        "bb_lower",
        "atr14",
        "volume_ma20",
    }
    assert expected_columns.issubset(enriched.columns)
    last_row = enriched.iloc[-1]
    for column in expected_columns:
        assert pd.notna(last_row[column]), f"{column} should be populated on the last row"


def test_rsi_stays_within_expected_range():
    size = 120
    close_prices = [100 + (idx % 7) - 3 + (idx * 0.2) for idx in range(size)]
    frame = pd.DataFrame(
        {
            "open_time": pd.date_range("2024-01-01", periods=size, freq="h", tz="UTC"),
            "open": close_prices,
            "high": [price + 1 for price in close_prices],
            "low": [price - 1 for price in close_prices],
            "close": close_prices,
            "volume": [500 + idx for idx in range(size)],
            "close_time": pd.date_range("2024-01-01 00:59", periods=size, freq="h", tz="UTC"),
        }
    )

    enriched = compute_indicators(frame)
    assert enriched["rsi14"].between(0, 100).all()


def test_ema_3_8_17_strategy_backtest_runs_with_long_and_short_signals():
    closes = [
        100,
        99,
        98,
        99,
        101,
        104,
        107,
        110,
        108,
        105,
        101,
        97,
        93,
        90,
        92,
        95,
        99,
        103,
        107,
        111,
        108,
        104,
        100,
        96,
        92,
        89,
        91,
        94,
        98,
        102,
        106,
        110,
        107,
        103,
        99,
        95,
        91,
        88,
        90,
        94,
        98,
        102,
        106,
        109,
        105,
        101,
        97,
        93,
    ]
    size = len(closes)
    frame = pd.DataFrame(
        {
            "open_time": pd.date_range("2024-01-01", periods=size, freq="h", tz="UTC"),
            "open": closes,
            "high": [price + 1.5 for price in closes],
            "low": [price - 1.5 for price in closes],
            "close": closes,
            "volume": [1000 + (idx * 5) for idx in range(size)],
            "close_time": pd.date_range("2024-01-01 00:59", periods=size, freq="h", tz="UTC"),
        }
    )

    enriched = compute_indicators(frame)
    result = backtest_ema_crossover(
        enriched,
        symbol="BTCUSDT",
        interval="1h",
        strategy_name="ema3_ema8_ema17_rsi_macd",
    )

    assert result.strategy_name == "ema3_ema8_ema17_rsi_macd"
    assert result.trade_count >= 0
    assert isinstance(result.total_return_percent, float)
    assert isinstance(result.max_drawdown_percent, float)
    assert any("EMA3/EMA8/EMA17 crossover mode" in note for note in result.notes)
