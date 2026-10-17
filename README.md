# NSE Delivery Volume Dynamics & Institutional Accumulation

[![Daily/Weekly Delivery Dataset Update](https://github.com/prathmeshgupta/nse-delivery-volume-dynamics/actions/workflows/weekly_update.yml/badge.svg)](https://github.com/prathmeshgupta/nse-delivery-volume-dynamics/actions/workflows/weekly_update.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Institutional-grade time-series dataset of National Stock Exchange of India (NSE) security-wise **traded volume, deliverable quantity, delivery percentage, and turnover dynamics**. 

Designed to eliminate the severe retail intraday noise in Indian equities and identify true institutional accumulation and distribution footprints.

---

### The Quantitative Problem

In Indian equity markets, **over 70% to 80% of daily traded volume in liquid stocks is speculative intraday churn and arbitrage** that squares off by 3:30 PM IST. 

Standard OHLCV data treats a 1,000-share day-trade identically to a 1,000-share institutional custody delivery. This creates misleading volume indicators (OBV, VWAP, MFI) in quantitative backtests. 

This dataset provides the clean, audited historical delivery records from NSE Bhavcopy archives (`sec_bhavdata_full`), tracking:
* **Deliverable Quantity**: Shares transferred to Demat custody.
* **Delivery Percentage**: `deliverable_qty / traded_qty * 100`.
* **Delivery Turnover (₹ Cr)**: Exact institutional capital committed.

---

### Dataset Schema

Outputs are distributed in both **Apache Parquet (`snappy` compressed)** and standard **CSV**:
* `output/delivery_dynamics.parquet`
* `output/delivery_dynamics.csv`

| Field | Type | Description |
| :--- | :--- | :--- |
| `symbol` | `string` | NSE Trading Symbol (e.g. `RELIANCE`, `TCS`, `INFY`) |
| `series` | `string` | Trading series (`EQ` for regular equity, `BE` for Trade-to-Trade) |
| `trade_date` | `string` | Trade session date in `YYYY-MM-DD` |
| `prev_close` | `float` | Previous trading session closing price |
| `open_price` | `float` | Session opening price |
| `high_price` | `float` | Session intraday high |
| `low_price` | `float` | Session intraday low |
| `close_price` | `float` | Session official closing price |
| `traded_qty` | `int64` | Total volume executed across all market participants |
| `deliverable_qty` | `int64` | Quantity marked for mandatory physical/Demat delivery |
| `delivery_pct` | `float` | Proportion of traded quantity marked for delivery (`0.0%` to `100.0%`) |
| `turnover_cr` | `float` | Total turnover in ₹ Crore |
| `delivery_turnover_cr` | `float` | Capital committed in delivery turnover in ₹ Crore |
| `source` | `string` | Data source origin (`NSE_SEC_BHAVDATA_FULL`) |

---

### Automated Weekly & Daily Updates

The dataset is kept fresh via a scheduled **GitHub Actions workflow**:
* **Schedule**: Runs automatically at **14:00 UTC (19:30 IST) Monday to Friday** after NSE Bhavcopy publication, with a weekly Sunday reconciliation at **02:00 UTC**.
* **Self-Healing Gap Fill**: Inspects the latest indexed `trade_date` and automatically backfills any missing trading sessions.
* **Circuit Breaker**: Pre-commit validation ensures zero nulls in primary keys before committing to Git.

---

### Quickstart & CLI Usage

```bash
# 1. Clone the repository
git clone https://github.com/prathmeshgupta/nse-delivery-volume-dynamics.git
cd nse-delivery-volume-dynamics

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the automated updater locally
python update.py

# 4. Query delivery history for a ticker
python runner.py --symbol RELIANCE

# 5. Screen for highest institutional delivery % (Min ₹10 Cr turnover)
python runner.py --top-delivery --min-turnover 10.0
```

---

### Research & Factor Signals

1. **Institutional Accumulation Surge:**
   $$\text{Signal} = (\text{Delivery \%} \ge 50\%) \land (\text{Traded Qty} \ge 1.5 \times \text{SMA}_{20}) \land (\Delta P > 0)$$
2. **Exhaustion / Retail Traps:**
   Rising prices accompanied by collapsing delivery % (<20%) indicating speculative retail frenzy without institutional participation.
