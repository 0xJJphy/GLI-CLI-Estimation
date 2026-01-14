"""
JSON Schema for Currencies Domain

Maps to future PostgreSQL tables:
- domain_currencies_dxy (daily DXY metrics)
- domain_currencies_pairs (daily FX pair metrics)
"""

CURRENCIES_SCHEMA = {
    "type": "object",
    "required": ["dates", "dxy", "pairs", "btc"],
    "properties": {
        "dates": {
            "type": "array",
            "items": {"type": "string", "format": "date"}
        },
        "dxy": {
            "type": "object",
            "properties": {
                "absolute": {"type": "array", "items": {"type": ["number", "null"]}},
                "roc_7d": {"type": "array", "items": {"type": ["number", "null"]}},
                "roc_30d": {"type": "array", "items": {"type": ["number", "null"]}},
                "roc_90d": {"type": "array", "items": {"type": ["number", "null"]}},
                "roc_180d": {"type": "array", "items": {"type": ["number", "null"]}},
                "roc_yoy": {"type": "array", "items": {"type": ["number", "null"]}},
                "roc_7d_z": {"type": "array", "items": {"type": ["number", "null"]}},
                "roc_30d_z": {"type": "array", "items": {"type": ["number", "null"]}},
                "roc_90d_z": {"type": "array", "items": {"type": ["number", "null"]}},
                "roc_180d_z": {"type": "array", "items": {"type": ["number", "null"]}},
                "roc_7d_pct": {"type": "array", "items": {"type": ["number", "null"]}},
                "roc_30d_pct": {"type": "array", "items": {"type": ["number", "null"]}},
                "roc_90d_pct": {"type": "array", "items": {"type": ["number", "null"]}},
                "roc_180d_pct": {"type": "array", "items": {"type": ["number", "null"]}},
                "volatility": {"type": "array", "items": {"type": ["number", "null"]}}
            }
        },
        "pairs": {
            "type": "object",
            "patternProperties": {
                "^[A-Z]{3}$": {
                    "type": "object",
                    "properties": {
                        "absolute": {"type": "array"},
                        "roc_7d": {"type": "array"},
                        "roc_30d": {"type": "array"},
                        "roc_90d": {"type": "array"},
                        "roc_180d": {"type": "array"},
                        "roc_yoy": {"type": "array"}
                    }
                }
            }
        },
        "btc": {
            "type": "object",
            "properties": {
                "absolute": {"type": "array"},
                "roc_7d": {"type": "array"},
                "roc_30d": {"type": "array"},
                "roc_90d": {"type": "array"},
                "roc_180d": {"type": "array"},
                "roc_yoy": {"type": "array"}
            }
        }
    }
}

# PostgreSQL DDL for future migration
CURRENCIES_DDL = """
-- DXY Daily Metrics
CREATE TABLE IF NOT EXISTS domain_currencies_dxy (
    date DATE PRIMARY KEY,
    absolute DECIMAL(10, 4),
    roc_7d DECIMAL(8, 4),
    roc_30d DECIMAL(8, 4),
    roc_90d DECIMAL(8, 4),
    roc_180d DECIMAL(8, 4),
    roc_yoy DECIMAL(8, 4),
    roc_7d_z DECIMAL(8, 4),
    roc_30d_z DECIMAL(8, 4),
    roc_90d_z DECIMAL(8, 4),
    roc_180d_z DECIMAL(8, 4),
    roc_7d_pct DECIMAL(6, 2),
    roc_30d_pct DECIMAL(6, 2),
    roc_90d_pct DECIMAL(6, 2),
    roc_180d_pct DECIMAL(6, 2),
    volatility DECIMAL(8, 4),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- FX Pairs Daily Metrics  
CREATE TABLE IF NOT EXISTS domain_currencies_pairs (
    date DATE,
    pair VARCHAR(3),  -- EUR, JPY, GBP, etc.
    absolute DECIMAL(12, 6),
    roc_7d DECIMAL(8, 4),
    roc_30d DECIMAL(8, 4),
    roc_90d DECIMAL(8, 4),
    roc_180d DECIMAL(8, 4),
    roc_yoy DECIMAL(8, 4),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (date, pair)
);

-- Indexes for time-series queries
CREATE INDEX IF NOT EXISTS idx_currencies_dxy_date ON domain_currencies_dxy(date DESC);
CREATE INDEX IF NOT EXISTS idx_currencies_pairs_date ON domain_currencies_pairs(date DESC);
"""
