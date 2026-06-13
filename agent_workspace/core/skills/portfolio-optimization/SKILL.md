---
name: portfolio-optimization
description: Markowitz mean-variance optimisation, Black-Litterman, risk parity, factor-based allocation, rebalancing strategies, and efficient frontier construction
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Portfolio Optimization

Systematic workflow for portfolio construction, optimisation under constraints, and allocation analysis.

## When to Use

- Constructing an optimal portfolio from a universe of assets
- Incorporating investor views into a benchmark-relative allocation
- Building risk-parity or equal-risk-contribution portfolios
- Analysing efficient frontiers and capital allocation lines
- Designing rebalancing strategies

## Mean-Variance Optimization (Markowitz)

### Standard Formulation

$$\min_w \; \frac{1}{2} w^T \Sigma w - \lambda \mu^T w$$
$$\text{s.t.} \quad \sum_i w_i = 1, \quad w_i \geq 0, \quad w_i \leq w_{\max}, \ldots$$

where:
- $w$ = vector of portfolio weights
- $\mu$ = vector of expected returns
- $\Sigma$ = covariance matrix of returns
- $\lambda$ = risk aversion parameter ($\lambda = 0$ → max return; $\lambda = \infty$ → min variance)

### Implementation
```python
import numpy as np
from scipy.optimize import minimize

def markowitz(returns, lambda_val=1.0, bounds=(0, 1)):
    n = returns.shape[1]
    mu = returns.mean() * 252
    Sigma = returns.cov() * 252

    def objective(w):
        return 0.5 * w @ Sigma @ w - lambda_val * mu @ w

    constraints = [{'type': 'eq', 'fun': lambda w: w.sum() - 1}]
    w0 = np.ones(n) / n  # equal weight start

    result = minimize(objective, w0,
                      bounds=[bounds]*n,
                      constraints=constraints,
                      method='SLSQP')

    return result.x, result.fun
```

### Efficient Frontier

```python
def efficient_frontier(returns, n_points=50):
    mus, sigmas = [], []
    mu_all = returns.mean() * 252
    Sigma_all = returns.cov() * 252
    n = returns.shape[1]

    lambda_range = np.logspace(-2, 4, n_points)

    for lam in lambda_range:
        w, _ = markowitz(returns, lam)
        w = np.clip(w, 0, 1)
        w = w / w.sum()  # ensure sum to 1
        port_mu = w @ mu_all
        port_sigma = np.sqrt(w @ Sigma_all @ w)
        mus.append(port_mu)
        sigmas.append(port_sigma)

    return np.array(sigmas), np.array(mus)
```

### Shrinkage Estimation (Ledoit-Wolf)

Sample covariance is noisy; shrinkage improves out-of-sample performance:

```python
from sklearn.covariance import LedoitWolf

lw = LedoitWolf()
shrunk_cov = lw.fit(returns).covariance_
```

## Black-Litterman Model

### Core Idea
Combine market equilibrium returns (prior) with investor views to produce a refined return estimate.

### Procedure

1. **Calculate equilibrium (implied) returns**:
   $$\pi = \lambda \Sigma w_{mkt}$$

2. **Specify investor views**:
   - $P$ = pick matrix ($k \times n$, where $k$ = number of views)
   - $Q$ = view vector ($k \times 1$)
   - $\Omega$ = view confidence matrix ($k \times k$, diagonal)

3. **Compute posterior expected returns**:
   $$\mu_{BL} = [(\tau\Sigma)^{-1} + P^T \Omega^{-1} P]^{-1} [(\tau\Sigma)^{-1} \pi + P^T \Omega^{-1} Q]$$

4. **Compute posterior covariance**:
   $$\Sigma_{BL} = \Sigma + [(\tau\Sigma)^{-1} + P^T\Omega^{-1}P]^{-1}$$

5. **Optimise** using $\mu_{BL}$ and $\Sigma_{BL}$

