# Rule: Statistical Reporting Standards

Conventions for reporting statistical results in academic and applied contexts,
following APA 7th edition and general best practices.

## Hypothesis Tests

**Always report:**
- Test statistic with its symbol and degrees of freedom: *t*(48) = 3.21
- Exact *p*-value to three decimal places (or *p* < .001 when below threshold)
- Effect size with confidence interval: *d* = 0.46, 95% CI [0.12, 0.80]
- Sample size(s)

**Format examples:**
```
t(48) = 3.21, p = .002, d = 0.46, 95% CI [0.12, 0.80]
F(2, 147) = 8.34, p < .001, η² = .10, 95% CI [.03, .18]
χ²(3, N = 200) = 12.56, p = .006, V = .25
r(98) = .42, p < .001, 95% CI [.25, .57]
```

## Regression

- Report model fit: *R*² (adjusted *R*² for OLS), AIC/BIC for model comparison
- Report each coefficient: estimate, SE, standardised coefficient (β), *t*, *p*
- Indicate reference level for categorical predictors
- Report confidence intervals for all coefficients
- Check and report assumption diagnostics (normality of residuals, homoscedasticity, VIF)

## Descriptive Statistics

- Report mean and SD for continuous variables: *M* = 4.32, *SD* = 1.07
- Report median and IQR for skewed distributions
- Report percentages for categorical variables with frequencies: 42% (n = 84)
- Specify the unit for every measured quantity

## Bayesian Reports

- Report posterior mean (or median) and 94% credible interval
- Report R-hat (< 1.01) and effective sample size as convergence evidence
- Describe prior choices and sensitivity analysis

## Figures

- Error bars must be labelled (SE, SD, or 95% CI)
- Axes must have units
- Use colour-blind-safe palettes
- Caption must state what is shown (e.g., "Error bars represent 95% CI")

## Prohibited Patterns

- Never report only "*p* < .05" without the test statistic
- Never use "marginally significant" or "trending towards significance"
- Never use stars (*, **, ***) as the only indicator of significance
- Never omit effect sizes for any primary result
- Never run post-hoc power analysis on observed data

## Review Checklist

- [ ] Test statistic, df, and p-value reported for every test
- [ ] Effect size + CI reported for every primary result
- [ ] Sample sizes stated
- [ ] Descriptive stats (mean/SD or median/IQR) reported
- [ ] Assumption checks documented
- [ ] No "trending towards significance" language
- [ ] Units on all measures
- [ ] Figures have labelled error bars and captioned axes
