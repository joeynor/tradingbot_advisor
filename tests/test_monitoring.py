from fastapi import HTTPException

from binance_paper_assistant.monitoring import emit_notification
from binance_paper_assistant.monitoring import trade_suggestion_key
from binance_paper_assistant.monitoring import watch_market_reports


def test_trade_suggestion_key_is_none_without_suggestion():
    report = {
        "symbol": "BTCUSDT",
        "interval": "15m",
        "possible_trade_idea": None,
    }

    assert trade_suggestion_key(report) is None


def test_trade_suggestion_key_changes_with_suggestion_details():
    base = {
        "symbol": "BTCUSDT",
        "interval": "15m",
        "possible_trade_idea": {
            "side": "long",
            "entry_zone": [100.0, 101.0],
            "stop_loss": 98.0,
            "take_profit": 106.0,
            "risk_reward_ratio": 2.5,
        },
    }

    modified = {
        **base,
        "possible_trade_idea": {
            **base["possible_trade_idea"],
            "take_profit": 107.0,
        },
    }

    assert trade_suggestion_key(base) != trade_suggestion_key(modified)


class TimeoutClient:
    def get_candles(self, symbol, interval, limit):
        raise HTTPException(status_code=504, detail="Timed out while fetching Binance market data.")


def test_watch_market_reports_handles_http_exception(capsys):
    watch_market_reports(
        client=TimeoutClient(),
        symbol="SOLUSDT",
        interval="15m",
        run_once=True,
        notify_mode="none",
    )

    output = capsys.readouterr().out
    assert "Watch check failed for SOLUSDT 15m" in output


def test_emit_notification_requires_ntfy_topic_url():
    report = {
        "symbol": "SOLUSDT",
        "interval": "15m",
        "possible_trade_idea": {
            "side": "long",
            "entry_zone": [100.0, 101.0],
            "stop_loss": 98.0,
            "take_profit": 106.0,
            "risk_reward_ratio": 2.5,
        },
    }

    try:
        emit_notification(report, "ntfy")
    except ValueError as exc:
        assert "ntfy topic URL" in str(exc)
    else:
        raise AssertionError("Expected emit_notification to require an ntfy topic URL.")
