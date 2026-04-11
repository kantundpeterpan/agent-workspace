---
name: bayesian-inference
description: Specifies probabilistic models in PyMC, runs MCMC/VI, diagnoses convergence, interprets posteriors, and performs posterior predictive checks
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Bayesian Inference

Workflow for building, sampling, diagnosing, and reporting Bayesian
probabilistic models using PyMC.

## When to Use

- Incorporating prior knowledge into an analysis
- Quantifying uncertainty beyond point estimates
- Hierarchical / multi-level models
- Small-sample analyses where asymptotic results are unreliable
- When full posterior distributions are needed

## Workflow

### 1. State the Generative Model

Write out the model mathematically before coding:

```
μ_i = α + β₁x₁ᵢ + β₂x₂ᵢ
y_i ~ Normal(μ_i, σ)

Priors:
  α ~ Normal(0, 10)
  β₁, β₂ ~ Normal(0, 2)
  σ ~ HalfNormal(5)
```

### 2. Elicit Priors

For each parameter:
- What scale is plausible? Use domain knowledge or standardise predictors.
- Use `pm.do_prior_predictive_checks()` to visualise implied outcomes.

```python
import pymc as pm
import numpy as np
import matplotlib.pyplot as plt

with pm.Model() as model:
    alpha = pm.Normal("alpha", mu=0, sigma=10)
    beta = pm.Normal("beta", mu=0, sigma=2, shape=2)
    sigma = pm.HalfNormal("sigma", sigma=5)

    mu = alpha + beta[0] * X[:, 0] + beta[1] * X[:, 1]
    y_obs = pm.Normal("y_obs", mu=mu, sigma=sigma, observed=y)

    # Prior predictive check
    prior_pred = pm.sample_prior_predictive(samples=200)

fig, ax = plt.subplots()
ax.hist(prior_pred.prior_predictive["y_obs"].values.flatten(), bins=50)
ax.set_title("Prior predictive distribution"); ax.set_xlabel("y")
fig.savefig("figures/bayes_prior_predictive.png", dpi=150)
```

### 3. Sample the Posterior

```python
with model:
    trace = pm.sample(
        draws=2000,
        tune=1000,
        chains=4,
        cores=4,
        random_seed=42,
        target_accept=0.9,
    )
```

### 4. Diagnose Convergence

```python
import arviz as az

# Numerical convergence diagnostics
summary = az.summary(trace, var_names=["alpha", "beta", "sigma"])
print(summary)
# R-hat < 1.01 and ESS_bulk > 400 required

# Trace plots
az.plot_trace(trace, var_names=["alpha", "beta", "sigma"])
plt.savefig("figures/bayes_trace.png", dpi=150)

# Energy plot
az.plot_energy(trace)
plt.savefig("figures/bayes_energy.png", dpi=150)

# Rank plots (MCMC mixing diagnostic)
az.plot_rank(trace, var_names=["alpha", "beta"])
plt.savefig("figures/bayes_rank.png", dpi=150)
```

**Convergence thresholds:**
- R-hat < 1.01 for all parameters
- ESS_bulk > 400, ESS_tail > 400
- No divergences (or < 0.1% of samples)

### 5. Posterior Summary

```python
# Posterior distribution plot
az.plot_posterior(trace, var_names=["beta"], hdi_prob=0.94)
plt.savefig("figures/bayes_posterior.png", dpi=150)

print(az.summary(trace, var_names=["beta"], hdi_prob=0.94))
```

Report: posterior mean, 94% HDI (Highest Density Interval).

### 6. Posterior Predictive Check

```python
with model:
    ppc = pm.sample_posterior_predictive(trace)

az.plot_ppc(az.from_pymc(posterior_predictive=ppc, model=model))
plt.savefig("figures/bayes_ppc.png", dpi=150)
```

### 7. Report Results

```
We specified a Bayesian linear regression with weakly informative priors
(α ~ N(0, 10), β ~ N(0, 2), σ ~ HalfNormal(5)).
Posterior sampling used NUTS (4 chains × 2,000 draws; 1,000 warm-up).
All parameters converged (R-hat < 1.01; ESS_bulk > 800).

β₁ had a posterior mean of 0.43 (94% HDI: [0.28, 0.58]), providing
strong evidence of a positive association with the outcome.
```

## Review Checklist

- [ ] Generative model written out mathematically before coding
- [ ] Priors justified (domain knowledge or prior predictive check)
- [ ] At least 4 chains sampled
- [ ] R-hat < 1.01 for all parameters
- [ ] ESS_bulk > 400 for all parameters
- [ ] Divergence count reported
- [ ] Trace, energy, and rank plots saved
- [ ] Posterior predictive check performed
- [ ] Results reported with posterior mean + HDI (not p-values)
