---
name: trading-execution
description: Order types, execution algorithms (VWAP, TWAP, iceberg), market microstructure, transaction cost analysis, and execution quality assessment
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Trading Execution

Workflow for designing execution strategies, selecting order types, and evaluating execution quality.

## When to Use

- Designing execution algorithms for portfolio implementation
- Selecting appropriate order types for different trading objectives
- Analysing transaction costs (commissions, spread, market impact)
- Evaluating execution quality with TCA (Transaction Cost Analysis)
- Understanding market microstructure effects

## Order Types

### Basic Order Types
| Type | Description | Use Case |
|------|-------------|----------|
| Market Order | Execute immediately at best available price | Urgent execution, high liquidity |
| Limit Order | Execute at specified price or better | Price-sensitive, patient |
| Stop Order | Becomes market order when stop price hit | Risk management, breakout entry |
| Stop-Limit | Becomes limit when stop price hit | Risk management with price control |

### Advanced Order Types
| Type | Description | Use Case |
|------|-------------|----------|
| Iceberg | Display only portion of total size | Hiding large orders |
| Pegged | Price pegged to reference (mid, best bid/offer) | Passive execution |
| Market-on-Close | Execute at closing auction price | Benchmark to close |
| VWAP | Volume-Weighted Average Price over period | Minimise market impact |
| TWAP | Time-Weighted Average Price | Even participation |
| Implementation Shortfall | Optimise between impact and timing risk | Large orders |
| Algo Wheels | Rotate through multiple algos | Complex execution goals |

## Execution Algorithms

### VWAP (Volume-Weighted Average Price)

Split parent order into child orders proportional to historical volume profile:

```python
def vwap_schedule(parent_qty, volume_profile, periods):
    """
    volume_profile: array of shape (periods,) with expected % volume per period
    Returns child order quantities per period
    """
    child_orders = parent_qty * volume_profile / volume_profile.sum()
    return child_orders
```

**Strategy**: participate at historical volume % each interval
**Goal**: execute at or better than market VWAP

### TWAP (Time-Weighted Average Price)

Split parent order equally across time intervals:

```python
def twap_schedule(parent_qty, n_intervals):
    return np.full(n_intervals, parent_qty / n_intervals)
```

**Strategy**: even participation over time
**Goal**: minimise timing risk

### Implementation Shortfall / Arrival Price

Balance market impact (trade slower) vs timing risk (trade faster):

$$\min_{\nu_t} \; \mathbb{E}\left[\text{cost} + \lambda \cdot \text{risk}\right]$$

Where:
- Cost = temporary impact + permanent impact + spread
- Risk = variance of execution shortfall relative to arrival price

```python
def optimal_execution(Q, sigma, eta, gamma, T, N):
    """
    Q = total shares to execute
    sigma = volatility (annualised)
    eta = temporary impact parameter
    gamma = permanent impact parameter
    T = time horizon (fraction of year)
    N = number of intervals
    """
    dt = T / N
    kappa = np.sqrt(eta * sigma**2 / gamma)

    # Almgren-Chriss optimal trajectory
    t = np.linspace(0, T, N + 1)
    remaining = Q * np.sinh(kappa * (T - t)) / np.sinh(kappa * T)
    child_orders = -np.diff(remaining)

    return child_orders, remaining
```

## Transaction Cost Analysis (TCA)

### Cost Components

| Component | Description | Typical Range |
|-----------|-------------|---------------|
| Commissions | Broker fee per share | $0.001 - 0.01/share |
| Exchange fees | Exchange/regulatory fees | $0.0001 - 0.0003/share |
| Bid-ask spread | Half-spread × shares (for market orders) | 1-50 bp |
| Market impact | Price movement caused by order | 5-50 bp (depends on size) |
| Delay/slippage | Price change from decision to execution | 0-50 bp |
| Opportunity cost | Cost of not executing (for unfilled) | Variable |

### Implementation Shortfall

