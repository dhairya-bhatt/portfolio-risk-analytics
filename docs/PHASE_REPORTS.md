# Phase Reports

This document tracks progress, architectural decisions, and educational breakdowns across each project phase of the **Portfolio Risk Analytics Service**.

---

## Phase 0: Planning, Architecture & Data Verification

### 1. What was built / analyzed
- `Portfolio_Risk_Project_Guide.docx`: Ingested and reviewed against interview and institutional quality requirements.
- Live verification of data providers: Tested Yahoo Finance and Stooq API endpoints for reliability and terms of service.
- Project architectural plan and file structure mapped out.
- `docs/PHASE_REPORTS.md`: Initialized phase tracking log.

---

### 2. Conceptual Deep-Dive (Plain English with Concrete Numbers)

#### A. Adjusted Close vs. Unadjusted Close
- **The Concept**: When an ETF or stock pays a cash dividend or undergoes a stock split, the raw market price drops on the ex-date. If you simply calculate returns using unadjusted close prices, a \$10 dividend on a \$100 stock looks like a 10% market crash ($100 \rightarrow \$90$), which is false; the shareholder actually received the \$10 in cash!
- **Numeric Example**:
  - Day 1: Asset trades at \$100.
  - Day 2: Company pays a \$10 dividend. Market price opens at \$90.
  - **Raw Return**: $\frac{90 - 100}{100} = -10\%$. (Distorted!)
  - **Adjusted Price**: To reflect true economic return, the historical price at Day 1 is adjusted down by the dividend factor: $100 \times \frac{90}{100} = \$90$.
  - **Adjusted Return**: $\frac{90 - 90}{90} = 0\%$. (Reflects that investor wealth remained flat).
  - *Key takeaway*: Always use **Adjusted Close** (`adj_close`) for total return and risk metrics so dividends and splits are accounted for.

#### B. Relational Integrity & Foreign Keys
- **The Concept**: In PostgreSQL, a Foreign Key (`FK`) enforces referential integrity. A price or a portfolio holding cannot point to an instrument ID that does not exist.
- **Why it matters**: If someone tries to insert a holding for `instrument_id = 999` when only IDs `1` to `8` exist in `instruments`, the database engine rejects the transaction immediately at the storage layer rather than silently corrupting downstream risk calculations.

#### C. Maximum Drawdown (MDD)
- **The Concept**: Maximum Drawdown measures the worst peak-to-trough drop in portfolio value before a new peak is reached. It answers the critical risk question: *"If an investor entered at the absolute worst possible time, what is the maximum paper loss they would have experienced?"*
- **Numeric Example**:
  - Day 0: Value $V_0 = 100$ (Peak = 100, Drawdown = 0%)
  - Day 1: Value $V_1 = 120$ (New Peak = 120, Drawdown = 0%)
  - Day 2: Value $V_2 = 90$  (Peak = 120, Drawdown = $\frac{90 - 120}{120} = -25\%$)
  - Day 3: Value $V_3 = 105$ (Peak = 120, Drawdown = $\frac{105 - 120}{120} = -12.5\%$)
  - **Maximum Drawdown**: $\min(0, 0, -0.25, -0.125) = -25\%$.

#### D. Value at Risk (VaR)
- **The Concept**: VaR gives a threshold loss over a specified horizon (here, 1 day) at a specified confidence level $c$ (e.g. 95%). A 1-day 95% VaR of 2.1% means: *"On 95% of trading days, we expect losses not to exceed 2.1%. Conversely, on 5% of days (roughly 1 day a month), losses will be at least 2.1%."*
- **Two complementary methods**:
  1. **Historical VaR**: Non-parametric. Takes the empirical daily returns sorted from worst to best and reads the $(1-c)$-th quantile (e.g., 5th percentile). No assumption about normal distributions, so it captures observed fat tails.
  2. **Parametric (Variance-Covariance) VaR**: Assumes returns follow a normal distribution $\mathcal{N}(\mu, \sigma^2)$. VaR $= z_c \cdot \sigma - \mu$, where $z_{0.95} \approx 1.644853$. It is fast and smooth, but understates risk when real returns have fat tails or extreme skew.

