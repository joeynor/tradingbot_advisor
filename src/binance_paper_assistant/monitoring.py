"""Polling helpers for repeated report checks and notifications."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from datetime import datetime
from typing import Any

import httpx
from fastapi import HTTPException

from .config import get_settings
from .indicators import compute_indicators
from .market_data import BinanceMarketDataClient
from .reporting import generate_market_report


def _timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def trade_suggestion_key(report: dict[str, Any]) -> str | None:
    suggestion = report.get("possible_trade_idea")
    if not suggestion:
        return None
    return json.dumps(
        {
            "symbol": report["symbol"],
            "interval": report["interval"],
            "suggestion": suggestion,
        },
        sort_keys=True,
    )


def _notification_text(report: dict[str, Any]) -> tuple[str, str]:
    suggestion = report["possible_trade_idea"]
    title = f"Trade suggestion: {report['symbol']} {report['interval']}"
    body = (
        f"{suggestion['side'].upper()} idea | "
        f"Entry {suggestion['entry_zone'][0]}-{suggestion['entry_zone'][1]} | "
        f"SL {suggestion['stop_loss']} | TP {suggestion['take_profit']} | "
        f"RR {suggestion['risk_reward_ratio']}"
    )
    return title, body


def _emit_desktop_notification(title: str, body: str) -> bool:
    if shutil.which("osascript") is None:
        return False
    script = f'display notification "{body}" with title "{title}"'
    subprocess.run(["osascript", "-e", script], check=False)
    return True


def _emit_ntfy_notification(title: str, body: str, topic_url: str, access_token: str | None = None) -> None:
    headers = {"Title": title}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    with httpx.Client(timeout=15.0) as client:
        response = client.post(topic_url, content=body.encode("utf-8"), headers=headers)
        response.raise_for_status()


def emit_notification(
    report: dict[str, Any],
    notify_mode: str,
    ntfy_topic_url: str | None = None,
    ntfy_access_token: str | None = None,
) -> None:
    title, body = _notification_text(report)
    if notify_mode == "desktop":
        delivered = _emit_desktop_notification(title, body)
        if delivered:
            print(f"[{_timestamp()}] Desktop notification sent: {body}")
            return
        print(f"[{_timestamp()}] Desktop notifications unavailable, falling back to stdout.")
    if notify_mode == "ntfy":
        if not ntfy_topic_url:
            raise ValueError("ntfy notifications require an ntfy topic URL.")
        _emit_ntfy_notification(title, body, ntfy_topic_url, ntfy_access_token)
        print(f"[{_timestamp()}] ntfy notification sent: {body}")
        return
    if notify_mode == "stdout" or notify_mode == "desktop":
        print(f"[{_timestamp()}] {title} :: {body}")


def _sleep_or_exit(poll_seconds: int, run_once: bool) -> bool:
    if run_once:
        return False
    time.sleep(poll_seconds)
    return True


def watch_market_reports(
    client: BinanceMarketDataClient,
    symbol: str,
    interval: str,
    poll_seconds: int = 900,
    notify_mode: str = "desktop",
    ntfy_topic_url: str | None = None,
    ntfy_access_token: str | None = None,
    run_once: bool = False,
) -> None:
    last_notified_key: str | None = None
    settings = get_settings()
    resolved_ntfy_topic_url = ntfy_topic_url or settings.ntfy_topic_url
    resolved_ntfy_access_token = ntfy_access_token or settings.ntfy_access_token

    while True:
        try:
            frame = client.get_candles(symbol, interval, 300)
            report = generate_market_report(compute_indicators(frame), symbol, interval)
        except HTTPException as exc:
            print(f"[{_timestamp()}] Watch check failed for {symbol} {interval}: {exc.detail}")
            if not _sleep_or_exit(poll_seconds, run_once):
                return
            continue
        except Exception as exc:
            print(f"[{_timestamp()}] Unexpected watch error for {symbol} {interval}: {exc}")
            if not _sleep_or_exit(poll_seconds, run_once):
                return
            continue

        suggestion_key = trade_suggestion_key(report)

        if suggestion_key is None:
            print(f"[{_timestamp()}] No trade suggestion for {symbol} {interval}.")
            last_notified_key = None
        elif suggestion_key != last_notified_key:
            try:
                emit_notification(
                    report,
                    notify_mode,
                    ntfy_topic_url=resolved_ntfy_topic_url,
                    ntfy_access_token=resolved_ntfy_access_token,
                )
                last_notified_key = suggestion_key
            except Exception as exc:
                print(f"[{_timestamp()}] Notification failed for {symbol} {interval}: {exc}")
        else:
            print(f"[{_timestamp()}] Trade suggestion unchanged for {symbol} {interval}.")

        if not _sleep_or_exit(poll_seconds, run_once):
            return
