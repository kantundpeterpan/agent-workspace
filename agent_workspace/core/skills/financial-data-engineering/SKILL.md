---
name: financial-data-engineering
description: API sourcing from yfinance, FRED, Alpha Vantage; data cleaning, alignment, feature engineering, and pipeline design for financial analysis
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Financial Data Engineering

Workflows for sourcing, cleaning, and engineering financial data for downstream analysis.

## When to Use

- Fetching market data from financial APIs
- Cleaning and aligning multi-source datasets
- Building feature pipelines for quantitative strategies
- Designing data versioning and storage schemas
- Ensuring data quality for backtesting and modelling

## Data Sources

### yfinance (Yahoo Finance)
Free, comprehensive equity data including prices and financials.

```python
import yfinance as yf

# Single ticker
aapl = yf.Ticker("AAPL")
hist = aapl.history(period="5y", interval="1d")
info = aapl.info  # Company metadata
financials = aapl.financials  # Annual income statement
balance = aapl.balance_sheet
cashflow = aapl.cashflow

# Multiple tickers
data = yf.download(["AAPL", "MSFT", "GOOGL"], start="2020-01-01")

# Dividends and splits
aapl.dividends
aapl.splits
```

**Limitations**: data may be delayed, no point-in-time guarantee, survivorship bias in historical universes, rate limiting.

### FRED (Federal Reserve Economic Data)
Macroeconomic time series from the St. Louis Fed.

```python
from fredapi import Fred
import os

fred = Fred(api_key=os.environ.get("FRED_API_KEY"))

gdp = fred.get_series("GDP")  # Nominal GDP (quarterly)
cpi = fred.get_series("CPIAUCSL")  # CPI All Urban (monthly)
unrate = fred.get_series("UNRATE")  # Unemployment rate
dgs10 = fred.get_series("DGS10")  # 10Y Treasury (daily)
dgs2 = fred.get_series("DGS2")  # 2Y Treasury
t10yie = fred.get_series("T10YIE")  # 10Y breakeven inflation
sp500 = fred.get_series("SP500")  # S&P 500 index
```

Key FRED series IDs:
| Series | Description | Frequency |
|--------|-------------|-----------|
| GDP | Gross Domestic Product | Quarterly |
| GDPC1 | Real GDP | Quarterly |
| CPIAUCSL | CPI All Urban Consumers | Monthly |
| PCEPILFE | Core PCE (ex food & energy) | Monthly |
| UNRATE | Unemployment Rate | Monthly |
| PAYEMS | Nonfarm Payrolls | Monthly |
| DGS10 | 10Y Treasury Constant Maturity | Daily |
| DGS2 | 2Y Treasury Constant Maturity | Daily |
| T10Y2Y | 10Y-2Y Treasury Spread | Daily |
| VIXCLS | VIX (CBOE Volatility Index) | Daily |
| FEDFUNDS | Effective Federal Funds Rate | Monthly |
| SP500 | S&P 500 Index | Daily |

### Alpha Vantage
Equities, FX, crypto, and technical indicators.

```python
import requests

API_KEY = os.environ.get("ALPHA_VANTAGE_KEY")
BASE_URL = "https://www.alphavantage.co/query"

params = {
    "function": "TIME_SERIES_DAILY_ADJUSTED",
    "symbol": "IBM",
    "apikey": API_KEY,
    "outputsize": "full",
}
r = requests.get(BASE_URL, params=params)
data = r.json()
```

**Free tier**: 25 requests/day, 5 calls/minute.

## Data Pipeline Design

### ETL Pattern
```
[API Sources] → Extract → Transform → Load → [Data Store] → Feature Engineering → [Feature Store]
                    ↑ Caching Layer ↓                              ↓
              [Cache Files]                               [Data Quality Checks]
```

### Caching Strategy
```python
import pickle
from pathlib import Path
from datetime import datetime, timedelta

CACHE_DIR = Path("data/cache")

def cached_fetch(fetch_func, cache_key, max_age_hours=24):
    """Fetch with file-based cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{cache_key}.pkl"

    if cache_path.exists():
        age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if age < timedelta(hours=max_age_hours):
            with open(cache_path, "rb") as f:
                return pickle.load(f)

    data = fetch_func()
    with open(cache_path, "wb") as f:
        pickle.dump(data, f)

    return data
```

### Rate Limiting

```python
import time
from functools import wraps

def rate_limit(calls_per_minute):
    min_interval = 60.0 / calls_per_minute
    last_call = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            result = func(*args, **kwargs)
            last_call[0] = time.time()
            return result
        return wrapper
    return decorator
```

## Data Cleaning

### Common Issues & Solutions
| Issue | Detection | Solution |
|-------|-----------|----------|
| Missing dates | `date_range.difference(df.index)` | Forward-fill or skip (depends on analysis) |
| Duplicate rows | `df.index.duplicated().sum()` | Keep last or aggregate |
| Price spikes | Z-score > 5 or % change > 50% on liquid stock | Flag for review; check for splits |
| Zero/negative prices | `(df['close'] <= 0).sum()` | Remove or flag |
| Survivorship bias | Missing delisted stocks in historical data | Source point-in-time data |
| Currency mismatch | Manual review | Convert to common base currency |
| Corporate actions | Price jump without corresponding volume spike | Adjust with split/dividend data |

