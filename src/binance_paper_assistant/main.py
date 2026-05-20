"""FastAPI application exposing local read-only analysis tools."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .backtesting import backtest_ema_crossover
from .config import get_settings
from .constants import SUPPORTED_STRATEGIES
from .db import init_db
from .indicators import compute_indicators
from .journal import JournalService
from .market_data import BinanceMarketDataClient
from .reporting import generate_market_report
from .schemas import (
    AddPaperTradeRequest,
    BacktestResult,
    CandleQuery,
    ClosePaperTradeRequest,
    MarketReportQuery,
    RecordPaperTradeEntryRequest,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Binance Paper Trading Assistant",
    version="0.1.0",
    lifespan=lifespan,
    description=(
        "Local read-only Binance spot market analysis assistant for decision support and paper trading only. "
        "This app does not place orders, withdraw funds, use private keys, or enable live trading."
    ),
)

market_client = BinanceMarketDataClient.from_settings()
journal_service = JournalService()


@app.get("/")
def root() -> dict[str, object]:
    settings = get_settings()
    return {
        "name": "Binance Paper Trading Assistant",
        "version": "0.1.0",
        "educational_only": True,
        "warnings": [
            "Not financial advice.",
            "Version 1 does not execute trades.",
            "Public Binance spot market data only.",
        ],
        "allowed_symbols": settings.symbol_allowlist,
        "allowed_intervals": settings.interval_allowlist,
    }


@app.get("/tools/get_candles")
def get_candles(symbol: str, interval: str, limit: int = 300) -> dict[str, object]:
    query = CandleQuery(symbol=symbol, interval=interval, limit=limit)
    frame = market_client.get_candles(query.symbol, query.interval, query.limit)
    return {
        "symbol": query.symbol,
        "interval": query.interval,
        "limit": query.limit,
        "count": len(frame),
        "candles": frame.to_dict(orient="records"),
        "educational_only": True,
    }


@app.get("/tools/calculate_indicators")
def calculate_indicators(symbol: str, interval: str, limit: int = 300) -> dict[str, object]:
    query = CandleQuery(symbol=symbol, interval=interval, limit=limit)
    frame = market_client.get_candles(query.symbol, query.interval, query.limit)
    enriched = compute_indicators(frame)
    latest = enriched.tail(1).to_dict(orient="records")[0]
    return {
        "symbol": query.symbol,
        "interval": query.interval,
        "limit": query.limit,
        "latest": latest,
        "educational_only": True,
        "risk_warning": "Indicators are lagging tools and can fail during fast market changes.",
    }


@app.get("/tools/generate_market_report")
def generate_market_report_endpoint(symbol: str, interval: str) -> dict[str, object]:
    query = MarketReportQuery(symbol=symbol, interval=interval)
    frame = market_client.get_candles(query.symbol, query.interval, limit=300)
    enriched = compute_indicators(frame)
    return generate_market_report(enriched, query.symbol, query.interval)


@app.post("/tools/add_paper_trade")
def add_paper_trade(request: AddPaperTradeRequest) -> dict[str, object]:
    trade = journal_service.add_trade_idea(request)
    return {
        "trade": trade.model_dump(),
        "warning": "Educational / paper trading only. No live execution is performed.",
    }


@app.post("/tools/paper_trades/{trade_id}/record_entry")
def record_paper_trade_entry(trade_id: int, request: RecordPaperTradeEntryRequest) -> dict[str, object]:
    trade = journal_service.record_entry(trade_id, request)
    return {
        "trade": trade.model_dump(),
        "warning": "Paper trade entry recorded. No exchange order was sent.",
    }


@app.post("/tools/close_paper_trade")
def close_paper_trade(trade_id: int, request: ClosePaperTradeRequest) -> dict[str, object]:
    trade = journal_service.close_trade(trade_id, request)
    return {
        "trade": trade.model_dump(),
        "warning": "Educational / paper trading only. No live execution is performed.",
    }


@app.get("/tools/list_paper_trades")
def list_paper_trades(status: str | None = None) -> dict[str, object]:
    if status and status not in {"idea", "open", "closed"}:
        raise HTTPException(status_code=400, detail="Status must be one of: idea, open, closed.")
    trades = journal_service.list_trades(status)
    return {
        "status": status or "all",
        "count": len(trades),
        "trades": [trade.model_dump() for trade in trades],
        "educational_only": True,
    }


@app.get("/tools/backtest_strategy", response_model=BacktestResult)
def backtest_strategy(symbol: str, interval: str, strategy_name: str) -> BacktestResult:
    query = CandleQuery(symbol=symbol, interval=interval, limit=500)
    if strategy_name not in SUPPORTED_STRATEGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported strategy_name: {strategy_name}. Supported: {sorted(SUPPORTED_STRATEGIES)}",
        )
    frame = market_client.get_candles(query.symbol, query.interval, query.limit)
    enriched = compute_indicators(frame)
    return backtest_ema_crossover(
        enriched,
        symbol=query.symbol,
        interval=query.interval,
        strategy_name=strategy_name,
    )
