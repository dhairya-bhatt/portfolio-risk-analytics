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
