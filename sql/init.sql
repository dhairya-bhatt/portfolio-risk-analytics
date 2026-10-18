-- ============================================================================
-- Portfolio Risk Analytics Service - PostgreSQL 16 Schema Initialization
-- ============================================================================

-- Drop tables if re-initializing (reverse dependency order)
DROP TABLE IF EXISTS holdings CASCADE;
DROP TABLE IF EXISTS portfolios CASCADE;
DROP TABLE IF EXISTS prices CASCADE;
DROP TABLE IF EXISTS instruments CASCADE;
DROP TABLE IF EXISTS ingestion_runs CASCADE;

-- ----------------------------------------------------------------------------
-- 1. instruments
-- Represents tradable assets (ETFs).
-- ----------------------------------------------------------------------------
CREATE TABLE instruments (
    id SERIAL PRIMARY KEY,
    -- Ticker symbol must be unique and non-null (e.g. 'SPY', 'AGG').
    ticker TEXT UNIQUE NOT NULL,
    -- Full descriptive name of the instrument.
    name TEXT NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2. prices
-- Stores daily adjusted close prices for instruments.
-- ----------------------------------------------------------------------------
CREATE TABLE prices (
    instrument_id INT NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    -- NUMERIC(18,6) prevents binary floating-point inaccuracy.
    -- CHECK (adj_close > 0) strictly guarantees prices are strictly positive,
    -- preventing division-by-zero or undefined logarithm/simple returns.
    adj_close NUMERIC(18,6) NOT NULL CHECK (adj_close > 0),
    -- Composite Primary Key guarantees at most one price record per instrument per day.
    PRIMARY KEY (instrument_id, date)
);

-- Index on prices(date):
-- RATIONALE: Risk queries fetch cross-sectional returns for all portfolio assets
-- across a date window (e.g., WHERE date BETWEEN :start AND :end).
-- While the composite primary key index indexes (instrument_id, date),
-- this single-column index enables fast range scans and date-alignment across instruments.
CREATE INDEX idx_prices_date ON prices(date);

-- ----------------------------------------------------------------------------
-- 3. portfolios
-- Named collections of asset allocations.
-- ----------------------------------------------------------------------------
CREATE TABLE portfolios (
    id SERIAL PRIMARY KEY,
    -- Unique constraint ensures distinct portfolio names.
    name TEXT UNIQUE NOT NULL
);

-- ----------------------------------------------------------------------------
-- 4. holdings
-- Defines the asset weights for each portfolio.
-- ----------------------------------------------------------------------------
CREATE TABLE holdings (
    portfolio_id INT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    instrument_id INT NOT NULL REFERENCES instruments(id) ON DELETE RESTRICT,
    -- CHECK (weight >= 0 AND weight <= 1) enforces a long-only portfolio constraint
    -- (no short positions) and ensures no single holding exceeds 100%.
    -- High numeric scale (8 decimal places) prevents truncation rounding errors.
    weight NUMERIC(10,8) NOT NULL CHECK (weight >= 0 AND weight <= 1),
    -- Composite PK prevents duplicate ticker entries within the same portfolio.
    PRIMARY KEY (portfolio_id, instrument_id)
);

-- ----------------------------------------------------------------------------
-- 5. ingestion_runs
-- Data provenance and audit log recording every ETL pipeline execution.
-- ----------------------------------------------------------------------------
CREATE TABLE ingestion_runs (
    id SERIAL PRIMARY KEY,
    -- Source identifier (e.g. 'yfinance', 'stooq', 'synthetic').
    source TEXT NOT NULL,
    ticker TEXT NOT NULL,
    -- Timezone-aware timestamp recording exact execution time.
    downloaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Count of valid rows inserted into prices.
    rows_loaded INT NOT NULL,
    -- Date boundaries of the ingested series.
    first_date DATE,
    last_date DATE,
    -- Count of malformed/invalid/duplicate rows discarded during validation.
    rows_rejected INT NOT NULL DEFAULT 0,
    -- Audit trail for gap detection and rejection reasons.
    notes TEXT
);