$$\text{IS} = \text{Side} \times (\text{Exec Price} - \text{Arrival Price}) + \text{Fees}$$

Components:
1. **Execution cost** = Arrival Price → Exec Price (market timing + impact)
2. **Opportunity cost** = Exec Price → Post-trade benchmark (for unfilled portion)
3. **Fixed costs** = Commissions + fees

### VWAP Slippage

$$\text{Slippage} = \text{Side} \times (\text{Avg Exec Price} - \text{Market VWAP})$$

### Benchmark Selection
| Benchmark | When to Use |
|-----------|------------|
| Arrival price | Urgent orders, momentum strategies |
| VWAP | Passive, participation strategies |
| Close | Index-tracking, ETF creation/redemption |
| Implementation shortfall | Optimal trade-off |

## Market Microstructure

### Key Concepts
- **Order book**: bids and offers at each price level
- **Spread**: Best Ask - Best Bid (cost of immediate execution)
- **Depth**: total shares available at best bid/offer
- **Resilience**: how quickly book refills after a trade
- **Adverse selection**: informed traders cause permanent price impact

### Liquidity Metrics

```python
def liquidity_metrics(order_book, tick_size=0.01):
    best_bid = order_book['bid_price'].max()
    best_ask = order_book['ask_price'].min()
    mid = (best_bid + best_ask) / 2

    # Quoted spread
    quoted_spread = best_ask - best_bid
    quoted_spread_bp = quoted_spread / mid * 10000

    # Effective spread (2 × |trade - mid|)
    # From actual trades, not just quotes

    # Depth at best
    bid_depth = order_book[order_book['bid_price'] == best_bid]['bid_size'].sum()
    ask_depth = order_book[order_book['ask_price'] == best_ask]['ask_size'].sum()

    # Depth for N tick move
    # Sum shares available within N ticks of mid

    return {
        'mid': mid,
        'quoted_spread': quoted_spread,
        'quoted_spread_bp': quoted_spread_bp,
        'bid_depth': bid_depth,
        'ask_depth': ask_depth,
    }
```

### Market Impact Models

**Square-root model** (empirically supported):
$$\text{Impact} = \alpha \cdot \sigma \cdot \sqrt{\frac{Q}{\text{ADV}}}$$

where:
- $\sigma$ = daily volatility
- $Q$ = order size
- ADV = average daily volume
- $\alpha$ ≈ 0.1-0.3 (calibrated per market)

**Almgren-Chriss framework**:
- **Permanent impact**: $\gamma \cdot v_t$ (information leakage)
- **Temporary impact**: $\eta \cdot \text{sign}(v_t) \cdot |v_t|^\beta$

## Execution Quality Reporting

### Post-Trade TCA Report

Required sections:
1. **Order summary**: ticker, side, quantity, start/end time
2. **Benchmark comparison**: vs arrival price, VWAP, close
3. **Cost breakdown**: commissions, spread, impact, delay
4. **Execution trajectory**: cumulative fill vs VWAP schedule
5. **Venue analysis**: where was liquidity found?
6. **Algo performance**: did the algo behave as expected?

### Key Metrics
| Metric | Formula |
|--------|---------|
| Arrival cost | Side × (avg_exec - arrival) / arrival |
| VWAP slippage | Side × (avg_exec - VWAP) / VWAP |
| Fill rate | Executed / Parent order |
| Participation rate | Executed / Market volume |
| Spread capture | % of half-spread captured by limit orders |

## Review Checklist

- [ ] Order type selected based on urgency and price sensitivity
- [ ] Execution algorithm parameters justified (horizon, participation rate, urgency)
- [ ] Expected market impact estimated (using square-root or Almgren-Chriss)
- [ ] Total transaction cost estimate provided
- [ ] Liquidity assessment: ADV, spread, depth
- [ ] Risk of adverse selection considered (pre-earnings, pre-FOMC, etc.)
- [ ] Post-trade TCA template prepared for measuring execution quality
