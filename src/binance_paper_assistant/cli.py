"""Small CLI for local usage."""

from __future__ import annotations

import argparse
import json

from .backtesting import backtest_ema_crossover
from .db import init_db
from .indicators import compute_indicators
from .journal import JournalService
from .market_data import BinanceMarketDataClient
from .monitoring import watch_market_reports
from .reporting import generate_market_report
from .schemas import AddPaperTradeRequest, ClosePaperTradeRequest, RecordPaperTradeEntryRequest


def _print(payload) -> None:
    print(json.dumps(payload, indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local read-only Binance analysis assistant")
    subparsers = parser.add_subparsers(dest="command", required=True)

    candles = subparsers.add_parser("candles")
    candles.add_argument("symbol")
    candles.add_argument("interval")
    candles.add_argument("--limit", type=int, default=100)

    report = subparsers.add_parser("report")
    report.add_argument("symbol")
    report.add_argument("interval")

    watch = subparsers.add_parser("watch")
    watch.add_argument("symbol")
    watch.add_argument("interval")
    watch.add_argument("--poll-seconds", type=int, default=900)
    watch.add_argument("--notify", choices=["desktop", "stdout", "ntfy", "none"], default="desktop")
    watch.add_argument("--ntfy-topic-url")
    watch.add_argument("--ntfy-access-token")
    watch.add_argument("--once", action="store_true")

    backtest = subparsers.add_parser("backtest")
    backtest.add_argument("symbol")
    backtest.add_argument("interval")
    backtest.add_argument("strategy_name")

    add_trade = subparsers.add_parser("add-trade")
    add_trade.add_argument("symbol")
    add_trade.add_argument("side")
    add_trade.add_argument("entry", type=float)
    add_trade.add_argument("stop_loss", type=float)
    add_trade.add_argument("take_profit", type=float)
    add_trade.add_argument("thesis")

    record_entry = subparsers.add_parser("record-entry")
    record_entry.add_argument("trade_id", type=int)
    record_entry.add_argument("actual_entry", type=float)
    record_entry.add_argument("--notes")

    close_trade = subparsers.add_parser("close-trade")
    close_trade.add_argument("trade_id", type=int)
    close_trade.add_argument("exit_price", type=float)
    close_trade.add_argument("--notes")

    list_trades = subparsers.add_parser("list-trades")
    list_trades.add_argument("--status", choices=["idea", "open", "closed"])

    return parser


def main() -> None:
    init_db()
    parser = build_parser()
    args = parser.parse_args()
    journal = JournalService()
    client = BinanceMarketDataClient.from_settings()

    if args.command == "candles":
        data = client.get_candles(args.symbol.upper(), args.interval, args.limit)
        _print(data.tail(5).to_dict(orient="records"))
        return

    if args.command == "report":
        data = client.get_candles(args.symbol.upper(), args.interval, 300)
        report = generate_market_report(compute_indicators(data), args.symbol.upper(), args.interval)
        _print(report)
        return

    if args.command == "watch":
        watch_market_reports(
            client=client,
            symbol=args.symbol.upper(),
            interval=args.interval,
            poll_seconds=args.poll_seconds,
            notify_mode=args.notify,
            ntfy_topic_url=args.ntfy_topic_url,
            ntfy_access_token=args.ntfy_access_token,
            run_once=args.once,
        )
        return

    if args.command == "backtest":
        data = client.get_candles(args.symbol.upper(), args.interval, 500)
        result = backtest_ema_crossover(
            compute_indicators(data),
            symbol=args.symbol.upper(),
            interval=args.interval,
            strategy_name=args.strategy_name,
        )
        _print(result.model_dump())
        return

    if args.command == "add-trade":
        trade = journal.add_trade_idea(
            AddPaperTradeRequest(
                symbol=args.symbol.upper(),
                side=args.side,
                entry=args.entry,
                stop_loss=args.stop_loss,
                take_profit=args.take_profit,
                thesis=args.thesis,
            )
        )
        _print(trade.model_dump())
        return

    if args.command == "record-entry":
        trade = journal.record_entry(
            args.trade_id,
            RecordPaperTradeEntryRequest(actual_entry=args.actual_entry, notes=args.notes),
        )
        _print(trade.model_dump())
        return

    if args.command == "close-trade":
        trade = journal.close_trade(
            args.trade_id,
            ClosePaperTradeRequest(exit_price=args.exit_price, notes=args.notes),
        )
        _print(trade.model_dump())
        return

    if args.command == "list-trades":
        trades = journal.list_trades(args.status)
        _print([trade.model_dump() for trade in trades])
        return


if __name__ == "__main__":
    main()
