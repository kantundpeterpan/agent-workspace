#!/usr/bin/env python3
"""
Options Calculator Tool
Prices options, computes Greeks, implied volatility, and payoff diagrams.
"""

import json
from typing import Any, Dict, Optional

import numpy as np
from scipy.stats import norm


def _black_scholes_price(S: float, K: float, T: float, r: float, sigma: float,
                          q: float = 0.0, option_type: str = "call") -> float:
    if sigma <= 0 or T <= 0:
        if option_type == "call":
            return max(0.0, S - K)
        else:
            return max(0.0, K - S)

    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "call":
        return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)


def _compute_greeks(S: float, K: float, T: float, r: float, sigma: float,
                     q: float = 0.0, option_type: str = "call") -> Dict[str, float]:
    if sigma <= 0 or T <= 0:
        return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0}

    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    gamma = np.exp(-q * T) * norm.pdf(d1) / (S * sigma * np.sqrt(T))

    if option_type == "call":
        delta = np.exp(-q * T) * norm.cdf(d1)
        theta = (-S * np.exp(-q * T) * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                 + q * S * np.exp(-q * T) * norm.cdf(d1)
                 - r * K * np.exp(-r * T) * norm.cdf(d2))
        rho = K * T * np.exp(-r * T) * norm.cdf(d2)
    else:
        delta = -np.exp(-q * T) * norm.cdf(-d1)
        theta = (-S * np.exp(-q * T) * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                 - q * S * np.exp(-q * T) * norm.cdf(-d1)
                 + r * K * np.exp(-r * T) * norm.cdf(-d2))
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)

    vega = S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T)

    return {
        "delta": round(float(delta), 6),
        "gamma": round(float(gamma), 6),
        "theta": round(float(theta / 365), 6),
        "vega": round(float(vega / 100), 6),
        "rho": round(float(rho / 100), 6),
    }


def _binomial_price(S: float, K: float, T: float, r: float, sigma: float,
                     q: float = 0.0, option_type: str = "call",
                     steps: int = 200, american: bool = True) -> float:
    if sigma <= 0 or T <= 0 or steps == 0:
        return _black_scholes_price(S, K, T, r, 0.001, q, option_type)

    dt = T / steps
    u = np.exp(sigma * np.sqrt(dt))
    d = 1 / u
    p = (np.exp((r - q) * dt) - d) / (u - d)
    disc = np.exp(-r * dt)

    S_tree = np.zeros((steps + 1, steps + 1))
    for i in range(steps + 1):
        for j in range(i + 1):
            S_tree[j, i] = S * (u ** (i - j)) * (d ** j)

    if option_type == "call":
        V = np.maximum(S_tree[:, steps] - K, 0)
    else:
        V = np.maximum(K - S_tree[:, steps], 0)

    for i in range(steps - 1, -1, -1):
        V = disc * (p * V[:-1] + (1 - p) * V[1:])
        if american:
            if option_type == "call":
                V = np.maximum(V, S_tree[:i + 1, i] - K)
            else:
                V = np.maximum(V, K - S_tree[:i + 1, i])

    return float(V[0])


def _monte_carlo_price(S: float, K: float, T: float, r: float, sigma: float,
                        q: float = 0.0, option_type: str = "call",
                        n_sims: int = 100000) -> Dict[str, Any]:
    if sigma <= 0 or T <= 0:
        price = max(0.0, S - K) if option_type == "call" else max(0.0, K - S)
        return {"price": price, "se": 0.0, "ci_lower": price, "ci_upper": price}

    np.random.seed(42)
    z = np.random.standard_normal(n_sims)
    ST = S * np.exp((r - q - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * z)

    if option_type == "call":
        payoffs = np.maximum(ST - K, 0)
    else:
        payoffs = np.maximum(K - ST, 0)

    price = float(np.exp(-r * T) * payoffs.mean())
    se = float(payoffs.std() / np.sqrt(n_sims))

    return {
        "price": round(price, 6),
        "se": round(se, 6),
        "ci_lower": round(price - 1.96 * se, 6),
        "ci_upper": round(price + 1.96 * se, 6),
    }


def _implied_volatility(market_price: float, S: float, K: float, T: float,
                         r: float, q: float = 0.0, option_type: str = "call",
                         tol: float = 1e-8, max_iter: int = 100) -> Optional[float]:
    sigma = 0.3
    for _ in range(max_iter):
        price = _black_scholes_price(S, K, T, r, sigma, q, option_type)
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        vega = S * np.exp(-q * T) * np.sqrt(T) * norm.pdf(d1)
        if abs(vega) < 1e-10:
            return None
        diff = price - market_price
        if abs(diff) < tol:
            return float(round(sigma, 6))
        sigma -= diff / vega
    return None


def _payoff_diagram(S: float, K: float, T: float, r: float, sigma: float,
                     q: float = 0.0, option_type: str = "call",
                     payoff_range: float = 0.3, n_points: int = 100) -> Dict[str, Any]:
    price = _black_scholes_price(S, K, T, r, sigma, q, option_type)
    spot_min = S * (1 - payoff_range)
    spot_max = S * (1 + payoff_range)
    spot_range = np.linspace(spot_min, spot_max, n_points)

    payoff = []
    for st in spot_range:
        pnl = st - S
        if option_type == "call":
            option_pnl = max(st - K, 0) - price
        else:
            option_pnl = max(K - st, 0) - price
        payoff.append(round(float(option_pnl), 4))

    return {
        "spot_range": [round(float(s), 2) for s in spot_range],
        "payoff": payoff,
    }


def calculate(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    option_type: str = "call",
    model: str = "black_scholes",
    binomial_steps: int = 200,
    monte_carlo_sims: int = 100000,
    payoff_range: float = 0.3,
) -> Dict[str, Any]:
    if model == "black_scholes":
        price = _black_scholes_price(S, K, T, r, sigma, q, option_type)
        mc_result = None
    elif model == "binomial":
        price = _binomial_price(S, K, T, r, sigma, q, option_type, binomial_steps)
        mc_result = None
    elif model == "monte_carlo":
        mc_result = _monte_carlo_price(S, K, T, r, sigma, q, option_type, monte_carlo_sims)
        price = mc_result["price"]
    else:
        return {"status": "error", "message": f"Unknown model: {model}"}

    greeks = _compute_greeks(S, K, T, r, sigma, q, option_type)
    payoff = _payoff_diagram(S, K, T, r, sigma, q, option_type, payoff_range)

    result = {
        "status": "success",
        "price": round(float(price), 6),
        "greeks": greeks,
        "payoff_diagram": payoff,
        "implied_volatility": round(float(sigma), 6),
        "message": f"Priced {option_type} option using {model} model",
    }

    if mc_result:
        result["monte_carlo"] = mc_result

    return result


if __name__ == "__main__":
    import fire
    fire.Fire(calculate)