### Standard Cleaning Pipeline
```python
def clean_price_data(df, ticker_col='ticker', date_col='date',
                     price_cols=['open', 'high', 'low', 'close', 'volume']):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.drop_duplicates(subset=[ticker_col, date_col])
    df = df.sort_values([ticker_col, date_col])

    for col in price_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Remove rows where close = 0 or negative
    if 'close' in df.columns:
        df = df[df['close'] > 0]

    # Flag price spikes (>20% daily change on liquid stocks)
    if 'close' in df.columns:
        df['ret'] = df.groupby(ticker_col)['close'].pct_change()
        df['spike_flag'] = df['ret'].abs() > 0.20
        df.drop(columns=['ret'], inplace=True)

    return df
```

## Data Alignment

### Aligning Multi-Frequency Data
```python
def align_dataframes(df_daily, df_quarterly, date_col='date'):
    """Forward-fill quarterly data to daily frequency."""
    # Ensure both have date index
    daily = df_daily.set_index(date_col)
    quarterly = df_quarterly.set_index(date_col)

    # Reindex quarterly to daily and forward-fill
    quarterly_daily = quarterly.reindex(daily.index, method='ffill')

    # Combine
    combined = daily.join(quarterly_daily, rsuffix='_q')
    return combined
```

### Handling Different Calendars
- US equities: NYSE calendar (≈252 trading days/year)
- Fixed income: SIFMA calendar
- FX/commodities: 24/5 or 24/7
- FRED macros: Monthly or quarterly with specific release dates
- Solution: reindex to common calendar, forward-fill macros

## Feature Engineering

### Returns
```python
def compute_returns(df, price_col='close', periods=[1, 5, 21, 63, 126, 252]):
    for p in periods:
        df[f'ret_{p}d'] = df.groupby('ticker')[price_col].pct_change(p)
    df['log_ret'] = np.log(df[price_col] / df.groupby('ticker')[price_col].shift(1))
    return df
```

### Volatility Features
```python
def compute_volatility(df, price_col='close', windows=[5, 21, 63, 126]):
    log_ret = np.log(df[price_col] / df.groupby('ticker')[price_col].shift(1))
    for w in windows:
        df[f'vol_{w}d'] = log_ret.groupby('ticker').rolling(w).std().values * np.sqrt(252)
    return df
```

### Technical Indicators
```python
def compute_technicals(df, price_col='close', volume_col='volume'):
    # SMA crossovers
    df['sma_20'] = df.groupby('ticker')[price_col].transform(lambda x: x.rolling(20).mean())
    df['sma_50'] = df.groupby('ticker')[price_col].transform(lambda x: x.rolling(50).mean())
    df['sma_200'] = df.groupby('ticker')[price_col].transform(lambda x: x.rolling(200).mean())

    # RSI
    delta = df.groupby('ticker')[price_col].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.groupby('ticker').rolling(14).mean().values
    avg_loss = loss.groupby('ticker').rolling(14).mean().values
    rs = avg_gain / avg_loss
    df['rsi_14'] = 100 - (100 / (1 + rs))

    # Volume ratio
    df['vol_ratio'] = df[volume_col] / df.groupby('ticker')[volume_col].transform(lambda x: x.rolling(20).mean())

    return df
```

## Data Storage

### Directory Structure
```
data/
├── cache/              # API response cache (pickle/parquet)
├── raw/
│   ├── prices/         # Raw price data from APIs
│   ├── financials/     # Raw financial statements
│   └── macro/          # FRED/other macro series
├── processed/
│   ├── universe/       # Combined, cleaned price data
│   ├── features/       # Engineered features
│   └── signals/        # Alpha signals / factor scores
└── metadata/
    ├── universes/      # Ticker lists with metadata
    └── schemas/        # Column descriptions and data dictionaries
```

### Naming Convention
- `prices_<source>_<start>_<end>.parquet`
- `features_v<version>_<date>.parquet`
- `universe_<name>_<date>.csv`

## Best Practices

1. **Never hardcode API keys** — use environment variables
2. **Cache aggressively** — respect API limits, reduce costs, speed up re-runs
3. **Log everything** — timestamps, row counts, API status codes
4. **Version your features** — tag datasets with version + date
5. **Validate after every pipeline run** — automated quality checks
6. **Document your schema** — column descriptions, units, frequency

## Review Checklist

- [ ] Data sources documented (API, access method, limitations)
- [ ] Cache implemented to avoid repeated API calls
- [ ] Rate limiting respected for all APIs
- [ ] Cleaning pipeline handles missing data, outliers, splits
- [ ] Cross-frequency alignment correct (no look-ahead)
- [ ] Features properly lagged for backtesting
- [ ] Data quality report generated (coverage, missingness, outliers)
- [ ] Schema documented
