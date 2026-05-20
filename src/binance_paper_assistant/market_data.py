"""Public Binance spot market data access."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
import pandas as pd
from fastapi import HTTPException

from .config import get_settings
from .constants import MAX_CANDLE_LIMIT


@dataclass(slots=True)
class BinanceMarketDataClient:
    base_url: str
    timeout_seconds: float

    @classmethod
    def from_settings(cls) -> "BinanceMarketDataClient":
        settings = get_settings()
        return cls(base_url=settings.binance_base_url.rstrip("/"), timeout_seconds=settings.request_timeout_seconds)

    def get_candles(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        limit = max(1, min(limit, MAX_CANDLE_LIMIT))
        url = f"{self.base_url}/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(url, params=params)
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail="Timed out while fetching Binance market data.") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="Failed to contact Binance public API.") from exc

        if response.status_code in {418, 429}:
            raise HTTPException(
                status_code=429,
                detail="Binance rate limit encountered. Slow down requests and retry shortly.",
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"Binance public API returned an error: {response.status_code}",
            )

        payload = response.json()
        frame = pd.DataFrame(
            payload,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_asset_volume",
                "taker_buy_quote_asset_volume",
                "ignore",
            ],
        )
        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_asset_volume",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
        ]
        for column in numeric_columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

        frame["open_time"] = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
        frame["close_time"] = pd.to_datetime(frame["close_time"], unit="ms", utc=True)
        frame["number_of_trades"] = pd.to_numeric(frame["number_of_trades"], errors="coerce").fillna(0).astype(int)
        return frame

