#!/usr/bin/env python3
"""
Finance Data Loader Tool
Fetches financial data from yfinance, FRED, and Alpha Vantage APIs.
"""

import json
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional


def _load_from_yfinance(symbol: str, start_date: Optional[str] = None,
                        end_date: Optional[str] = None, interval: str = "1d") -> Dict[str, Any]:
    try:
        import yfinance as yf
    except ImportError:
        return {"status": "error", "message": "yfinance required: pip install yfinance"}

    ticker = yf.Ticker(symbol)
    if start_date and end_date:
        hist = ticker.history(start=start_date, end=end_date, interval=interval)
    elif start_date:
        hist = ticker.history(start=start_date, interval=interval)
    else:
        hist = ticker.history(period="5y", interval=interval)

    if hist.empty:
        return {"status": "error", "message": f"No data found for symbol {symbol}"}

    hist.index = hist.index.astype(str)
    data = hist.reset_index().to_dict(orient="records")

    return {"status": "success", "data": data}


def _load_from_fred(symbol: str, start_date: Optional[str] = None,
                    end_date: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
    try:
        from fredapi import Fred
    except ImportError:
        return {"status": "error", "message": "fredapi required: pip install fredapi"}

    key = api_key or os.environ.get("FRED_API_KEY", "")
    if not key:
        return {"status": "error", "message": "FRED API key required: set FRED_API_KEY env var or pass fred_api_key"}

    fred = Fred(api_key=key)
    observation_start = start_date or "1900-01-01"
    series = fred.get_series(symbol, observation_start=observation_start,
                             observation_end=end_date)

    data = [{"date": str(d.date()), "value": float(v) if str(v) != "nan" else None}
            for d, v in series.items()]

    return {"status": "success", "data": data}


def _load_from_alpha_vantage(symbol: str, start_date: Optional[str] = None,
                              end_date: Optional[str] = None,
                              api_key: Optional[str] = None) -> Dict[str, Any]:
    try:
        import requests
    except ImportError:
        return {"status": "error", "message": "requests required: pip install requests"}

    key = api_key or os.environ.get("ALPHA_VANTAGE_KEY", "")
    if not key:
        return {"status": "error", "message": "Alpha Vantage key required: set ALPHA_VANTAGE_KEY env var or pass alpha_vantage_key"}

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "apikey": key,
        "outputsize": "full",
    }
    resp = requests.get(url, params=params)
    raw = resp.json()

    time_series_key = "Time Series (Daily)"
    if time_series_key not in raw:
        return {"status": "error", "message": f"Alpha Vantage error: {raw.get('Error Message', raw)}"}

    data = []
    for date_str, values in raw[time_series_key].items():
        if start_date and date_str < start_date:
            continue
        if end_date and date_str > end_date:
            continue
        data.append({
            "date": date_str,
            "open": float(values["1. open"]),
            "high": float(values["2. high"]),
            "low": float(values["3. low"]),
            "close": float(values["4. close"]),
            "adjusted_close": float(values["5. adjusted close"]),
            "volume": int(values["6. volume"]),
        })

    data.sort(key=lambda x: x["date"])
    return {"status": "success", "data": data}


def _check_cache(cache_path: str, cache_key: str, max_age_hours: int = 24) -> Optional[Dict]:
    p = Path(cache_path) / f"{cache_key}.pkl"
    if not p.exists():
        return None
    age = datetime.now() - datetime.fromtimestamp(p.stat().st_mtime)
    if age >= timedelta(hours=max_age_hours):
        return None
    with open(p, "rb") as f:
        return pickle.load(f)


def _write_cache(cache_path: str, cache_key: str, data: Dict) -> None:
    p = Path(cache_path) / f"{cache_key}.pkl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as f:
        pickle.dump(data, f)


def load_data(
    source: str,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = "1d",
    cache_path: Optional[str] = None,
    fred_api_key: Optional[str] = None,
    alpha_vantage_key: Optional[str] = None,
) -> Dict[str, Any]:
    cache_key = f"{source}_{symbol}_{start_date}_{end_date}_{interval}".replace("/", "_")
    cached = False

    if cache_path:
        cached_result = _check_cache(cache_path, cache_key)
        if cached_result is not None:
            cached_result["metadata"]["cached"] = True
            return cached_result

    if source == "yfinance":
        result = _load_from_yfinance(symbol, start_date, end_date, interval)
    elif source == "fred":
        result = _load_from_fred(symbol, start_date, end_date, fred_api_key)
    elif source == "alpha_vantage":
        result = _load_from_alpha_vantage(symbol, start_date, end_date, alpha_vantage_key)
    else:
        return {"status": "error", "message": f"Unknown source: {source}"}

    if result["status"] == "success":
        rows = len(result["data"])
        result["metadata"] = {
            "source": source,
            "symbol": symbol,
            "start_date": start_date or "earliest",
            "end_date": end_date or "latest",
            "rows": rows,
            "columns": len(result["data"][0]) if rows > 0 else 0,
            "fetch_timestamp": datetime.now().isoformat(),
            "cached": False,
        }

        if cache_path and rows > 0:
            _write_cache(cache_path, cache_key, result)

    return result


if __name__ == "__main__":
    import fire
    fire.Fire(load_data)
