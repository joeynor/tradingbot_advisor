from pathlib import Path

from binance_paper_assistant import config as config_module
from binance_paper_assistant.db import init_db
from binance_paper_assistant.journal import JournalService
from binance_paper_assistant.schemas import AddPaperTradeRequest, ClosePaperTradeRequest, RecordPaperTradeEntryRequest


def test_journal_trade_lifecycle(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "journal.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    config_module.get_settings.cache_clear()
    init_db()
    journal = JournalService()

    created = journal.add_trade_idea(
        AddPaperTradeRequest(
            symbol="BTCUSDT",
            side="long",
            entry=100.0,
            stop_loss=95.0,
            take_profit=110.0,
            thesis="Educational paper trade based on support reclaim and bullish momentum.",
        )
    )

    assert created.status == "idea"
    assert round(created.risk_reward_ratio, 2) == 2.0

    opened = journal.record_entry(
        created.id,
        RecordPaperTradeEntryRequest(actual_entry=101.0, notes="Triggered on retest."),
    )
    assert opened.status == "open"
    assert opened.actual_entry == 101.0

    closed = journal.close_trade(
        created.id,
        ClosePaperTradeRequest(exit_price=108.0, notes="Closed into resistance."),
    )
    assert closed.status == "closed"
    assert round(closed.pnl_amount, 2) == 7.0
    assert round(closed.pnl_percent, 2) == round((7.0 / 101.0) * 100, 2)

    closed_trades = journal.list_trades("closed")
    assert len(closed_trades) == 1

