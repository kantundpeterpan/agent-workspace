---
name: risk-modeling
description: Value-at-Risk (VaR), Conditional VaR, stress testing, scenario analysis, Monte Carlo simulation, and comprehensive risk reporting
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Risk Modeling

Systematic workflow for measuring, analysing, and reporting portfolio risk across multiple methodologies.

## When to Use

- Computing Value-at-Risk (VaR) and Conditional VaR (Expected Shortfall)
- Running stress tests and scenario analysis
- Performing Monte Carlo risk simulations
- Backtesting risk models
- Producing risk reports with actionable insights

## Value-at-Risk (VaR)

### Definition
VaR at confidence level $\alpha$ is the maximum loss not exceeded with probability $\alpha$ over a given horizon:

$$P(L > \text{VaR}_{\alpha}) = 1 - \alpha$$

### Methods

#### 1. Parametric (Variance-Covariance)
Assume normal returns:
$$\text{VaR}_{\alpha} = -(\mu + z_{\alpha} \sigma) \times V$$

where $z_{0.95} \approx -1.645$, $z_{0.99} \approx -2.326$

```python
import numpy as np
from scipy.stats import norm

def parametric_var(returns, confidence=0.95, value=1_000_000):
    mu = returns.mean()
    sigma = returns.std()
    z = norm.ppf(1 - confidence)
    var = -(mu + z * sigma) * value
    return var
```

#### 2. Historical Simulation
Use empirical return distribution directly:

```python
def historical_var(returns, confidence=0.95, value=1_000_000):
    var = -np.percentile(returns, 100 * (1 - confidence)) * value
    return var
```

**Advantages**: no distribution assumption, captures fat tails
**Disadvantages**: assumes past = future, sensitive to window length

#### 3. Monte Carlo Simulation
Simulate N return paths from fitted distribution:

```python
def monte_carlo_var(returns, confidence=0.95, value=1_000_000, n_sim=100_000):
    mu, sigma = returns.mean(), returns.std()

    # Simulate returns
    simulated = np.random.normal(mu, sigma, n_sim)

    # Or with fat tails (t-distribution)
    # df, loc, scale = t.fit(returns)
    # simulated = t.rvs(df, loc, scale, size=n_sim)

    var = -np.percentile(simulated, 100 * (1 - confidence)) * value
    return var
```

## Conditional VaR (Expected Shortfall)

The expected loss given that the loss exceeds VaR:

$$\text{CVaR}_{\alpha} = \mathbb{E}[L \mid L > \text{VaR}_{\alpha}]$$

```python
def cvar(returns, confidence=0.95, value=1_000_000):
    var_threshold = -np.percentile(returns, 100 * (1 - confidence))
    tail_losses = returns[returns <= -var_threshold]
    cvar = -tail_losses.mean() * value
    return cvar
```

CVaR is always ≥ VaR and satisfies subadditivity (coherent risk measure).

## VaR Backtesting

### Kupiec Test (Proportion of Failures)
Tests whether the observed exception rate matches the expected rate.

$$LR_{POF} = -2 \ln\left(\frac{(1-p)^{T-N} p^N}{(1-N/T)^{T-N} (N/T)^N}\right) \sim \chi^2(1)$$

where $p = 1 - \alpha$, $T$ = total days, $N$ = exceptions

```python
def kupiec_test(returns, var_series, confidence=0.95):
    p = 1 - confidence
    N = (returns < -var_series).sum()
    T = len(returns)
    p_hat = N / T

    lr = -2 * (np.log((1-p)**(T-N) * p**N) - np.log((1-p_hat)**(T-N) * p_hat**N))

    from scipy.stats import chi2
    p_value = 1 - chi2.cdf(lr, 1)
    return lr, p_value, N, T
```

### Christoffersen Test (Conditional Coverage)
Tests whether exceptions are independent (no clustering).

## Stress Testing & Scenario Analysis

### Historical Stress Scenarios

| Scenario | Date | Key Moves |
|----------|------|-----------|
| Black Monday | Oct 19, 1987 | S&P 500 -20.5% single day |
| Asian Financial Crisis | 1997-1998 | EM equities -60%, Asian currencies collapse |
| Russian Default / LTCM | Aug-Sep 1998 | Credit spreads +100bp, flight to Treasuries |
| Dot-com Bubble Burst | Mar 2000 - Oct 2002 | Nasdaq -78%, S&P -49% |
| Global Financial Crisis | Sep 2008 - Mar 2009 | S&P -57%, HY spreads +1500bp, VIX 80+ |
| European Debt Crisis | 2011 | EUR -10%, periphery spreads +300bp |
| Taper Tantrum | May-Jun 2013 | US 10Y +100bp, EM selloff |
| China Devaluation | Aug 2015 | Shanghai -40%, EM FX selloff |
| Volmageddon | Feb 5, 2018 | VIX +115% single day, XIV termination |
| COVID Crash | Feb-Mar 2020 | S&P -34%, VIX 82, oil negative |
| UK Gilt Crisis | Sep 2022 | UK 30Y +130bp, GBP -5% |

