"""Local MCP server exposing read-only Binance analysis and paper journal tools."""

from __future__ import annotations

import argparse
from typing import Any

from mcp.server.fastmcp import FastMCP

from .backtesting import backtest_ema_crossover
from .constants import SUPPORTED_STRATEGIES
from .db import init_db
from .indicators import compute_indicators
from .journal import JournalService
from .market_data import BinanceMarketDataClient
from .reporting import generate_market_report as build_market_report
from .schemas import (
    AddPaperTradeRequest,
    CandleQuery,
    ClosePaperTradeRequest,
    MarketReportQuery,
    RecordPaperTradeEntryRequest,
)

mcp = FastMCP(
    "Binance Paper Trading Assistant",
    instructions=(
        "Local read-only Binance spot market analysis and paper trading journal server. "
        "Never interpret outputs as financial advice. "
        "Never place live orders, never withdraw funds, and never use margin, futures, leverage, or derivatives."
    ),
    json_response=True,
)

market_client = BinanceMarketDataClient.from_settings()
journal_service = JournalService()


def _initialize() -> None:
    init_db()


@mcp.tool()
def get_candles(symbol: str, interval: str, limit: int = 300) -> dict[str, Any]:
    """Fetch public Binance spot candles for an allowlisted symbol and interval."""
    _initialize()
    query = CandleQuery(symbol=symbol, interval=interval, limit=limit)
    frame = market_client.get_candles(query.symbol, query.interval, query.limit)
    return {
        "symbol": query.symbol,
        "interval": query.interval,
        "limit": query.limit,
        "count": len(frame),
        "candles": frame.to_dict(orient="records"),
        "educational_only": True,
        "risk_warning": "Public market data only. This tool does not execute trades.",
    }


@mcp.tool()
def calculate_indicators(symbol: str, interval: str, limit: int = 300) -> dict[str, Any]:
    """Calculate EMA, RSI, MACD, Bollinger Bands, ATR, and volume moving average."""
    _initialize()
    query = CandleQuery(symbol=symbol, interval=interval, limit=limit)
    frame = market_client.get_candles(query.symbol, query.interval, query.limit)
    enriched = compute_indicators(frame)
    return {
        "symbol": query.symbol,
        "interval": query.interval,
        "limit": query.limit,
        "latest": enriched.tail(1).to_dict(orient="records")[0],
        "educational_only": True,
        "risk_warning": "Indicators are lagging and should not be used for live trading decisions.",
    }


@mcp.tool(name="generate_market_report")
def generate_market_report_tool(symbol: str, interval: str) -> dict[str, Any]:
    """Generate a structured market report with scenarios, risk warnings, and paper-trade-only ideas."""
    _initialize()
    query = MarketReportQuery(symbol=symbol, interval=interval)
    frame = market_client.get_candles(query.symbol, query.interval, limit=300)
    enriched = compute_indicators(frame)
    return build_market_report(enriched, query.symbol, query.interval)


@mcp.tool()
def add_paper_trade(
    symbol: str,
    side: str,
    entry: float,
    stop_loss: float,
    take_profit: float,
    thesis: str,
) -> dict[str, Any]:
    """Add an educational paper trade idea to the local journal. This never sends an exchange order."""
    _initialize()
    trade = journal_service.add_trade_idea(
        AddPaperTradeRequest(
            symbol=symbol,
            side=side,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            thesis=thesis,
        )
    )
    return {
        "trade": trade.model_dump(mode="json"),
        "educational_only": True,
        "warning": "Paper trading journal entry created. No live order was placed.",
    }


@mcp.tool()
def record_paper_trade_entry(trade_id: int, actual_entry: float, notes: str | None = None) -> dict[str, Any]:
    """Record a paper trade entry price for an existing journal idea."""
    _initialize()
    trade = journal_service.record_entry(
        trade_id,
        RecordPaperTradeEntryRequest(actual_entry=actual_entry, notes=notes),
    )
    return {
        "trade": trade.model_dump(mode="json"),
        "educational_only": True,
        "warning": "Paper trade entry recorded locally. No exchange order was sent.",
    }


@mcp.tool()
def close_paper_trade(trade_id: int, exit_price: float, notes: str | None = None) -> dict[str, Any]:
    """Close a paper trade in the local journal and calculate PnL."""
    _initialize()
    trade = journal_service.close_trade(
        trade_id,
        ClosePaperTradeRequest(exit_price=exit_price, notes=notes),
    )
    return {
        "trade": trade.model_dump(mode="json"),
        "educational_only": True,
        "warning": "Paper trade closed locally. No live execution occurred.",
    }


@mcp.tool()
def list_paper_trades(status: str | None = None) -> dict[str, Any]:
    """List paper trades by status: idea, open, closed, or all when omitted."""
    _initialize()
    trades = journal_service.list_trades(status)
    return {
        "status": status or "all",
        "count": len(trades),
        "trades": [trade.model_dump(mode="json") for trade in trades],
        "educational_only": True,
        "warning": "Journal results are for paper trading review only.",
    }


@mcp.tool()
def backtest_strategy(symbol: str, interval: str, strategy_name: str) -> dict[str, Any]:
    """Backtest the EMA20/EMA50 crossover strategy, with optional RSI filter, on public spot candles."""
    _initialize()
    if strategy_name not in SUPPORTED_STRATEGIES:
        raise ValueError(f"Unsupported strategy_name: {strategy_name}. Supported: {sorted(SUPPORTED_STRATEGIES)}")
    query = CandleQuery(symbol=symbol, interval=interval, limit=500)
    frame = market_client.get_candles(query.symbol, query.interval, query.limit)
    enriched = compute_indicators(frame)
    result = backtest_ema_crossover(
        enriched,
        symbol=query.symbol,
        interval=query.interval,
        strategy_name=strategy_name,
    )
    return result.model_dump(mode="json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Binance Paper Trading Assistant MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Use stdio for local clients and streamable-http for inspector/testing.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for streamable-http transport.")
    parser.add_argument("--port", type=int, default=8001, help="Port for streamable-http transport.")
    args = parser.parse_args()

    _initialize()
    if args.transport == "streamable-http":
        import uvicorn

        uvicorn.run(mcp.streamable_http_app(), host=args.host, port=args.port)
        return

    mcp.run()


if __name__ == "__main__":
    main()
