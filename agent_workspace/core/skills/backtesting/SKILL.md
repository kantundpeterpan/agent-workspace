---
name: backtesting
description: Strategy backtest design, walk-forward analysis, performance metrics computation, overfitting detection, and backtest validation
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Backtesting

Systematic workflow for designing, running, and evaluating trading strategy backtests with rigorous bias prevention.

## When to Use

- Testing a quantitative trading strategy on historical data
- Evaluating strategy performance metrics
- Detecting and preventing overfitting and data-snooping biases
- Comparing multiple strategy variants
- Preparing a strategy for paper trading or live deployment

## Backtest Design Principles

### Golden Rules
1. **Point-in-time data**: never use information available only after the trade date
2. **Survivorship-free universe**: include stocks that were delisted
3. **Realistic transaction costs**: commissions + slippage + market impact
4. **Sufficient out-of-sample period**: minimum 30% of total data
5. **Benchmark awareness**: compare against appropriate passive benchmark

### Common Biases to Avoid
| Bias | Description | Prevention |
|------|-------------|------------|
| Look-ahead | Using future data to make current decisions | Lag all signals; verify data timestamps |
| Survivorship | Only testing on stocks that still exist | Backfill delisted stocks; use point-in-time universes |
| Data snooping | Overfitting to historical patterns | Walk-forward validation; deflated Sharpe |
| In-sample overfit | Model fits noise, not signal | Minimum 30% OOS; limit free parameters |

## Walk-Forward Analysis

### Procedure
1. Split data into in-sample (IS) and out-of-sample (OOS) periods
2. Use rolling or expanding windows:
   - **Rolling**: fixed-length window (e.g., 5 years IS, 1 year OOS)
   - **Expanding**: growing window from start to current date
3. For each window:
   a. Train/optimise strategy on IS window
   b. Test/run strategy on subsequent OOS window
   c. Record OOS performance
4. Aggregate all OOS periods for final evaluation

```python
def walk_forward_analysis(prices, signals, train_years=5, test_years=1):
    results = []
    dates = prices.index
    step = 252 * test_years  # trading days per OOS period
    train_len = 252 * train_years

    for i in range(train_len, len(dates), step):
        train_dates = dates[i - train_len : i]
        test_dates = dates[i : min(i + step, len(dates))]

        # Train on IS, run on OOS
        strategy_params = optimize_strategy(prices.loc[train_dates], signals.loc[train_dates])
        oos_perf = run_strategy(prices.loc[test_dates], signals.loc[test_dates], strategy_params)

        results.append(oos_perf)

    return aggregate_results(results)
```

## Performance Metrics

### Return Metrics
```python
def compute_metrics(returns, benchmark_returns=None, rf_rate=0.0):
    metrics = {}

    # Total and annualised returns
    metrics['total_return'] = (1 + returns).prod() - 1
    metrics['ann_return'] = (1 + metrics['total_return']) ** (252 / len(returns)) - 1

    # Risk
    metrics['ann_volatility'] = returns.std() * np.sqrt(252)
    metrics['downside_deviation'] = returns[returns < 0].std() * np.sqrt(252)

    # Risk-adjusted returns
    excess = returns - rf_rate / 252
    metrics['sharpe_ratio'] = excess.mean() / returns.std() * np.sqrt(252)
    metrics['sortino_ratio'] = excess.mean() / returns[returns < 0].std() * np.sqrt(252)

    # Drawdowns
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = cumulative / running_max - 1
    metrics['max_drawdown'] = drawdown.min()
    metrics['calmar_ratio'] = metrics['ann_return'] / abs(metrics['max_drawdown'])

    # Win/Loss
    metrics['win_rate'] = (returns > 0).mean()
    metrics['avg_win'] = returns[returns > 0].mean()
    metrics['avg_loss'] = returns[returns < 0].mean()
    metrics['profit_factor'] = abs(returns[returns > 0].sum() / returns[returns < 0].sum())
    metrics['expectancy'] = metrics['win_rate'] * metrics['avg_win'] + (1 - metrics['win_rate']) * metrics['avg_loss']

    # Relative
    if benchmark_returns is not None:
        active = returns - benchmark_returns
        metrics['tracking_error'] = active.std() * np.sqrt(252)
        metrics['information_ratio'] = active.mean() / active.std() * np.sqrt(252)
        metrics['beta'] = np.cov(returns, benchmark_returns)[0,1] / benchmark_returns.var()
        metrics['alpha'] = metrics['ann_return'] - rf_rate - metrics['beta'] * (benchmark_returns.mean()*252 - rf_rate)

    return metrics
```

### Key Metrics Table
| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Sharpe ratio | > 1.0 | 0.5 - 1.0 | < 0.5 |
| Sortino ratio | > 1.5 | 1.0 - 1.5 | < 1.0 |
| Max drawdown | < 20% | 20% - 40% | > 40% |
| Calmar ratio | > 1.0 | 0.5 - 1.0 | < 0.5 |
| Win rate | > 55% | 45% - 55% | < 45% |
| Profit factor | > 1.5 | 1.2 - 1.5 | < 1.2 |
| Information ratio | > 0.5 | 0.3 - 0.5 | < 0.3 |

## Overfitting Detection

### Deflated Sharpe Ratio (DSR)
Accounts for multiple testing: the probability that the observed Sharpe ratio is from skill rather than luck given the number of strategies tested.

$$DSR = \Phi\left(\frac{(SR - \mathbb{E}[\max SR]) \sqrt{T-1}}{\sqrt{1 - \gamma_3 \cdot SR + \frac{\gamma_4 - 1}{4} \cdot SR^2}}\right)$$

Where the expected maximum SR from $N$ random strategies is:
$$\mathbb{E}[\max SR] \approx \sqrt{2 \ln(N)} \cdot \left(1 - \frac{\ln(\ln(N)) + \ln(4\pi)}{4\ln(N)}\right)$$

DSR < 0.05: reject null; strategy likely adds value.

### Other Overfitting Tests
- **Probabilistic Sharpe Ratio (PSR)**: probability SR exceeds a threshold
- **Performance Degradation**: OOS SR / IS SR ratio (should be > 0.5)
- **Parameter stability**: vary parameters ±20%, observe SR changes

## Backtest Report Template

### Required Sections
1. **Strategy Description**: universe, signals, entry/exit rules, rebalancing frequency
2. **Data Summary**: source, sample period, ticker count, adjustments
3. **Walk-Forward Results**: IS vs OOS performance comparison
4. **Performance Table**: all metrics vs benchmark
5. **Equity Curve**: cumulative returns (strategy vs benchmark)
6. **Drawdown Plot**: underwater chart with max drawdown annotation
7. **Monthly Returns Heatmap**: calendar-year matrix
8. **Return Distribution**: histogram with normal overlay + skew/kurtosis
9. **Rolling Metrics**: 12-month rolling Sharpe, volatility, beta
10. **Overfitting Tests**: deflated Sharpe, performance degradation ratio

## Review Checklist

- [ ] Point-in-time data used; no look-ahead bias
- [ ] Survivorship-free universe confirmed
- [ ] Transaction costs modelled realistically
- [ ] Walk-forward with ≥30% out-of-sample data
- [ ] All performance metrics computed and explained
- [ ] Benchmark comparison included
- [ ] Overfitting tests done (deflated SR, OOS/IS ratio)
- [ ] Strategy logic clearly documented
- [ ] Sensitivity analysis on key parameters
- [ ] Risk warnings: worst-case OOS period, max consecutive losses
