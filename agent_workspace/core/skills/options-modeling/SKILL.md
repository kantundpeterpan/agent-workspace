---
name: options-modeling
description: Black-Scholes/Merton, binomial trees, Monte Carlo pricing, Greeks computation, implied volatility, volatility surfaces, and option strategy analysis
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Options Modeling

Systematic workflow for pricing options, computing Greeks, building volatility surfaces, and analysing option strategies.

## When to Use

- Pricing European and American options
- Computing and interpreting option Greeks
- Fitting and analysing volatility surfaces
- Designing and evaluating multi-leg option strategies
- Hedging options portfolios

## Pricing Models

### Black-Scholes-Merton (European Options)

**Core formulas**:
$$C = S_0 \Phi(d_1) - K e^{-rT} \Phi(d_2)$$
$$P = K e^{-rT} \Phi(-d_2) - S_0 \Phi(-d_1)$$

where:
$$d_1 = \frac{\ln(S_0/K) + (r - q + \sigma^2/2)T}{\sigma \sqrt{T}}$$
$$d_2 = d_1 - \sigma \sqrt{T}$$

With dividends ($q$ = continuous dividend yield).

```python
import numpy as np
from scipy.stats import norm

def black_scholes(S, K, T, r, sigma, q=0.0, option_type='call'):
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'call':
        price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:  # put
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)

    return price
```

### Binomial Tree (American Options)

```python
def binomial_tree(S, K, T, r, sigma, N, q=0.0, option_type='call', american=True):
    dt = T / N
    u = np.exp(sigma * np.sqrt(dt))
    d = 1 / u
    p = (np.exp((r - q) * dt) - d) / (u - d)
    disc = np.exp(-r * dt)

    S_tree = np.zeros((N + 1, N + 1))
    for i in range(N + 1):
        for j in range(i + 1):
            S_tree[j, i] = S * (u ** (i - j)) * (d ** j)

    if option_type == 'call':
        V = np.maximum(S_tree[:, N] - K, 0)
    else:
        V = np.maximum(K - S_tree[:, N], 0)

    for i in range(N - 1, -1, -1):
        V = disc * (p * V[:-1] + (1 - p) * V[1:])
        if american:
            if option_type == 'call':
                V = np.maximum(V, S_tree[:i + 1, i] - K)
            else:
                V = np.maximum(V, K - S_tree[:i + 1, i])

    return V[0]
```

### Monte Carlo Simulation

```python
def monte_carlo_option(S, K, T, r, sigma, N=100000, q=0.0, option_type='call'):
    np.random.seed(42)
    z = np.random.standard_normal(N)
    ST = S * np.exp((r - q - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * z)

    if option_type == 'call':
        payoffs = np.maximum(ST - K, 0)
    else:
        payoffs = np.maximum(K - ST, 0)

    price = np.exp(-r * T) * payoffs.mean()
    se = payoffs.std() / np.sqrt(N)

    return price, se, price - 1.96*se, price + 1.96*se
```

## Greeks

### Analytical (Black-Scholes)

| Greek | Call Formula | Put Formula | Interpretation |
|-------|-------------|-------------|----------------|
| Delta | $e^{-qT} \Phi(d_1)$ | $-e^{-qT} \Phi(-d_1)$ | $/unit change in underlying |
| Gamma | $\frac{e^{-qT} \phi(d_1)}{S\sigma\sqrt{T}}$ | Same | Delta change per $1 underlying move |
| Theta | $-\frac{Se^{-qT}\phi(d_1)\sigma}{2\sqrt{T}} + qSe^{-qT}\Phi(d_1) - rKe^{-rT}\Phi(d_2)$ | $-\frac{Se^{-qT}\phi(d_1)\sigma}{2\sqrt{T}} - qSe^{-qT}\Phi(-d_1) + rKe^{-rT}\Phi(-d_2)$ | Time decay (per year; ÷365 for daily) |
| Vega | $Se^{-qT} \phi(d_1)\sqrt{T}$ | Same | $/1% IV change (÷100 for 1% change) |
| Rho | $KTe^{-rT}\Phi(d_2)$ | $-KTe^{-rT}\Phi(-d_2)$ | $/1% rate change (÷100 for 1%) |

