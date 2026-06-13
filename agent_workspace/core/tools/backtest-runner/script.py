#!/usr/bin/env python3
"""
Backtest Runner Tool
Programmatic backtesting engine with performance metrics.
"""

import json
from typing import Any, Dict, List, Optional

import numpy as np


def _build_df(data: List[Dict]) -> "pd.DataFrame":
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas required: pip install pandas")
    df = pd.DataFrame(data)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
    return df


def _compute_metrics(returns: np.ndarray, rf_daily: float = 0.0,
                     benchmark_returns: Optional[np.ndarray] = None) -> Dict[str, Any]:
    T = len(returns)

    total_return = float((1 + returns).prod() - 1)
    ann_return = float((1 + total_return) ** (252 / T) - 1) if T > 0 else 0.0
    ann_vol = float(returns.std() * np.sqrt(252))

    excess = returns - rf_daily
    sharpe = float(excess.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0.0

    downside = returns[returns < 0]
    downside_std = downside.std() if len(downside) > 1 else 0.0
    sortino = float(excess.mean() / downside_std * np.sqrt(252)) if downside_std > 0 else 0.0

    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = cumulative / running_max - 1
    max_dd = float(drawdown.min())
    calmar = float(ann_return / abs(max_dd)) if max_dd != 0 else 0.0

    win_rate = float((returns > 0).mean())
    avg_win = float(returns[returns > 0].mean()) if (returns > 0).any() else 0.0
    avg_loss = float(returns[returns < 0].mean()) if (returns < 0).any() else 0.0

    gross_profit = float(returns[returns > 0].sum()) if (returns > 0).any() else 0.0
    gross_loss = float(abs(returns[returns < 0].sum())) if (returns < 0).any() else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    metrics = {
        "total_return": round(total_return, 6),
        "annualized_return": round(ann_return, 6),
        "annualized_volatility": round(ann_vol, 6),
        "sharpe_ratio": round(sharpe, 4),
        "sortino_ratio": round(sortino, 4),
        "max_drawdown": round(max_dd, 6),
        "calmar_ratio": round(calmar, 4),
        "win_rate": round(win_rate, 4),
        "avg_win": round(avg_win, 6),
        "avg_loss": round(avg_loss, 6),
        "profit_factor": round(profit_factor, 4) if np.isfinite(profit_factor) else 9999,
    }

    if benchmark_returns is not None:
        active = returns - benchmark_returns
        tracking_error = float(active.std() * np.sqrt(252))
        ir = float(active.mean() / active.std() * np.sqrt(252)) if active.std() > 0 else 0.0
        beta = float(np.cov(returns, benchmark_returns)[0, 1] / benchmark_returns.var())
        metrics["tracking_error"] = round(tracking_error, 6)
        metrics["information_ratio"] = round(ir, 4)
        metrics["beta"] = round(beta, 4)

    return metrics


def run_backtest(
    prices: List[Dict],
    signals: List[Dict],
    initial_capital: float = 100000,
    transaction_cost: float = 0.001,
    benchmark_prices: Optional[List[Dict]] = None,
    risk_free_rate: float = 0.0,
) -> Dict[str, Any]:
    try:
        import pandas as pd
    except ImportError:
        return {"status": "error", "message": "pandas required: pip install pandas"}

    try:
        price_df = _build_df(prices)
        signal_df = _build_df(signals)
    except Exception as e:
        return {"status": "error", "message": f"Error parsing input data: {e}"}

    common_idx = price_df.index.intersection(signal_df.index)
    if len(common_idx) < 2:
        return {"status": "error", "message": "Insufficient overlapping data points"}

    price_df = price_df.loc[common_idx]
    signal_df = signal_df.loc[common_idx]

    ret_matrix = price_df.pct_change().fillna(0)
    weights = signal_df.div(signal_df.abs().sum(axis=1), axis=0).fillna(0)
    weights = weights.shift(1).fillna(0)

    turnover = weights.diff().abs().sum(axis=1)
    portfolio_returns = (weights * ret_matrix).sum(axis=1)
    portfolio_returns -= turnover * transaction_cost

    rf_daily = risk_free_rate / 252
    bench_ret = None
    if benchmark_prices:
        bench_df = _build_df(benchmark_prices)
        bench_ret_arr = bench_df.pct_change().fillna(0).values.flatten()
        common_len = min(len(portfolio_returns), len(bench_ret_arr))
        portfolio_returns = portfolio_returns.iloc[:common_len]
        bench_ret = bench_ret_arr[:common_len]

    metrics = _compute_metrics(portfolio_returns.values, rf_daily, bench_ret)

    equity = (1 + portfolio_returns).cumprod() * initial_capital
    cumulative = (1 + portfolio_returns.values).cumprod()
    running_max = cumulative.cummax()
    drawdown = cumulative / running_max - 1

    equity_curve = [
        {"date": str(d.date()), "value": round(float(v), 2)}
        for d, v in equity.items()
    ]
    drawdown_curve = [
        {"date": str(portfolio_returns.index[i].date()), "drawdown": round(float(dd), 6)}
        for i, dd in enumerate(drawdown)
    ]

    monthly = portfolio_returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    monthly_returns = {str(d.date()): round(float(r), 6) for d, r in monthly.items()}

    return {
        "status": "success",
        "metrics": metrics,
        "equity_curve": equity_curve,
        "drawdown_curve": drawdown_curve,
        "monthly_returns": monthly_returns,
        "message": f"Backtest complete: {len(portfolio_returns)} trading days",
    }


if __name__ == "__main__":
    import fire
    fire.Fire(run_backtest)
