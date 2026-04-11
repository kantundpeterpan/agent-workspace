---
name: concept-explanation
description: Explains complex scientific, mathematical, and statistical concepts at multiple levels of detail — from intuitive analogy to formal definition — using the Feynman technique and progressive elaboration
allowed_tools:
  - Read
  - Write
---

# Concept Explanation Skill

## Purpose

Take any concept from statistics, mathematics, data science, or related disciplines
and explain it clearly at the right level of abstraction for the audience.

## The Feynman Technique (4 Steps)

1. **Name the concept** — identify exactly what is to be explained
2. **Explain as if to a novice** — plain language, no jargon, intuitive analogies
3. **Identify gaps** — where did the explanation break down or become vague?
4. **Simplify and use analogies** — refine until the explanation is gap-free

## Explanation Levels

Always offer explanations at multiple levels:

| Level | Audience | Style |
|---|---|---|
| **Intuitive** | Non-specialist | Analogy, everyday language |
| **Conceptual** | First-year student | Definitions, informal maths |
| **Formal** | Practitioner | Precise notation, proofs |
| **Computational** | Coder | Code example in Python or R |

## Worked Example: p-value

### Level 1 — Intuitive
Imagine you flip a coin 10 times and get 9 heads. You wonder: "Could this be a fair coin
by chance?" The p-value is the probability of getting a result **as extreme or more extreme**
than 9 heads, *if the coin really were fair*. A very small p-value means your result would
be very surprising under the fair-coin assumption.

### Level 2 — Conceptual
The p-value is computed under the null hypothesis $H_0$. It answers:
"If $H_0$ were true, how probable is a test statistic at least as large as the one observed?"
A small p-value (e.g., $p < .05$) is used as evidence against $H_0$, but it does **not**
tell you the probability that $H_0$ is true.

### Level 3 — Formal
Let $T$ be a test statistic with distribution $F$ under $H_0$. The p-value is:

$$p = P(T \geq t_{\text{obs}} \mid H_0) = 1 - F(t_{\text{obs}})$$

for a one-sided right-tail test.  
For a two-sided test: $p = 2 \cdot P(T \geq |t_{\text{obs}}| \mid H_0)$.

### Level 4 — Computational

```python
from scipy import stats
import numpy as np

# Two-sample t-test
group_a = [5.1, 5.8, 4.9, 6.2, 5.5]
group_b = [4.0, 4.3, 3.8, 4.6, 4.1]
t_stat, p_value = stats.ttest_ind(group_a, group_b)
print(f"t = {t_stat:.3f}, p = {p_value:.4f}")
```

```r
# R equivalent
group_a <- c(5.1, 5.8, 4.9, 6.2, 5.5)
group_b <- c(4.0, 4.3, 3.8, 4.6, 4.1)
t.test(group_a, group_b)
```

## Common Misconceptions to Address

Always proactively correct these mistakes:

| Misconception | Correct understanding |
|---|---|
| "p < .05 means the result is important" | Statistical significance ≠ practical significance; always report effect sizes |
| "The p-value is the probability H₀ is true" | It is $P(\text{data} \mid H_0)$, not $P(H_0 \mid \text{data})$ |
| "$R^2 = 0.8$ means the model explains 80% of the truth" | It explains 80% of variance in the **sample** |
| "Correlation implies causation" | Correlation is a necessary but not sufficient condition for causation |

## Math Notation

Use LaTeX dollar notation for all mathematical expressions:
- Inline: `$H_0$`, `$p < .05$`, `$\alpha$`, `$\beta$`, `$\hat{y}$`
- Display blocks for key formulas and derivations: `$$...$$`
- Number equations that are referenced in the text (e.g., Equation (1))

## Explanation Templates

### For a Statistical Test
1. What question does it answer?
2. What are the inputs (data requirements, assumptions)?
3. What does the test statistic measure?
4. How do you interpret the result?
5. What can go wrong (assumption violations)?

### For a Mathematical Concept
1. Intuitive motivation (why does this concept exist?)
2. Informal definition
3. Formal definition with notation
4. Simple worked example
5. Common pitfalls and generalisations

### For an Algorithm or Method
1. What problem does it solve?
2. High-level idea (pseudocode or diagram)
3. Step-by-step walkthrough on a small example
4. Complexity and limitations
5. When to use it vs. alternatives