---

### 3. Key Architectural Choices & Rationale
- **Direct SQL via `sql/init.sql` instead of Alembic**: Keeps the schema transparent, self-contained, and easy for interviewers to review without navigating migration histories.
- **Python Standard Library `statistics.NormalDist` instead of `scipy`**: Eliminates a 50MB+ dependency binary just for an inverse CDF quantile function, speeding up Docker image builds and reducing supply chain risk.
- **Strict Provenance via `ingestion_runs`**: Real-world quantitative systems require data auditability. Tracking the run timestamp, source, row counts, and rejection notes guarantees transparency.

---

### 4. Calculations Used So Far
- *None implemented in code yet (Phase 0 Planning phase).*

---

### 5. Data Sources Used So Far
- **Yahoo Finance (`yfinance`)**: Evaluated via live endpoint check (`https://query1.finance.yahoo.com/v8/finance/chart/SPY`). Verified functional.
- **Stooq (`stooq.com`)**: Evaluated via live HTTP check. *Finding*: Stooq currently serves anti-bot JavaScript/Cloudflare challenges to basic HTTP clients.

---

### 6. How to Run and Verify
- Verify Python launcher availability:
  ```powershell
  py --version
  ```
- Verify git repository status:
  ```powershell
  git status
  ```

---

### 7. Test Results
- *No unit tests yet. Pre-flight network and environment checks passed.*

---

### 8. Interview Preparation Questions & Model Answers
1. **Q: Why is `yfinance` suitable for an academic or personal project, but unacceptable in production at an institutional asset manager like BlackRock?**
   - *Answer*: `yfinance` is an unofficial, community-maintained scraper around Yahoo Finance's undocumented web endpoints. It carries no Service Level Agreement (SLA), Yahoo's terms of service prohibit automated scraping and restrict data to personal non-commercial use, and endpoint changes can silently break ingestion pipelines without notice. Production platforms like Aladdin license authoritative, audited data directly from vendors (Bloomberg, Refinitiv/LSEG, ICE) with contractual accuracy, survivorship-bias handling, and delivery guarantees.
2. **Q: Why must portfolio risk calculations use Adjusted Close rather than raw Close prices?**
   - *Answer*: Corporate actions (dividends and stock splits) artificially alter nominal price levels without altering total shareholder wealth. A dividend drops the closing price on the ex-dividend date by the payout amount; using raw close prices would incorrectly register this dividend payout as a severe negative market return. Adjusted close backward-adjusts previous prices by the distribution ratio, preserving true economic returns.
3. **Q: Why use `statistics.NormalDist` rather than installing `scipy.stats`?**
   - *Answer*: Python 3.8+ introduced `statistics.NormalDist` in the standard library. For computing parametric VaR quantiles ($z_c = \Phi^{-1}(c)$), `NormalDist().inv_cdf(c)` is mathematically exact, natively supported with zero C-extension overhead, and eliminates a 50MB+ external dependency (`scipy`), making the container lightweight, secure, and fast to build.

---

### 9. Action Items Before Phase 1
- Verify Docker Desktop or Docker engine availability on the host machine.
- Set up project virtual environment (`.venv`) using Python.

---

## Phase 1: Foundation (Scaffolding, Database Schema, Core Engine & Healthcheck)