### Hypothetical Stress Scenarios

```python
scenarios = {
    'Equity_Crash': {'S&P': -0.20, 'VIX': 0.80, 'HY_OAS': 0.03, 'Gold': 0.05},
    'Rate_Shock': {'S&P': -0.05, 'US10Y': 0.01, 'USD': 0.05, 'Gold': -0.05},
    'Stagflation': {'S&P': -0.10, 'US10Y': 0.005, 'Oil': 0.30, 'Gold': 0.10},
    'Credit_Crunch': {'S&P': -0.15, 'HY_OAS': 0.05, 'IG_OAS': 0.02, 'USD': 0.03},
    'Dollar_Collapse': {'S&P': -0.05, 'USD': -0.15, 'Gold': 0.15, 'Oil': 0.20},
}

def run_stress_test(portfolio_weights, asset_betas, scenario):
    scenario_returns = {}
    for asset, exposures in asset_betas.items():
        ret = 0
        for factor, beta in exposures.items():
            if factor in scenario:
                ret += beta * scenario[factor]
        scenario_returns[asset] = ret

    portfolio_loss = sum(portfolio_weights[a] * scenario_returns[a]
                         for a in portfolio_weights)
    return portfolio_loss, scenario_returns
```

### Reverse Stress Testing
Identify the scenario conditions that would cause a specified loss:
1. Define unacceptable loss threshold (e.g., -20% of NAV)
2. Work backwards: what combination of market moves causes this?
3. Assess plausibility of those market moves
4. Highlight as ultimate risk scenario

## Monte Carlo Risk Simulation

### Multi-Asset Simulation with Correlation

```python
def simulate_correlated_returns(mu, Sigma, n_periods=252, n_sim=10000):
    """Simulate n_sim paths of n_periods for correlated assets."""
    L = np.linalg.cholesky(Sigma)
    n_assets = len(mu)

    # Generate independent normal draws
    z = np.random.randn(n_sim, n_periods, n_assets)

    # Apply correlation structure
    correlated = z @ L.T + mu

    return correlated
```

### Key Outputs
1. Distribution of terminal portfolio values (histogram)
2. VaR and CVaR at multiple confidence levels
3. Probability of losing more than X%
4. Probability of positive return
5. Worst-case (1st percentile) and best-case (99th percentile) paths

## Risk Reporting

### Risk Dashboard Components

1. **VaR Summary**: parametric, historical, and Monte Carlo at 95% and 99%
2. **VaR Backtest**: exception chart, Kupiec/Christoffersen test results
3. **Drawdown Analysis**: max drawdown, current drawdown, drawdown duration
4. **Stress Test Results**: P&L under each scenario (bar chart)
5. **Risk Decomposition**: what factors/assets drive portfolio risk
6. **Concentration**: top-5 positions, sector, factor
7. **Liquidity Risk**: days to liquidate, bid-ask impact
8. **Leverage**: gross/net exposure, VaR as % of NAV

### Risk Limits Dashboard
| Limit | Value | Current | Utilisation | Status |
|-------|-------|---------|-------------|--------|
| VaR 99% / NAV | 5% | 3.2% | 64% | 🟢 |
| Max Drawdown | 20% | 8.5% | 43% | 🟢 |
| Net Exposure | 0-100% | 85% | 85% | 🟢 |
| Gross Exposure | <200% | 140% | 70% | 🟢 |
| Single Name | 10% | 7.2% | 72% | 🟢 |
| Sector | 30% | 22% | 73% | 🟢 |

## Review Checklist

- [ ] VaR computed by all 3 methods at 95% and 99%
- [ ] CVaR reported alongside VaR
- [ ] VaR backtested (Kupiec + Christoffersen tests)
- [ ] Historical stress scenarios applied to current portfolio
- [ ] Hypothetical scenarios defined and tested
- [ ] Monte Carlo simulation with sufficient paths (≥10,000)
- [ ] Risk decomposition: identified top risk contributors
- [ ] Concentration and liquidity risks assessed
- [ ] Risk limits defined and current utilisation reported
- [ ] Reverse stress test identifies existential risk scenarios
