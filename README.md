# Binance Paper Trading Assistant

Local read-only Binance spot market analysis assistant for decision support and paper trading.

## Important Warnings

- This project is **not financial advice**.
- This project is **educational / paper trading only**.
- Version 1 **does not execute trades**, place live orders, withdraw funds, enable margin, or use derivatives.
- Version 1 uses **public Binance spot market data only** and does **not require an API key**.
- Every report should be reviewed critically, and every trade idea should be treated as a learning artifact, not an instruction to trade.

## Version 1 Safety Boundaries

- No live trading library is included.
- No private Binance API integration is required.
- Configuration lives in `.env`.
- `.env` is ignored by git.
- Symbol and interval inputs are validated with allowlists.
- HTTP errors and Binance rate-limit responses are handled explicitly.
- API secrets are not logged or stored in source code.

## Folder Structure

```text
tradingbot/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── src/
│   └── binance_paper_assistant/
│       ├── __init__.py
│       ├── backtesting.py
│       ├── cli.py
│       ├── config.py
│       ├── constants.py
│       ├── db.py
│       ├── indicators.py
│       ├── journal.py
│       ├── mcp_server.py
│       ├── main.py
│       ├── market_data.py
│       ├── reporting.py
│       ├── schema.sql
│       └── schemas.py
└── tests/
    ├── conftest.py
    ├── test_indicators.py
    └── test_journal.py
```

## Features

- Fetch public Binance spot candles for:
  - `BTCUSDT`
  - `ETHUSDT`
  - `BNBUSDT`
  - `SOLUSDT`
  - `XRPUSDT`
- Supported intervals:
  - `15m`
  - `1h`
  - `4h`
  - `1d`
- Indicators:
  - `EMA3`
  - `EMA8`
  - `EMA17`
  - `EMA20`
  - `EMA50`
  - `EMA200`
  - `RSI14`
  - `MACD`
  - `Bollinger Bands`
  - `ATR14`
  - `Volume MA20`
- Structured market reports with:
  - trend
  - momentum
  - volatility
  - support and resistance estimates
  - bullish and bearish scenarios
  - trade idea only when minimum risk/reward is at least `1:2`
  - reasons not to trade
- Paper trading journal:
  - add trade idea
  - record entry
  - close trade
  - calculate PnL
  - calculate risk/reward
  - list open and closed trades
- Backtesting:
  - `EMA20/EMA50` crossover
  - `EMA3/EMA8/EMA17` crossover with RSI and MACD filters
  - optional RSI filter
  - win rate
  - total return
  - max drawdown
  - buy-and-hold comparison

## Local API Tools

The FastAPI app exposes these local read-only tools:

- `GET /tools/get_candles`
- `GET /tools/calculate_indicators`
- `GET /tools/generate_market_report`
- `POST /tools/add_paper_trade`
- `POST /tools/paper_trades/{trade_id}/record_entry`
- `POST /tools/close_paper_trade`
- `GET /tools/list_paper_trades`
- `GET /tools/backtest_strategy`

## Local MCP Tools

The MCP server exposes these local tools:

- `get_candles(symbol, interval, limit)`
- `calculate_indicators(symbol, interval, limit)`
- `generate_market_report(symbol, interval)`
- `add_paper_trade(symbol, side, entry, stop_loss, take_profit, thesis)`
- `record_paper_trade_entry(trade_id, actual_entry, notes)`
- `close_paper_trade(trade_id, exit_price, notes)`
- `list_paper_trades(status)`
- `backtest_strategy(symbol, interval, strategy_name)`

## Setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create your local environment file

```bash
cp .env.example .env
```

Version 1 does not need a Binance API key.

### 4. Run the local API server

```bash
PYTHONPATH=src uvicorn binance_paper_assistant.main:app --reload
```

The API docs will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 5. Run the local MCP server

For local process-based MCP clients:

```bash
PYTHONPATH=src python3 -m binance_paper_assistant.mcp_server
```

For MCP Inspector or HTTP-capable MCP clients:

```bash
PYTHONPATH=src python3 -m binance_paper_assistant.mcp_server --transport streamable-http --port 8001
```