```python
def black_litterman(pi, Sigma, P, Q, Omega, tau=0.025):
    tau_Sigma_inv = np.linalg.inv(tau * Sigma)
    Omega_inv = np.linalg.inv(Omega)

    M = np.linalg.inv(tau_Sigma_inv + P.T @ Omega_inv @ P)
    mu_bl = M @ (tau_Sigma_inv @ pi + P.T @ Omega_inv @ Q)
    Sigma_bl = Sigma + M

    return mu_bl, Sigma_bl
```

## Risk Parity (Equal Risk Contribution)

### Objective
Each asset contributes equally to portfolio risk:
$$\sigma_{p,i} = w_i \cdot \frac{\partial \sigma_p}{\partial w_i} = \frac{w_i (\Sigma w)_i}{\sqrt{w^T \Sigma w}}$$

$$\min_w \sum_{i,j} \left(w_i (\Sigma w)_i - w_j (\Sigma w)_j\right)^2$$

```python
def risk_parity(Sigma):
    n = Sigma.shape[0]

    def risk_contributions(w):
        port_vol = np.sqrt(w @ Sigma @ w)
        mrc = Sigma @ w / port_vol  # marginal risk contributions
        rc = w * mrc
        return rc, port_vol

    def objective(w):
        rc, _ = risk_contributions(w)
        target_rc = 1.0 / n
        return np.sum((rc / rc.sum() - target_rc) ** 2)

    constraints = [{'type': 'eq', 'fun': lambda w: w.sum() - 1}]
    w0 = np.ones(n) / n
    result = minimize(objective, w0,
                      bounds=[(0, 1)]*n,
                      constraints=constraints,
                      method='SLSQP')
    return result.x
```

## Portfolio Analytics

### Risk Decomposition
| Component | Formula | Interpretation |
|-----------|---------|----------------|
| Total risk | $\sigma_p = \sqrt{w^T \Sigma w}$ | Portfolio volatility |
| Marginal risk contribution | $\text{MRC}_i = (\Sigma w)_i / \sigma_p$ | Change in risk per unit change in weight |
| Risk contribution | $\text{RC}_i = w_i \times \text{MRC}_i$ | Absolute risk from asset i |
| % Risk contribution | $\text{RC}_i / \sigma_p$ | Fraction of total risk |

### Performance Attribution
- **Brinson**: allocation effect + selection effect + interaction
- **Factor-based**: decompose returns into factor exposures × factor returns

### Turnover
$$\text{Turnover} = \frac{1}{2} \sum_i |w_{i, t} - w_{i, t-1}|$$

### Diversification Metrics
- **Effective N**: $N_{\text{eff}} = 1 / \sum w_i^2$
- **HHI**: $\sum w_i^2$ (0 = evenly distributed, 1 = single asset)
- **Diversification ratio**: $\frac{\sum w_i \sigma_i}{\sigma_p}$ (>1 means diversification benefit)

## Rebalancing Strategies

| Strategy | Rule | Pros | Cons |
|----------|------|------|------|
| Calendar | Rebalance monthly/quarterly | Simple, predictable | May trade unnecessarily |
| Threshold | Rebalance when |weight - target| > X% | Trades only when needed | Tracking error can grow |
| Optimal | Trade off tracking error vs costs | Minimises total cost | Requires cost estimates |
| Constant mix | Maintain fixed % allocation | Disciplined | Can amplify drawdowns |

## Review Checklist

- [ ] Investment objective and benchmark clearly defined
- [ ] Expected returns estimation method justified
- [ ] Covariance estimation method stated (sample, shrinkage, factor model)
- [ ] Constraints documented (long-only, max weight, sector, turnover)
- [ ] Efficient frontier plotted with current and optimal portfolios
- [ ] Risk decomposition: what drives portfolio risk?
- [ ] Concentration analysis: top-N, effective N, HHI
- [ ] Transaction cost / turnover estimate
- [ ] Rebalancing frequency and threshold specified
- [ ] Out-of-sample performance considerations noted
