#!/usr/bin/env python3
"""
Portfolio Optimizer Tool
Runs mean-variance, risk-parity, and Black-Litterman portfolio optimisation.
"""

import json
from typing import Any, Dict, List, Optional

import numpy as np
from scipy.optimize import minimize


def _build_returns_matrix(returns_data: List[Dict]) -> np.ndarray:
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas required: pip install pandas")

    df = pd.DataFrame(returns_data)
    return df.values, list(df.columns)


def _markowitz(mu: np.ndarray, Sigma: np.ndarray, lambda_val: float = 1.0,
               max_weight: float = 1.0) -> np.ndarray:
    n = len(mu)

    def objective(w):
        return 0.5 * w @ Sigma @ w - lambda_val * mu @ w

    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    bounds = [(0, max_weight)] * n
    w0 = np.ones(n) / n

    result = minimize(objective, w0, bounds=bounds, constraints=constraints, method="SLSQP")
    return result.x


def _min_variance(Sigma: np.ndarray, max_weight: float = 1.0) -> np.ndarray:
    n = Sigma.shape[0]

    def objective(w):
        return w @ Sigma @ w

    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    bounds = [(0, max_weight)] * n
    w0 = np.ones(n) / n

    result = minimize(objective, w0, bounds=bounds, constraints=constraints, method="SLSQP")
    return result.x


def _max_sharpe(mu: np.ndarray, Sigma: np.ndarray, rf: float = 0.0,
                max_weight: float = 1.0) -> np.ndarray:
    n = len(mu)
    excess = mu - rf

    def neg_sharpe(w):
        port_excess = w @ excess
        port_vol = np.sqrt(w @ Sigma @ w)
        return -port_excess / port_vol if port_vol > 1e-10 else 1e10

    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    bounds = [(0, max_weight)] * n
    w0 = np.ones(n) / n

    result = minimize(neg_sharpe, w0, bounds=bounds, constraints=constraints, method="SLSQP")
    return result.x


def _risk_parity(Sigma: np.ndarray, max_weight: float = 1.0) -> np.ndarray:
    n = Sigma.shape[0]

    def risk_contributions(w):
        port_vol = np.sqrt(w @ Sigma @ w)
        mrc = Sigma @ w / port_vol
        rc = w * mrc
        return rc

    def objective(w):
        rc = risk_contributions(w)
        target = rc.sum() / n
        return np.sum((rc - target) ** 2)

    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    bounds = [(0, max_weight)] * n
    w0 = np.ones(n) / n

    result = minimize(objective, w0, bounds=bounds, constraints=constraints, method="SLSQP")
    return result.x


def _black_litterman(pi: np.ndarray, Sigma: np.ndarray, P: np.ndarray,
                     Q: np.ndarray, Omega: np.ndarray, tau: float = 0.025) -> np.ndarray:
    tau_Sigma_inv = np.linalg.inv(tau * Sigma)
    Omega_inv = np.linalg.inv(Omega)

    M = np.linalg.inv(tau_Sigma_inv + P.T @ Omega_inv @ P)
    mu_bl = M @ (tau_Sigma_inv @ pi + P.T @ Omega_inv @ Q)
    Sigma_bl = Sigma + M

    return mu_bl, Sigma_bl


def _compute_efficient_frontier(mu: np.ndarray, Sigma: np.ndarray,
                                 max_weight: float = 1.0, n_points: int = 30) -> Dict:
    n = len(mu)
    frontiers_returns = []
    frontiers_vols = []

    min_var_w = _min_variance(Sigma, max_weight)
    max_ret_w_idx = np.argmax(mu)
    max_ret_w = np.zeros(n)
    max_ret_w[max_ret_w_idx] = min(max_weight, 1.0)
    remaining = 1.0 - max_ret_w[max_ret_w_idx]
    others = [i for i in range(n) if i != max_ret_w_idx]
    if others:
        eq_other = remaining / len(others)
        for i in others:
            max_ret_w[i] = eq_other

    min_ret = min_var_w @ mu
    max_ret = max_ret_w @ mu

    target_returns = np.linspace(min_ret, max_ret, n_points)
    for target in target_returns:
        def objective(w):
            return w @ Sigma @ w
        constraints = [
            {"type": "eq", "fun": lambda w: w.sum() - 1},
            {"type": "eq", "fun": lambda w, t=target: w @ mu - t},
        ]
        bounds = [(0, max_weight)] * n
        w0 = np.ones(n) / n
        res = minimize(objective, w0, bounds=bounds, constraints=constraints, method="SLSQP")
        if res.success:
            frontiers_returns.append(target)
            frontiers_vols.append(np.sqrt(res.x @ Sigma @ res.x))

    return {"returns": frontiers_returns, "volatilities": frontiers_vols}


