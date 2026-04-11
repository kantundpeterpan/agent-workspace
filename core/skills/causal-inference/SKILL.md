---
name: causal-inference
description: Designs causal studies and estimates treatment effects using propensity scores, difference-in-differences, instrumental variables, and regression discontinuity, with formal assumption checks
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Causal Inference

Systematic workflow for moving from association to causation — designing
studies, selecting estimators, checking identification assumptions, and
reporting treatment effects.

## When to Use

- Estimating the effect of a treatment/intervention
- Analysing observational data where randomisation was not possible
- A/B test analysis (randomised experiment)
- Programme evaluation

## Causal Framework

Always begin by stating:
1. **Estimand**: What causal effect are we estimating? (ATE, ATT, LATE)
2. **Treatment**: Binary/continuous, how was it assigned?
3. **Potential outcomes**: Y(1) and Y(0) for each unit
4. **Identification assumptions**: What must hold for causal interpretation?

## Method Selection

| Study Design | Method | Key Assumption |
|---|---|---|
| Randomised experiment | OLS / t-test on outcomes | Randomisation |
| Observational (selection on observables) | Propensity score matching / IPW | Unconfoundedness |
| Panel data, policy change | Difference-in-Differences | Parallel trends |
| Instrumental variable available | IV / 2SLS | Exclusion restriction + relevance |
| Threshold-based treatment | Regression Discontinuity | Local continuity |
| Matched time series | Synthetic Control | Donor pool similarity |

## Workflows

### Propensity Score Matching

```python
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import numpy as np, pandas as pd

# Estimate propensity scores
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[confounders])
ps_model = LogisticRegression(max_iter=1000)
ps_model.fit(X_scaled, df["treatment"])
df["ps"] = ps_model.predict_proba(X_scaled)[:, 1]

# Check overlap (common support)
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
df[df.treatment==1]["ps"].hist(ax=ax, bins=30, alpha=0.5, label="Treated")
df[df.treatment==0]["ps"].hist(ax=ax, bins=30, alpha=0.5, label="Control")
ax.set_xlabel("Propensity score"); ax.legend()
fig.savefig("figures/propensity_overlap.png", dpi=150)
```

### Balance Table

```python
from scipy import stats

rows = []
for col in confounders:
    treated = df[df.treatment==1][col]
    control = df[df.treatment==0][col]
    smd = (treated.mean() - control.mean()) / np.sqrt(
        (treated.std()**2 + control.std()**2) / 2
    )
    rows.append({"Variable": col, "Treated mean": treated.mean().round(3),
                 "Control mean": control.mean().round(3), "SMD": smd.round(3)})

balance = pd.DataFrame(rows)
print(balance)
# SMD < 0.1 is well-balanced
```

### Difference-in-Differences

```python
import statsmodels.formula.api as smf

# DiD regression: Y ~ post + treated + post*treated + controls
did_model = smf.ols(
    "outcome ~ post * treated + age + income",
    data=df_panel
).fit(cov_type="cluster", cov_kwds={"groups": df_panel["unit_id"]})

print(did_model.summary())
att = did_model.params["post:treated"]
ci = did_model.conf_int().loc["post:treated"]
print(f"ATT = {att:.4f}, 95% CI [{ci[0]:.4f}, {ci[1]:.4f}]")
```

### Parallel Trends Check

```python
# Plot pre-period trends for treated and control groups
pre = df_panel[df_panel.post == 0]
trends = pre.groupby(["time", "treated"])["outcome"].mean().unstack()
fig, ax = plt.subplots()
trends.plot(ax=ax); ax.set_title("Pre-period trends (must be parallel)")
fig.savefig("figures/parallel_trends.png", dpi=150)
```

## Reporting

```
Using propensity score matching (nearest-neighbour, caliper = 0.02),
we estimated the average treatment effect on the treated (ATT).
Covariate balance was assessed using standardised mean differences (SMD);
all SMDs fell below 0.10 after matching (see Table 2).

The ATT was estimated at 3.2 percentage points (95% CI [1.4, 5.0],
p = .001), indicating that participation in the programme increased
the outcome by approximately 3.2 pp among treated units.
```

## Review Checklist

- [ ] Estimand (ATE/ATT/LATE) stated explicitly
- [ ] Identification assumptions stated and justified
- [ ] Balance table with SMD computed
- [ ] Overlap/common-support plot generated
- [ ] Parallel-trends plot for DiD
- [ ] Clustered or robust standard errors used
- [ ] Sensitivity analysis (Rosenbaum bounds or placebo test)
- [ ] Effect estimate with CI and interpretation in substantive terms