```python
def compute_greeks(S, K, T, r, sigma, q=0.0, option_type='call'):
    d1 = (np.log(S/K) + (r - q + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)

    if option_type == 'call':
        delta = np.exp(-q*T) * norm.cdf(d1)
        theta = (-S*np.exp(-q*T)*norm.pdf(d1)*sigma/(2*np.sqrt(T))
                 + q*S*np.exp(-q*T)*norm.cdf(d1)
                 - r*K*np.exp(-r*T)*norm.cdf(d2))
        rho = K*T*np.exp(-r*T)*norm.cdf(d2)
    else:  # put
        delta = -np.exp(-q*T) * norm.cdf(-d1)
        theta = (-S*np.exp(-q*T)*norm.pdf(d1)*sigma/(2*np.sqrt(T))
                 - q*S*np.exp(-q*T)*norm.cdf(-d1)
                 + r*K*np.exp(-r*T)*norm.cdf(-d2))
        rho = -K*T*np.exp(-r*T)*norm.cdf(-d2)

    gamma = np.exp(-q*T)*norm.pdf(d1) / (S*sigma*np.sqrt(T))
    vega = S*np.exp(-q*T)*norm.pdf(d1)*np.sqrt(T) / 100  # per 1% IV change

    return {'delta': delta, 'gamma': gamma, 'theta': theta/365, 'vega': vega, 'rho': rho/100}
```

## Implied Volatility

Calculate the IV that makes the model price equal the market price:

```python
def implied_volatility(market_price, S, K, T, r, q=0.0, option_type='call', tol=1e-8, max_iter=100):
    sigma = 0.3  # Initial guess
    for i in range(max_iter):
        price = black_scholes(S, K, T, r, sigma, q, option_type)
        vega = S * np.exp(-q*T) * np.sqrt(T) * norm.pdf(
            (np.log(S/K) + (r - q + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        )
        if abs(vega) < 1e-10:
            return None
        diff = price - market_price
        if abs(diff) < tol:
            return sigma
        sigma = sigma - diff / vega
    return sigma
```

## Volatility Surface

A volatility surface shows IV across strikes (moneyness) and maturities.

### Key Features
- **Smile/Skew**: IV varies with strike; OTM puts usually higher IV
- **Term structure**: IV varies with time to expiry
- **Sticky strike**: surface fixed in strike space; IV for a given strike stays constant
- **Sticky delta**: surface fixed in delta space; IV follows the moneyness

### Construction
1. Collect option chains for all available strikes and expiries
2. Compute implied volatility for each option
3. Interpolate/smooth across strikes and maturities
4. Plot as 3D surface or heatmap

## Relationship Between Greeks

### Put-Call Parity
$$C - P = Se^{-qT} - Ke^{-rT}$$

Implies: $\Delta_C - \Delta_P = e^{-qT}$ and $\Gamma_C = \Gamma_P$

### Gamma-Theta Tradeoff
For a delta-hedged portfolio: higher gamma means more frequent rebalancing profit, but higher theta (time decay) cost.

## Strategy Payoff Diagrams

Always construct a payoff diagram (profit/loss vs underlying price at expiry) showing:
- X-axis: underlying price range ($\pm$ 3σ or ±20%)
- Y-axis: profit/loss ($)
- Components: each leg's payoff as dashed line
- Combined payoff as solid line
- Breakeven points marked
- Max profit / max loss annotated

## Review Checklist

- [ ] Correct model selected (European → BSM; American → binomial)
- [ ] Dividend yield included if applicable
- [ ] All Greeks computed and interpreted
- [ ] Implied volatility vs historical volatility compared
- [ ] Volatility smile/skew documented
- [ ] Payoff diagram for each strategy
- [ ] Early exercise risk noted for American options
- [ ] Interest rate and dividend assumptions stated