HTTP clients can connect to [http://127.0.0.1:8001/mcp](http://127.0.0.1:8001/mcp).

There is also a tiny Python MCP client example in [examples/mcp_client.py](/Users/joey/Documents/RanDWork/tradingbot/examples/mcp_client.py):

```bash
PYTHONPATH=src python3 examples/mcp_client.py
```

## Example Commands

### CLI examples

```bash
PYTHONPATH=src python3 -m binance_paper_assistant.cli report BTCUSDT 1h
PYTHONPATH=src python3 -m binance_paper_assistant.cli watch BTCUSDT 15m
PYTHONPATH=src python3 -m binance_paper_assistant.cli candles ETHUSDT 4h --limit 120
PYTHONPATH=src python3 -m binance_paper_assistant.cli backtest BTCUSDT 1h ema20_ema50
PYTHONPATH=src python3 -m binance_paper_assistant.cli backtest SOLUSDT 4h ema20_ema50_rsi
PYTHONPATH=src python3 -m binance_paper_assistant.cli backtest BTCUSDT 15m ema3_ema8_ema17_rsi_macd
PYTHONPATH=src python3 -m binance_paper_assistant.cli add-trade BTCUSDT long 64000 62000 68000 "Educational setup only after support reclaim."
PYTHONPATH=src python3 -m binance_paper_assistant.cli record-entry 1 64150 --notes "Paper entry after confirmation candle."
PYTHONPATH=src python3 -m binance_paper_assistant.cli close-trade 1 67600 --notes "Paper exit into resistance."
PYTHONPATH=src python3 -m binance_paper_assistant.cli list-trades --status open
PYTHONPATH=src python3 -m binance_paper_assistant.cli list-trades --status closed
PYTHONPATH=src python3 -m binance_paper_assistant.mcp_server
PYTHONPATH=src python3 -m binance_paper_assistant.mcp_server --transport streamable-http --port 8001
```

Watch every 15 minutes and notify on a fresh paper-trade suggestion:

```bash
PYTHONPATH=src python3 -m binance_paper_assistant.cli watch BTCUSDT 15m
```

Useful watch options:

```bash
PYTHONPATH=src python3 -m binance_paper_assistant.cli watch BTCUSDT 15m --notify stdout
PYTHONPATH=src python3 -m binance_paper_assistant.cli watch BTCUSDT 15m --notify ntfy --ntfy-topic-url https://ntfy.sh/your-topic
PYTHONPATH=src python3 -m binance_paper_assistant.cli watch ETHUSDT 15m --poll-seconds 900
PYTHONPATH=src python3 -m binance_paper_assistant.cli watch SOLUSDT 15m --once --notify stdout
nohup env PYTHONPATH=src python3 -m binance_paper_assistant.cli watch BTCUSDT 15m > watch.log 2>&1 &
```

For cloud VMs, `ntfy.sh` is a better fit than desktop notifications. You can set it in `.env`:

```bash
NTFY_TOPIC_URL=https://ntfy.sh/your-topic
NTFY_ACCESS_TOKEN=
```

Then run:

```bash
PYTHONPATH=src python3 -m binance_paper_assistant.cli watch SOLUSDT 15m --notify ntfy
```

## Deploy On A Linux Server

Quick setup on a Linux server or VM:

```bash
git clone git@github.com:joeynor/tradingbot_advisor.git
cd tradingbot_advisor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Recommended `.env` values for a VM watcher:

```bash
REQUEST_TIMEOUT_SECONDS=30
NTFY_TOPIC_URL=https://ntfy.sh/your-topic
NTFY_ACCESS_TOKEN=
```

Run a one-off check:

```bash
PYTHONPATH=src python3 -m binance_paper_assistant.cli watch SOLUSDT 15m --once --notify ntfy
```

Run continuously in the background with `nohup`:

```bash
nohup env PYTHONPATH=src .venv/bin/python -m binance_paper_assistant.cli watch SOLUSDT 15m --notify ntfy > watch.log 2>&1 &
tail -f watch.log
```

For a proper always-on deployment that survives logout and reboot, use `systemd`.

Create a reusable service template:

```bash
sudo tee /etc/systemd/system/tradingbot-watch@.service > /dev/null <<'EOF'
[Unit]
Description=Tradingbot watcher for %i
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/root/tradingbot_advisor
Environment=PYTHONPATH=src
ExecStart=/root/tradingbot_advisor/.venv/bin/python -u -m binance_paper_assistant.cli watch SOLUSDT %i --notify ntfy
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF
```

Reload `systemd` and start the intervals you want:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tradingbot-watch@15m.service
sudo systemctl enable --now tradingbot-watch@1h.service
sudo systemctl enable --now tradingbot-watch@4h.service
sudo systemctl enable --now tradingbot-watch@1d.service
```

Check service status:

```bash
systemctl status tradingbot-watch@15m.service
systemctl status tradingbot-watch@1h.service
systemctl status tradingbot-watch@4h.service
systemctl status tradingbot-watch@1d.service
```

Follow logs:

```bash
journalctl -u tradingbot-watch@15m.service -f
journalctl -u tradingbot-watch@1h.service -f
journalctl -u tradingbot-watch@4h.service -f
journalctl -u tradingbot-watch@1d.service -f
```

Restart or stop a watcher:

```bash
sudo systemctl restart tradingbot-watch@15m.service
sudo systemctl stop tradingbot-watch@15m.service
```

Useful operational notes:

- The watcher only sends a notification when a fresh trade suggestion appears.
- If Binance times out, the process stays alive and logs the failure before trying again on the next cycle.
- `ntfy.sh` works well for server deployments because it does not depend on a local desktop session.
- If your server has flaky connectivity to Binance, increasing `REQUEST_TIMEOUT_SECONDS` to `30` or `45` is a reasonable first step.
- Use supported interval names exactly: `15m`, `1h`, `4h`, and `1d`.

### API examples

```bash
curl "http://127.0.0.1:8000/tools/get_candles?symbol=BTCUSDT&interval=1h&limit=200"
curl "http://127.0.0.1:8000/tools/calculate_indicators?symbol=ETHUSDT&interval=4h&limit=300"
curl "http://127.0.0.1:8000/tools/generate_market_report?symbol=SOLUSDT&interval=1h"
curl "http://127.0.0.1:8000/tools/list_paper_trades?status=closed"
curl "http://127.0.0.1:8000/tools/backtest_strategy?symbol=BTCUSDT&interval=1h&strategy_name=ema20_ema50_rsi"
curl "http://127.0.0.1:8000/tools/backtest_strategy?symbol=BTCUSDT&interval=15m&strategy_name=ema3_ema8_ema17_rsi_macd"
```

Add a paper trade:

```bash
curl -X POST "http://127.0.0.1:8000/tools/add_paper_trade" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "long",
    "entry": 64000,
    "stop_loss": 62000,
    "take_profit": 68000,
    "thesis": "Educational setup only based on trend alignment and support reclaim."
  }'
```

Close a paper trade:

```bash
curl -X POST "http://127.0.0.1:8000/tools/close_paper_trade?trade_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "exit_price": 67600,
    "notes": "Educational paper exit only."
  }'
```

## Example Market Report Output

```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "educational_only": true,
  "risk_warning": "For decision support and paper trading only. Do not execute live trades from this report.",
  "trend_condition": "Bullish but not fully aligned",
  "momentum_condition": "Bullish momentum",
  "volatility_condition": "Moderate volatility",
  "support_resistance_estimate": {
    "support": 63820.4,
    "resistance": 65750.9
  },
  "possible_trade_idea": {
    "side": "long",
    "label": "Educational / paper trading only",
    "entry_zone": [64210.2, 64531.6],
    "stop_loss": 63510.0,
    "take_profit": 65950.0,
    "invalidation_level": 63510.0,
    "risk_reward_ratio": 2.15
  },
  "reasons_not_to_trade": [
    "This is educational analysis only and not financial advice.",
    "Market structure may change quickly around macro news or low-liquidity hours.",
    "Public candle-based indicators lag price and can fail in chop.",
    "If invalidation is too wide for your risk tolerance, skip the setup."
  ]
}
```

## How To Inspect Paper Trading Results

- Use `list-trades --status open` to review current educational positions.
- Use `list-trades --status closed` to inspect completed paper trades and PnL.
- Open the SQLite database specified by `DATABASE_URL` if you want direct inspection.
- Review FastAPI responses in `/docs` for the same journal data.

## How To Add More Symbols Safely

1. Add the symbol to `SUPPORTED_SYMBOLS` in [constants.py](/Users/joey/tradingbot/src/binance_paper_assistant/constants.py).
2. Add the symbol to `SYMBOL_ALLOWLIST` in `.env`.
3. Restart the API server.
4. Keep additions limited to Binance **spot** symbols only in version 1.
5. Do not add margin, futures, leveraged tokens, or derivative markets to this project.

## Run Tests

```bash
PYTHONPATH=src pytest
```

## Notes For Future Safe Expansion

- If private Binance integration is ever added, keep it strictly read-only.
- Do not store secrets in source code.
- Keep write actions, trading actions, and withdrawals permanently out of scope unless the safety model changes explicitly.

## MCP Notes

- The MCP server uses the same internal service layer as the FastAPI app, so validation and safety rules stay aligned.
- Binance access remains public-data-only and read-only.
- The only local writes are to the SQLite paper-trading journal.

## EMA 3/8/17 Strategy Notes

- Strategy name: `ema3_ema8_ema17_rsi_macd`
- Entry signal: `EMA3` crossing above `EMA8` for longs, or below `EMA8` for shorts
- Trend filter: longs require `EMA8 > EMA17`, shorts require `EMA8 < EMA17`
- Momentum filter: longs require `RSI14 > 50` and `MACD > signal`; shorts require `RSI14 < 50` and `MACD < signal`
- Exit rule: opposite crossover
- Educational / paper trading only, and still not financial advice
