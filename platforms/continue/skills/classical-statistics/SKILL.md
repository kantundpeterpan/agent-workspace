---
name: classical-statistics
description: Applies classical frequentist statistical methods — hypothesis testing, ANOVA, regression, non-parametric tests, chi-square, survival analysis — with full assumption checking and APA-style reporting
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Classical Statistics

Systematic workflow for applying and reporting classical (frequentist) statistical
analyses, covering test selection, assumption checking, execution, and formal reporting.

## When to Use

- Comparing group means (t-tests, ANOVA)
- Testing associations (chi-square, correlation, regression)
- Non-parametric alternatives when normality is violated
- Survival / time-to-event analysis
- Power and sample size planning
- Any analysis requiring APA-style statistical reporting

## Test Selection Guide

### Comparing Two Groups

| Data Type | Equal Variances | Test |
|---|---|---|
| Continuous, normal | Yes | Independent samples *t*-test |
| Continuous, normal | No | Welch's *t*-test |
| Continuous, non-normal | — | Mann-Whitney *U* |
| Binary / count | — | Chi-square / Fisher's exact |
| Paired continuous | Normal differences | Paired *t*-test |
| Paired continuous | Non-normal | Wilcoxon signed-rank |

### Comparing Three or More Groups

| Design | Parametric | Non-parametric |
|---|---|---|
| One factor, independent | One-way ANOVA | Kruskal-Wallis |
| One factor, repeated | Repeated-measures ANOVA | Friedman |
| Two factors | Two-way ANOVA | Scheirer-Ray-Hare |
| Mixed (between + within) | Mixed ANOVA | — |

### Association / Prediction

| Outcome type | Predictors | Model |
|---|---|---|
| Continuous | Continuous/categorical | OLS regression |
| Binary | Any | Logistic regression |
| Count | Any | Poisson / NB regression |
| Ordered categorical | Any | Ordinal logistic regression |
| Time-to-event | Any | Cox proportional hazards |
| Continuous, correlated | Any | Linear mixed-effects model |

## Analysis Workflow

### 1. Formulate Hypotheses

State null and alternative hypotheses precisely before looking at data:
- $H_0: \mu_1 = \mu_2$
- $H_1: \mu_1 \neq \mu_2$ (two-sided) or $H_1: \mu_1 > \mu_2$ (one-sided)

Specify $\alpha$ level (default 0.05) and test direction upfront.

> **Math notation:** Use `$...$` for all inline statistical symbols and expressions
> (e.g., `$H_0$`, `$\mu$`, `$\sigma^2$`, `$\alpha = .05$`, `$\chi^2$`) and
> `$$...$$` for display equations.

### 2. Check Assumptions

**For parametric tests:**
- Normality: Shapiro-Wilk (*n* < 50) or Q-Q plot (*n* ≥ 50)
- Homogeneity of variance: Levene's test
- Independence: confirmed by study design

**For regression:**
- Linearity: residual vs fitted plot
- Normality of residuals: Q-Q plot
- Homoscedasticity: Breusch-Pagan test / scale-location plot
- Independence: Durbin-Watson
- No multicollinearity: VIF < 5 (warn), < 10 (critical)
- Influential points: Cook's distance > 4/*n*

### 3. Run the Test

```python
from scipy import stats
import statsmodels.formula.api as smf

# Welch t-test
t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)

# One-way ANOVA
f_stat, p_val = stats.f_oneway(g1, g2, g3)

# Chi-square test of independence
chi2, p_val, dof, expected = stats.chi2_contingency(contingency_table)

# OLS regression
model = smf.ols('outcome ~ predictor1 + C(group)', data=df).fit()
print(model.summary())
```

### 4. Compute Effect Sizes

| Test | Effect size | Formula |
|---|---|---|
| *t*-test | Cohen's *d* | $d = (M_1 - M_2) / SD_\text{pooled}$ |
| ANOVA | $\eta^2$ or $\omega^2$ | $\eta^2 = SS_\text{effect} / SS_\text{total}$ |
| Chi-square | Cramér's *V* | $V = \sqrt{\chi^2 / (n \times \min(r-1,\, c-1))}$ |
| Correlation | *r* | Pearson or Spearman |
| Regression | $R^2$ / $\beta$ | From model summary |

### 5. Post-hoc Tests (ANOVA)

- Tukey HSD for equal *n* and equal variance
- Games-Howell for unequal *n* or variance
- Apply Bonferroni correction for > 3 planned comparisons
- Report all pairwise comparisons, not just significant ones

### 6. Report Results (APA Style)

```
$t(62.4) = 3.21$, $p = .002$, $d = 0.80$, 95% CI [0.31, 1.28]

$F(2, 117) = 8.34$, $p < .001$, $\eta^2 = .13$, 95% CI [.04, .23]

$\chi^2(3,\, N = 200) = 12.56$, $p = .006$, $V = .25$
```

## Power Analysis

```python
from statsmodels.stats.power import TTestIndPower

analysis = TTestIndPower()
n = analysis.solve_power(effect_size=0.5, alpha=0.05, power=0.80)
print(f"Required n per group: {n:.0f}")
```

## Review Checklist

- [ ] Hypotheses stated before analysis
- [ ] α level pre-specified
- [ ] Assumption checks run and results reported
- [ ] Appropriate test selected given data type and design
- [ ] Effect size computed and reported
- [ ] Confidence intervals provided
- [ ] Post-hoc tests applied where appropriate
- [ ] Results reported in APA format
- [ ] Figures include labelled error bars
