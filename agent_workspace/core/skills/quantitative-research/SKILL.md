---
name: quantitative-research
description: Factor model construction, alpha signal development, statistical arbitrage, systematic strategy design and evaluation
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Quantitative Research

Systematic workflow for developing quantitative trading signals, constructing factor models, and evaluating alpha strategies.

## When to Use

- Building multi-factor models for stock selection
- Developing alpha signals from market data
- Testing statistical arbitrage strategies
- Analysing factor performance and decay
- Researching new quantitative investment ideas

## Alpha Signal Development Lifecycle

### 1. Hypothesis Formulation
- State the economic rationale for why the signal should work
- Identify the behavioural or structural inefficiency it exploits
- Define the expected relationship and direction
- Specify under what conditions the signal should work (and fail)

### 2. Data Sourcing
- Determine required data: prices, fundamentals, estimates, alternative data
- Ensure point-in-time availability to avoid look-ahead bias
- Verify data quality: missingness, outliers, survivorship, adjustments

### 3. Signal Construction

**Common transformations**:
```python
import numpy as np
import pandas as pd
from scipy import stats

# Z-score normalisation
signal_z = (raw_signal - raw_signal.mean()) / raw_signal.std()

# Rank normalisation (cross-sectional)
signal_rank = raw_signal.rank(pct=True)

# Sector neutralisation
def sector_neutralise(signal, sector_map):
    sector_mean = signal.groupby(sector_map).transform('mean')
    return signal - sector_mean

# Winsorisation
def winsorise(series, limits=(0.01, 0.99)):
    lower = series.quantile(limits[0])
    upper = series.quantile(limits[1])
    return series.clip(lower, upper)
```

### 4. Factor Evaluation

**Information Coefficient (IC)**:
- $IC_t = \text{corr}(\text{signal}_t, \text{forward\_return}_{t+1})$
- Rank IC: Spearman correlation (more robust to outliers)
- Mean IC, IC standard deviation, IC t-stat, IC hit rate

```python
def compute_ic(signal, forward_returns):
    ic = signal.corrwith(forward_returns, axis=1)
    ir = ic.mean() / ic.std()  # Information ratio of IC
    return ic, ir
```

**Factor Returns (Fama-MacBeth)**:
1. Cross-sectional regression each period: $R_i = \alpha + \beta \cdot \text{signal}_i + \varepsilon_i$
2. Time-series of $\hat{\beta}$ coefficients
3. t-stat = mean(β) / (std(β) / √T)

**Quintile/Decile Analysis**:
- Sort stocks into 5 (quintile) or 10 (decile) bins by signal
- Compute mean forward return for each bin
- Long-short spread: top bin return - bottom bin return
- Report long-only, short-only, and long-short performance

### 5. Factor Timing & Decay
- Rolling IC: how stable is the signal over time?
- Half-life of IC decay: when does predictive power drop by 50%?
- Does signal work better in certain market regimes (up/down, high/low vol)?

## Multi-Factor Models

### Factor Categories
| Factor | Typical Definition | Economic Rationale |
|--------|-------------------|-------------------|
| Value | Book/Price, Earnings/Price, CF/Price | Cheap assets outperform expensive |
| Momentum | 12-1 month return | Trend persistence; delayed information diffusion |
| Quality | ROE, accruals, leverage, earnings stability | High-quality companies compound better |
| Low Volatility | Low beta, low idiosyncratic vol | Leverage-constrained investors bid up high-beta |
| Size | Market capitalisation | Small-cap premium (debated in recent decades) |
| Growth | Earnings/sales growth, capex growth | Growth companies compound; may be overpriced |
| Liquidity | Amihud illiquidity, turnover | Illiquidity premium |
| Sentiment | Short interest, analyst dispersion | Contrarian signals |

### Factor Combination
1. **Equal-weighted**: $\text{score}_i = \frac{1}{K} \sum_{k=1}^K \text{rank}(s_{i,k})$
2. **IC-weighted**: $\text{score}_i = \sum_{k=1}^K |\overline{IC_k}| \cdot \text{rank}(s_{i,k})$
3. **Optimisation-based**: max IC subject to correlation constraints

### Factor Correlation Matrix
Always check factor redundancy:
```python
factor_corr = factor_returns.corr()
# Flag pairs with |correlation| > 0.7
```

## Statistical Arbitrage

### Pairs Trading
1. Identify cointegrated pairs: run Engle-Granger or Johansen test
2. Estimate hedge ratio: $P_{A,t} = \alpha + \beta P_{B,t} + \varepsilon_t$
3. Compute spread: $s_t = P_{A,t} - \hat{\alpha} - \hat{\beta} P_{B,t}$
4. Z-score the spread: $z_t = (s_t - \bar{s}) / \sigma_s$
5. Entry: $|z_t| > 2$, Exit: $z_t \to 0$ or stop at $|z_t| > 3$

### PCA-Based Strategies
1. Run PCA on returns matrix (assets × time)
2. First few PCs capture systematic factors
3. Residuals (idiosyncratic returns) = actual - PCA-reconstructed
4. Trade residuals for mean-reversion signals

## Evaluation Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Mean IC | mean(IC_t) | > 0.03 |
| ICIR | mean(IC) / std(IC) | > 0.5 |
| Quintile spread (ann.) | (Q5 ret - Q1 ret) annualised | > 5% |
| Hit rate | frac(IC_t > 0) | > 55% |
| Factor turnover | mean(|rank_t - rank_{t-1}|) | < 30% |

## Research Documentation

Each quant research output must include:
- Alpha hypothesis statement with economic rationale
- Data sources and sample period
- Signal construction details (transformations, normalisation)
- IC analysis: mean IC, ICIR, rolling IC, IC decay
- Quintile analysis with cumulative return plot
- Factor correlation matrix
- Robustness checks: subsample, region, sector
- Limitations and known issues