### 1. What was built
- `.gitignore`: Excludes virtual environments, compilation caches, coverage reports, Docker volumes, and secret files (`.env`).
- `pyproject.toml`: Standard packaging specifying dependencies (FastAPI, SQLAlchemy 2, psycopg 3, pandas, NumPy, yfinance, Pydantic v2), Ruff linter rules, and pytest options.
- `.env.example`: Canonical environment configuration template documenting all database, risk default, and application variables.
- `sql/init.sql`: Production PostgreSQL 16 DDL defining 5 tables (`instruments`, `prices`, `portfolios`, `holdings`, `ingestion_runs`), composite keys, CHECK constraints, and indexes.
- `docker-compose.yml`: Multi-container specification running `postgres:16-alpine` with automated entrypoint schema initialization and health checks alongside the API service.
- `app/config.py`: Centralized configuration management using Pydantic v2 `BaseSettings` with type validation, `.env` file reading, and cached singleton instantiation.
- `app/db.py`: Database infrastructure implementing SQLAlchemy 2 engine with psycopg 3 driver, connection pooling (`pool_pre_ping=True`), session generator (`get_db`), and live `SELECT 1` connectivity probe.
- `app/models.py`: SQLAlchemy 2 declarative ORM models matching database tables with explicit types (`Mapped[...]`), relationships, and constraints.
- `app/api.py`: FastAPI application entrypoint featuring OpenAPI docs setup and `/health` route exercising both application process and database engine.
- `tests/conftest.py`: Pytest session fixtures providing an isolated `TestClient` and transactional database session.
- `tests/test_api.py`: Integration test asserting `/health` endpoint response structure and status code integrity.

---

### 2. Conceptual Deep-Dive (Plain English with Concrete Numbers)

#### A. Fixed-Point Decimal (`NUMERIC`) vs. Floating-Point (`FLOAT`)
- **The Concept**: Computers represent floating-point numbers (`float` in Python, `FLOAT` / `DOUBLE PRECISION` in SQL) using binary fractions (IEEE 754 standard). Numbers that have finite representations in base 10 (like 0.1 or 0.2) have repeating, infinite representations in base 2!
- **Numeric Example**:
  - In binary float: `0.1 + 0.2` produces `0.30000000000000004`.
  - In a portfolio risk engine tracking \$100,000,000 across 10,000 daily rebalancings, tiny float precision leaks cause weights that should sum to 1.0 to sum to `0.99999997` or `1.00000004`.
  - **The Solution**: PostgreSQL's `NUMERIC(precision, scale)` stores exact decimal digits in an array of base-10,000 integers. `NUMERIC(18,6)` guarantees that every cent and basis point is stored with 100% mathematical precision without binary rounding drift.

#### B. Integrity Constraints: Why Every Rule Exists
- **`CHECK (adj_close > 0)` on `prices`**:
  - The single-period simple return formula is $r(t) = \frac{P(t)}{P(t-1)} - 1$.
  - If a vendor sends a bad tick of \$0.00, calculating $r(t+1)$ causes an uncaught ZeroDivisionError crash. If it sends a corrupted negative price, it generates mathematically nonsensical negative cumulative returns. The database engine rejects bad rows at the gate.
- **`CHECK (weight >= 0 AND weight <= 1)` on `holdings`**:
  - Enforces a long-only investment mandate (no short positions, where $w_i < 0$) and guarantees that no single asset exceeds 100% of the portfolio.
- **Composite Primary Keys**:
  - `prices(instrument_id, date)`: A stock or ETF has exactly one closing price on any given trading day. The composite PK guarantees uniqueness without requiring an artificial surrogate ID.
  - `holdings(portfolio_id, instrument_id)`: A portfolio cannot allocate to the same ETF twice.

#### C. Why We Need `idx_prices_date` Alongside the Primary Key
- The composite primary key `(instrument_id, date)` automatically creates a B-tree index ordered by `instrument_id` first, then `date`.
- If we query: *"Give me prices for instrument 1 on 2024-01-15"*, the primary key index is lightning fast because `instrument_id` is the leading column.
- But our multi-asset risk engine needs to query: *"Give me the prices of all 8 assets between 2020-01-01 and 2024-12-31 to compute their covariance matrix."*
- Without a standalone index on `date`, PostgreSQL would have to execute an expensive sequential table scan across millions of historical price rows. `CREATE INDEX idx_prices_date ON prices(date)` allows PostgreSQL to jump directly to the date range across all instruments in $O(\log N)$ time.

