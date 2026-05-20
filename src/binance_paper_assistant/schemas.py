"""Pydantic models for API and internal services."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .config import get_settings
from .constants import MAX_CANDLE_LIMIT, MIN_CANDLE_LIMIT, SUPPORTED_SIDES


class CandleQuery(BaseModel):
    symbol: str
    interval: str
    limit: int = Field(default=300, ge=MIN_CANDLE_LIMIT, le=MAX_CANDLE_LIMIT)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        value = value.upper()
        if value not in get_settings().symbol_allowlist:
            raise ValueError(f"Unsupported symbol: {value}")
        return value

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, value: str) -> str:
        if value not in get_settings().interval_allowlist:
            raise ValueError(f"Unsupported interval: {value}")
        return value


class MarketReportQuery(BaseModel):
    symbol: str
    interval: str

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        value = value.upper()
        if value not in get_settings().symbol_allowlist:
            raise ValueError(f"Unsupported symbol: {value}")
        return value

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, value: str) -> str:
        if value not in get_settings().interval_allowlist:
            raise ValueError(f"Unsupported interval: {value}")
        return value


class AddPaperTradeRequest(BaseModel):
    symbol: str
    side: Literal["long", "short"]
    entry: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    thesis: str = Field(min_length=10, max_length=2000)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        value = value.upper()
        if value not in get_settings().symbol_allowlist:
            raise ValueError(f"Unsupported symbol: {value}")
        return value

    @field_validator("side")
    @classmethod
    def validate_side(cls, value: str) -> str:
        if value not in SUPPORTED_SIDES:
            raise ValueError(f"Unsupported side: {value}")
        return value


class RecordPaperTradeEntryRequest(BaseModel):
    actual_entry: float = Field(gt=0)
    notes: str | None = Field(default=None, max_length=2000)


class ClosePaperTradeRequest(BaseModel):
    exit_price: float = Field(gt=0)
    notes: str | None = Field(default=None, max_length=2000)


class PaperTradeRecord(BaseModel):
    id: int
    symbol: str
    side: str
    entry: float
    stop_loss: float
    take_profit: float
    thesis: str
    status: str
    created_at: datetime
    updated_at: datetime
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    actual_entry: float | None = None
    actual_exit: float | None = None
    notes: str | None = None
    risk_reward_ratio: float | None = None
    pnl_amount: float | None = None
    pnl_percent: float | None = None
    educational_only: bool = True


class BacktestResult(BaseModel):
    symbol: str
    interval: str
    strategy_name: str
    trade_count: int
    win_rate: float
    total_return_percent: float
    max_drawdown_percent: float
    buy_and_hold_return_percent: float
    educational_only: bool = True
    notes: list[str]
