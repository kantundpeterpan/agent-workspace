# Rule: Statistical Integrity

Standards for honest, rigorous, and transparent statistical practice that
prevents inadvertent or deliberate misrepresentation of results.

## Pre-registration and Hypothesis Registration

- State hypotheses, analysis plan, and stopping rule **before** collecting or
  examining data; use OSF, AsPredicted, or a datestamped document
- Distinguish confirmatory analyses (pre-registered) from exploratory analyses
  (must be labelled as such)
- Never re-label a failed confirmatory test as "exploratory" post-hoc

## Prohibited Practices

**P-hacking / Fishing:**
- Do not run multiple tests and report only significant ones without correction
- Do not try multiple dependent-variable operationalisations and report only the significant one
- Do not collect data until p < .05, then stop — pre-specify n

**HARKing (Hypothesising After Results are Known):**
- Do not present a post-hoc hypothesis as if it were pre-specified
- Label all post-hoc analyses explicitly: "This analysis was exploratory"

**Selective Reporting:**
- Report all tested hypotheses, not just significant ones
- Report effect sizes for non-significant results too
- If a model was one of several tested, report model comparison

**Post-hoc Power Analysis:**
- Never compute "observed power" from the same data used to test the hypothesis
- Power analysis belongs before data collection, not after

## Multiple Comparisons

- Apply Bonferroni, Benjamini-Hochberg (FDR), or equivalent correction when
  testing more than one hypothesis
- State correction method and adjusted α level explicitly
- Do not use "marginal significance" (p < .10) as a positive result

## Outlier Handling

- Define outlier detection rule before seeing data
- Document which observations were excluded and why
- Report results with and without exclusions if the rule was applied after inspection

## Reporting Language

```
# PROHIBITED
"marginally significant" (p = .07)
"trending towards significance"
"failed to reach significance"    ← suggests the test "tried" to be significant
"borderline significant"

# CORRECT
"not statistically significant, p = .07"
"insufficient evidence to reject H₀, p = .07"
```

## Data and Code Sharing

- Publish analysis code and (where ethically permissible) data
- Cite the specific version of analysis code used to produce results
- Provide a README that allows another researcher to reproduce all reported analyses

## Review Checklist

- [ ] Hypotheses stated before data analysis
- [ ] Confirmatory vs exploratory analyses clearly labelled
- [ ] Multiple comparison correction applied and stated
- [ ] All tested hypotheses reported (not just significant ones)
- [ ] No "marginally significant" language
- [ ] Outlier removal rule defined before inspection
- [ ] Post-hoc exploratory findings labelled as such
- [ ] No post-hoc power analysis
- [ ] Effect sizes reported for all primary tests
- [ ] Code and data sharing plan in place
