CREATE TABLE IF NOT EXISTS paper_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('long', 'short')),
    entry REAL NOT NULL,
    stop_loss REAL NOT NULL,
    take_profit REAL NOT NULL,
    thesis TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'idea',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    opened_at TEXT,
    closed_at TEXT,
    actual_entry REAL,
    actual_exit REAL,
    notes TEXT,
    risk_reward_ratio REAL,
    pnl_amount REAL,
    pnl_percent REAL,
    educational_only INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_paper_trades_status ON paper_trades(status);
CREATE INDEX IF NOT EXISTS idx_paper_trades_symbol ON paper_trades(symbol);

