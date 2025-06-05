-- PokéCertify Database Schema
-- Cards and Trades tables for card grading, verification, and trading

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY, -- UUID
    owner TEXT NOT NULL,
    card_name TEXT NOT NULL,
    card_info TEXT,
    grade TEXT NOT NULL,
    estimated_value REAL,
    image_path TEXT NOT NULL,
    date_added TEXT NOT NULL, -- ISO 8601 timestamp
    UNIQUE(id)
);

CREATE TABLE IF NOT EXISTS trades (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL,
    from_owner TEXT NOT NULL,
    to_owner TEXT NOT NULL,
    trade_date TEXT NOT NULL, -- ISO 8601 timestamp
    FOREIGN KEY(card_id) REFERENCES cards(id) ON DELETE CASCADE
);

-- Index for fast trade history lookup
CREATE INDEX IF NOT EXISTS idx_trades_card_id ON trades(card_id);

-- Index for fast owner lookup in cards
CREATE INDEX IF NOT EXISTS idx_cards_owner ON cards(owner);