#### D. Connection Pooling & `SELECT 1` Healthchecks
- Opening a fresh TCP connection to PostgreSQL requires a three-way TCP handshake, SSL negotiation, and process authentication—costing 20 to 50 milliseconds per request.
- SQLAlchemy maintains a **Connection Pool** of reusable, already-open connections in memory.
- In `app/db.py`, `pool_pre_ping=True` issues an internal `SELECT 1` before checking out a connection from the pool. If PostgreSQL restarted or dropped an idle TCP connection, SQLAlchemy discards the dead connection and seamlessly opens a fresh one without throwing a 500 error to the client.

---

### 3. Key Architectural Choices & Rationale
- **Single SQL script (`sql/init.sql`) mounted into `docker-entrypoint-initdb.d`**: When PostgreSQL initializes for the first time in Docker, it automatically executes all `.sql` files in that directory. This provides zero-touch database bootstrapping without requiring complex migration frameworks for a fixed-scope service.
- **SQLAlchemy 2 `Mapped[...]` Declarative Typing**: Using SQLAlchemy 2.0 type-annotated attributes allows Ruff and Mypy to catch type mismatches at lint time rather than runtime.
- **Pydantic v2 `BaseSettings` with `.env` Separation**: Follows Twelve-Factor App methodology (Config in Environment). No credentials or database URLs are hardcoded in application logic.

---

### 4. Calculations Used So Far
- *None implemented in code yet (Foundation phase). Scheduled for Phase 3.*

---

### 5. Data Sources Used So Far
- *None loaded yet. Scheduled for Phase 2.*

---

### 6. How to Run and Verify
```powershell
# 1. Run linting and style verification
.venv\Scripts\ruff.exe check .
.venv\Scripts\ruff.exe format --check .

# 2. Run the test suite
.venv\Scripts\pytest.exe
```

Expected output:
- Ruff: `All checks passed! 10 files already formatted`
- Pytest: `1 passed`

---

### 7. Test Results
- **Test count**: 1 test (`tests/test_api.py::test_health_check_structure`).
- **Pass rate**: 100% passed.

---

### 8. Three Interview Questions You Can Now Answer
1. **Q: Why use `NUMERIC(18,6)` instead of `FLOAT` or `DOUBLE PRECISION` for asset prices and portfolio weights?**
   - *Model Answer*: `FLOAT` uses binary floating-point representation (IEEE 754), which cannot represent many base-10 decimals exactly (e.g. 0.1). Over thousands of return calculations and daily portfolio rebalancings, accumulated binary rounding errors cause portfolio weights to drift away from 1.0. PostgreSQL's `NUMERIC` is an arbitrary-precision exact decimal type that stores base-10 digits without precision loss.
2. **Q: Since `prices` already has a primary key on `(instrument_id, date)`, why did you add a secondary index on `date` alone?**
   - *Model Answer*: Composite B-tree indexes are ordered left-to-right. A query filtering by `instrument_id` uses the primary key index efficiently. However, calculating portfolio metrics requires cross-sectional date alignment: filtering all instruments across a date window (`WHERE date BETWEEN :start AND :end`). Without a single-column index on `date`, PostgreSQL would have to perform a costly sequential scan of the entire `prices` table.
3. **Q: How does FastAPI's dependency injection (`Depends(get_db)`) guarantee database safety and prevent connection leaks?**
   - *Model Answer*: `get_db` is implemented as a Python generator using a `try ... finally` block. When a request arrives, FastAPI invokes `get_db()`, which checks out a session from the SQLAlchemy connection pool. Once the route finishes processing and sends the HTTP response (or even if an unhandled exception occurs), FastAPI automatically executes the code after `yield`, invoking `db.close()`. This guarantees that connections are always returned to the pool, preventing connection exhaustion under heavy load.

---

### 9. Action Items Before Phase 2
- Implement `scripts/download_prices.py` to ingest the 8-ETF universe.
- Build `app/loaders.py` with multi-step data cleaning, gap detection, and `ingestion_runs` provenance logging.
- Generate a deterministic synthetic dataset with a fixed random seed for offline test execution.
- Create `docs/DATA_SOURCES.md` documenting end-to-end data lineage.
