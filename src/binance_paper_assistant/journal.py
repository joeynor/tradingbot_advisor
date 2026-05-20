"""Paper trading journal service."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException

from .db import get_connection
from .schemas import AddPaperTradeRequest, ClosePaperTradeRequest, PaperTradeRecord, RecordPaperTradeEntryRequest


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def calculate_risk_reward(side: str, entry: float, stop_loss: float, take_profit: float) -> float:
    if side == "long":
        risk = entry - stop_loss
        reward = take_profit - entry
    else:
        risk = stop_loss - entry
        reward = entry - take_profit
    if risk <= 0:
        raise ValueError("Stop-loss configuration results in non-positive risk.")
    return reward / risk


def calculate_pnl(side: str, entry_price: float, exit_price: float) -> tuple[float, float]:
    if side == "long":
        pnl_amount = exit_price - entry_price
    else:
        pnl_amount = entry_price - exit_price
    pnl_percent = (pnl_amount / entry_price) * 100
    return pnl_amount, pnl_percent


def _row_to_trade(row) -> PaperTradeRecord:
    return PaperTradeRecord.model_validate(dict(row))


class JournalService:
    def add_trade_idea(self, request: AddPaperTradeRequest) -> PaperTradeRecord:
        rr = calculate_risk_reward(request.side, request.entry, request.stop_loss, request.take_profit)
        timestamp = _utc_now_iso()
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO paper_trades (
                    symbol, side, entry, stop_loss, take_profit, thesis,
                    status, created_at, updated_at, risk_reward_ratio, educational_only
                ) VALUES (?, ?, ?, ?, ?, ?, 'idea', ?, ?, ?, 1)
                """,
                (
                    request.symbol,
                    request.side,
                    request.entry,
                    request.stop_loss,
                    request.take_profit,
                    request.thesis,
                    timestamp,
                    timestamp,
                    rr,
                ),
            )
            connection.commit()
            trade_id = cursor.lastrowid
        return self.get_trade(trade_id)

    def record_entry(self, trade_id: int, request: RecordPaperTradeEntryRequest) -> PaperTradeRecord:
        trade = self.get_trade(trade_id)
        if trade.status not in {"idea", "open"}:
            raise HTTPException(status_code=400, detail="Only idea or open trades can record an entry.")

        timestamp = _utc_now_iso()
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE paper_trades
                SET status = 'open',
                    opened_at = COALESCE(opened_at, ?),
                    actual_entry = ?,
                    notes = COALESCE(?, notes),
                    updated_at = ?
                WHERE id = ?
                """,
                (timestamp, request.actual_entry, request.notes, timestamp, trade_id),
            )
            connection.commit()
        return self.get_trade(trade_id)

    def close_trade(self, trade_id: int, request: ClosePaperTradeRequest) -> PaperTradeRecord:
        trade = self.get_trade(trade_id)
        if trade.status == "closed":
            raise HTTPException(status_code=400, detail="Trade is already closed.")

        entry_price = trade.actual_entry or trade.entry
        pnl_amount, pnl_percent = calculate_pnl(trade.side, entry_price, request.exit_price)
        timestamp = _utc_now_iso()
        notes = request.notes if request.notes is not None else trade.notes
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE paper_trades
                SET status = 'closed',
                    closed_at = ?,
                    actual_exit = ?,
                    notes = ?,
                    pnl_amount = ?,
                    pnl_percent = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (timestamp, request.exit_price, notes, pnl_amount, pnl_percent, timestamp, trade_id),
            )
            connection.commit()
        return self.get_trade(trade_id)

    def get_trade(self, trade_id: int) -> PaperTradeRecord:
        with get_connection() as connection:
            row = connection.execute("SELECT * FROM paper_trades WHERE id = ?", (trade_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Trade {trade_id} was not found.")
        return _row_to_trade(row)

    def list_trades(self, status: str | None = None) -> list[PaperTradeRecord]:
        query = "SELECT * FROM paper_trades"
        params: tuple[str, ...] = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at DESC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [_row_to_trade(row) for row in rows]

