---
name: statistical-inference
description: Fits, diagnoses, and interprets classical and generalised linear models with formal hypothesis testing, confidence intervals, and APA-style reporting
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Statistical Inference

Systematic workflow for model specification, fitting, assumption checking,
and results reporting for classical and generalised linear models.

## When to Use

- Fitting OLS, logistic, Poisson, or mixed-effects models
- Performing formal hypothesis tests on coefficients
- Computing confidence intervals and effect sizes
- Writing the Methods and Results sections for a paper

## Modelling Workflow

### 1. Specify the Model

Write out the statistical model before fitting:

```
Linear:  Y_i = β₀ + β₁X₁ᵢ + β₂X₂ᵢ + εᵢ,  εᵢ ~ N(0, σ²)
Logistic: logit(P(Y=1)) = β₀ + β₁X₁ + β₂X₂
Poisson:  log(μᵢ) = β₀ + β₁X₁ᵢ + β₂X₂ᵢ
```

State the estimand (ATE, conditional effect, etc.) explicitly.

### 2. Fit the Model

```python
import statsmodels.formula.api as smf
import pandas as pd

# OLS
model = smf.ols("outcome ~ predictor1 + C(group)", data=df).fit()

# Logistic
model = smf.logit("binary_outcome ~ x1 + x2", data=df).fit()

# Poisson
model = smf.poisson("count ~ x1 + x2", data=df).fit()

# Mixed-effects (LME4-style)
import statsmodels.formula.api as smf
model = smf.mixedlm("y ~ x1 + x2", data=df, groups=df["subject_id"]).fit()

print(model.summary())
```

### 3. Check Assumptions

```python
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

residuals = model.resid
fitted = model.fittedvalues

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Residuals vs Fitted
axes[0,0].scatter(fitted, residuals, alpha=0.4)
axes[0,0].axhline(0, color='red', lw=1)
axes[0,0].set_xlabel("Fitted"); axes[0,0].set_ylabel("Residuals")
axes[0,0].set_title("Residuals vs Fitted")

# Q-Q plot
stats.probplot(residuals, plot=axes[0,1])
axes[0,1].set_title("Normal Q-Q")

# Scale-Location
axes[1,0].scatter(fitted, np.sqrt(np.abs(residuals)), alpha=0.4)
axes[1,0].set_xlabel("Fitted"); axes[1,0].set_ylabel("√|Residuals|")
axes[1,0].set_title("Scale-Location")

# Cook's distance
influence = model.get_influence()
(c, p) = influence.cooks_distance
axes[1,1].stem(range(len(c)), c, markerfmt=",", basefmt="b-")
axes[1,1].axhline(4/len(df), color='red', lw=1, label=f"4/n={4/len(df):.4f}")
axes[1,1].set_title("Cook's Distance"); axes[1,1].legend()

fig.tight_layout()
fig.savefig("figures/regression_diagnostics.png", dpi=150)
```

### 4. Check Multicollinearity

```python
from statsmodels.stats.outliers_influence import variance_inflation_factor

X = model.model.exog
vif = pd.DataFrame({
    "feature": model.model.exog_names,
    "VIF": [variance_inflation_factor(X, i) for i in range(X.shape[1])]
})
print(vif[vif["VIF"] > 5])  # flag if VIF > 5
```

### 5. Report Results (APA Format)

```
A multiple linear regression was conducted to predict {outcome} from
{predictors}. The model explained a significant proportion of variance,
R² = .34, F(3, 196) = 33.5, p < .001.

Predictor1 was a significant positive predictor, β = 0.42, 95% CI [0.28, 0.56],
t(196) = 5.91, p < .001.

Predictor2 was not significant, β = 0.08, 95% CI [−0.04, 0.21],
t(196) = 1.30, p = .196.
```

### 6. Confidence Intervals

```python
ci = model.conf_int(alpha=0.05)
ci.columns = ["Lower 95%", "Upper 95%"]
results = pd.concat([model.params, model.pvalues, ci], axis=1)
results.columns = ["Estimate", "p-value", "Lower 95%", "Upper 95%"]
print(results.round(4))
```

## Review Checklist

- [ ] Model equation written out before fitting
- [ ] Estimand stated clearly
- [ ] Residuals vs Fitted, Q-Q, Scale-Location, Cook's D plots generated
- [ ] VIF checked for multicollinearity
- [ ] Coefficient table with CIs and p-values
- [ ] Results reported in APA format (β, CI, t/z, p)
- [ ] Effect sizes reported (standardised β, R², pseudo-R²)
- [ ] Diagnostic plots saved to `figures/`
