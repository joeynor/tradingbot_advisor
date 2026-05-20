"""Project constants and allowlists."""

SUPPORTED_SYMBOLS = {"BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"}
SUPPORTED_INTERVALS = {"15m", "1h", "4h", "1d"}
SUPPORTED_STRATEGIES = {"ema20_ema50", "ema20_ema50_rsi", "ema3_ema8_ema17_rsi_macd"}
SUPPORTED_SIDES = {"long", "short"}
MAX_CANDLE_LIMIT = 1000
MIN_CANDLE_LIMIT = 50
