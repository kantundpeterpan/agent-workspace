---
name: time-series-analysis
description: Full time series workflow — stationarity testing, decomposition, ACF/PACF, model selection (ARIMA/ETS/Prophet), walk-forward validation, and forecast with prediction intervals
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Time Series Analysis

Systematic workflow for analysing temporal data and producing validated
forecasts with uncertainty quantification.

## When to Use

- Forecasting future values of a time-indexed variable
- Decomposing a series into trend, seasonality, and residual
- Testing for stationarity, unit roots, or structural breaks
- Evaluating multiple forecasting models

## Workflow

### 1. Load and Inspect

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/processed/timeseries.csv", parse_dates=["date"], index_col="date")
series = df["value"].asfreq("MS")  # set correct frequency

fig, ax = plt.subplots(figsize=(12, 4))
series.plot(ax=ax); ax.set_title("Raw series"); ax.set_ylabel("Value")
fig.tight_layout(); fig.savefig("figures/ts_raw.png", dpi=150)
```

### 2. Stationarity Tests

```python
from statsmodels.tsa.stattools import adfuller, kpss

# Augmented Dickey-Fuller (H₀: unit root / non-stationary)
adf_result = adfuller(series.dropna())
print(f"ADF: stat={adf_result[0]:.4f}, p={adf_result[1]:.4f}")

# KPSS (H₀: stationary)
kpss_result = kpss(series.dropna(), regression="c")
print(f"KPSS: stat={kpss_result[0]:.4f}, p={kpss_result[1]:.4f}")
```

Interpretation:
- $p_\text{ADF} < 0.05$ and $p_\text{KPSS} > 0.05$ → stationary
- Otherwise → difference or transform ($\log$, $\sqrt{\cdot}$)

### 3. Decomposition

```python
from statsmodels.tsa.seasonal import seasonal_decompose

decomp = seasonal_decompose(series, model="additive", period=12)
fig = decomp.plot()
fig.set_size_inches(12, 8)
fig.savefig("figures/ts_decomposition.png", dpi=150)
```

### 4. ACF and PACF

```python
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

fig, axes = plt.subplots(1, 2, figsize=(14, 4))
plot_acf(series.diff().dropna(), lags=40, ax=axes[0])
plot_pacf(series.diff().dropna(), lags=40, ax=axes[1])
axes[0].set_title("ACF (after differencing)")
axes[1].set_title("PACF (after differencing)")
fig.tight_layout(); fig.savefig("figures/ts_acf_pacf.png", dpi=150)
```

### 5. Fit Models

The general $\text{ARIMA}(p, d, q)$ model is:

$$\phi(B)(1-B)^d y_t = \theta(B)\,\varepsilon_t, \qquad \varepsilon_t \sim \mathcal{N}(0, \sigma^2)$$

where $B$ is the backshift operator, $\phi(B) = 1 - \phi_1 B - \cdots - \phi_p B^p$ is the
AR polynomial, and $\theta(B) = 1 + \theta_1 B + \cdots + \theta_q B^q$ is the MA polynomial.

> **Math notation:** Use `$...$` for inline model parameters (e.g., `$\phi_1$`,
> `$\sigma^2$`, `$\text{AIC}$`) and `$$...$$` for display equations.

```python
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import pmdarima as pm

# Auto-ARIMA (automatic order selection)
auto_model = pm.auto_arima(train, seasonal=True, m=12,
                            stepwise=True, information_criterion="aic")
print(auto_model.summary())

# Exponential Smoothing (Holt-Winters)
ets_model = ExponentialSmoothing(train, trend="add", seasonal="add",
                                  seasonal_periods=12).fit()
```

### 6. Walk-Forward Validation

```python
from sklearn.metrics import mean_absolute_error, mean_squared_error

def walk_forward_rmse(series, train_size, horizon=1):
    errors = []
    for i in range(train_size, len(series) - horizon + 1):
        train = series[:i]
        actual = series[i:i+horizon]
        model = pm.auto_arima(train, seasonal=True, m=12, stepwise=True)
        forecast = model.predict(n_periods=horizon)
        errors.append(mean_squared_error(actual, forecast, squared=False))
    return errors

rmse_list = walk_forward_rmse(series, train_size=48)
print(f"Walk-forward RMSE: {pd.Series(rmse_list).mean():.4f} ± {pd.Series(rmse_list).std():.4f}")
```

### 7. Forecast with Prediction Intervals

```python
forecast, conf_int = auto_model.predict(n_periods=24, return_conf_int=True)
forecast_idx = pd.date_range(series.index[-1], periods=25, freq="MS")[1:]

fig, ax = plt.subplots(figsize=(12, 5))
series[-36:].plot(ax=ax, label="Historical")
pd.Series(forecast, index=forecast_idx).plot(ax=ax, label="Forecast", linestyle="--")
ax.fill_between(forecast_idx, conf_int[:,0], conf_int[:,1], alpha=0.2, label="95% PI")
ax.legend(); ax.set_title("24-Month Forecast with 95% Prediction Interval")
fig.savefig("figures/ts_forecast.png", dpi=150)
```

## Review Checklist

- [ ] Series plotted; frequency and gaps identified
- [ ] Stationarity tested (ADF + KPSS), transformations applied
- [ ] Decomposition plot saved
- [ ] ACF/PACF after differencing saved
- [ ] At least 2 models fitted and compared (ARIMA, ETS, baseline)
- [ ] Walk-forward validation used (not train/test split)
- [ ] Forecast plot with prediction intervals saved
- [ ] RMSE and MAE reported for model comparison