def optimize(
    method: str,
    returns: List[Dict],
    lambda_val: float = 1.0,
    target_return: Optional[float] = None,
    max_weight: float = 1.0,
    market_weights: Optional[List[float]] = None,
    views: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    try:
        ret_matrix, asset_names = _build_returns_matrix(returns)
    except Exception as e:
        return {"status": "error", "message": f"Error building returns matrix: {e}"}

    n_assets = len(asset_names)
    mu = ret_matrix.mean(axis=0) * 252
    Sigma = np.cov(ret_matrix.T) * 252

    try:
        if method == "markowitz":
            weights = _markowitz(mu, Sigma, lambda_val, max_weight)
        elif method == "max_sharpe":
            weights = _max_sharpe(mu, Sigma, max_weight=max_weight)
        elif method == "min_variance":
            weights = _min_variance(Sigma, max_weight)
        elif method == "risk_parity":
            weights = _risk_parity(Sigma, max_weight)
        elif method == "black_litterman":
            if not market_weights or not views:
                return {"status": "error",
                        "message": "market_weights and views required for Black-Litterman"}
            market_w = np.array(market_weights)
            if len(market_w) != n_assets:
                return {"status": "error", "message": "market_weights length must match number of assets"}
            pi = lambda_val * Sigma @ market_w
            P = np.array([v.get("pick", []) for v in views])
            Q = np.array([v.get("value", 0.0) for v in views])
            diag = [v.get("confidence", 0.1) for v in views]
            Omega = np.diag(diag)
            mu_bl, Sigma_bl = _black_litterman(pi, Sigma, P, Q, Omega)
            weights = _markowitz(mu_bl, Sigma_bl, lambda_val, max_weight)
        else:
            return {"status": "error", "message": f"Unknown method: {method}"}
    except Exception as e:
        return {"status": "error", "message": f"Optimization failed: {e}"}

    weights = np.clip(weights, 0, 1)
    weights = weights / weights.sum()

    port_ret = weights @ mu
    port_vol = np.sqrt(weights @ Sigma @ weights)
    sharpe = (port_ret - 0.0) / port_vol if port_vol > 1e-10 else 0.0

    mrc = Sigma @ weights / port_vol if port_vol > 1e-10 else np.zeros(n_assets)
    risk_contrib = weights * mrc
    risk_contrib_pct = risk_contrib / risk_contrib.sum() if risk_contrib.sum() > 0 else risk_contrib

    weights_dict = {}
    risk_contrib_dict = {}
    for i, name in enumerate(asset_names):
        weights_dict[name] = round(float(weights[i]), 6)
        risk_contrib_dict[name] = {
            "marginal_contribution": round(float(mrc[i]), 6),
            "component_contribution": round(float(risk_contrib[i]), 6),
            "pct_contribution": round(float(risk_contrib_pct[i] * 100), 2),
        }

    frontier = _compute_efficient_frontier(mu, Sigma, max_weight)

    return {
        "status": "success",
        "weights": weights_dict,
        "portfolio_return": round(float(port_ret), 6),
        "portfolio_volatility": round(float(port_vol), 6),
        "sharpe_ratio": round(float(sharpe), 4),
        "risk_contributions": risk_contrib_dict,
        "efficient_frontier": frontier,
        "message": f"Optimised {n_assets} assets using {method} method",
    }


if __name__ == "__main__":
    import fire
    fire.Fire(optimize)
