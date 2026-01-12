The scraper supports PostgreSQL/Supabase for persistent data storage.

### Entity Relationship Diagram

```mermaid
erDiagram
    providers ||--o{ etfs : "has"
    etfs ||--o{ etf_daily_data : "has"
    etfs ||--o{ etf_flows : "has"
    btc_prices ||--o| etf_daily_data : "referenced by"
    
    providers {
        int id PK
        varchar name UK
        varchar website
        varchar country
        timestamp created_at
    }
    
    etfs {
        int id PK
        varchar ticker UK
        varchar name
        int provider_id FK
        varchar market
        date launch_date
        boolean is_active
        timestamp created_at
    }
    
    etf_daily_data {
        bigint id PK
        int etf_id FK
        date date
        decimal nav
        decimal market_price
        bigint shares_outstanding
        decimal holdings_btc
        bigint volume
        decimal premium_discount
        timestamp created_at
        timestamp updated_at
    }
    
    etf_flows {
        bigint id PK
        date date
        int etf_id FK
        decimal flow_btc
        decimal flow_usd
        varchar source
        timestamp created_at
    }
    
    btc_prices {
        bigint id PK
        date date UK
        decimal price_usd
        varchar source
        timestamp created_at
    }
    
    scrape_logs {
        bigint id PK
        timestamp started_at
        timestamp finished_at
        varchar status
        int etfs_processed
        int etfs_failed
        text error_message
        int execution_time_seconds
    }
```

### Tables Overview

| Table | Description | Records |
|-------|-------------|---------|
| `providers` | ETF issuers (Grayscale, BlackRock, etc.) | 13 |
| `etfs` | Bitcoin ETF products | 14 |
| `etf_daily_data` | Daily NAV, price, holdings per ETF | Growing |
| `etf_flows` | Daily BTC flows from CoinMarketCap | Growing |
| `btc_prices` | Historical BTC prices (USD) | Growing |
| `scrape_logs` | Scraper execution history | Growing |

### Views

- `v_etf_summary` - Daily summary of all ETFs with calculated AUM
- `v_etf_latest` - Most recent data for each ETF

### Duplicate Prevention

All tables use `UPSERT` with `ON CONFLICT` to prevent duplicates:
- `etf_daily_data`: Unique constraint on `(etf_id, date)`
- `etf_flows`: Unique constraint on `(etf_id, date)`
- `btc_prices`: Unique constraint on `date`