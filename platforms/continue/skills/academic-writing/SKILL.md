---
name: academic-writing
description: Drafts and refines academic writing — abstracts, introductions, methods, results, and discussion sections — following discipline norms with proper citations and APA/IEEE style
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Academic Writing

Guides the drafting, revision, and polishing of academic writing for
statistics, data science, and quantitative social science projects.

## When to Use

- Writing thesis chapters or paper sections
- Drafting an abstract from a completed analysis
- Converting bullet-point results into flowing prose
- Revising a draft for clarity, concision, and style
- Checking citation formatting

## Writing Order

Write sections in this order (not the order they appear in the paper):

1. **Methods** — most concrete; write what you did
2. **Results** — describe what you found, guided by methods
3. **Discussion** — interpret and contextualise results
4. **Introduction** — frame the problem; now you know what you're introducing
5. **Abstract** — last; summarise the whole paper in ≤ 250 words

## Section-by-Section Guidelines

### Abstract

Structure (for empirical papers):
1. Background / motivation (1 sentence)
2. Research question / objective (1 sentence)
3. Methods (2 sentences: data + approach)
4. Results (2 sentences: key findings with numbers)
5. Conclusion / implications (1 sentence)

```
Background. [One sentence motivating the problem.]
Objective. We investigated [question] using [data].
Methods. [N] [subjects/observations] were [analysed/randomised/surveyed]
using [method]. [Additional method detail.]
Results. [Main finding 1] (stat, p-value). [Main finding 2].
Conclusion. [Takeaway and/or implication].
```

### Introduction

1. Hook: why does this problem matter?
2. Gap: what don't we know?
3. Contribution: what does this paper add?
4. Roadmap: "Section 2 describes…"

### Methods

- **Data**: source, collection method, n, inclusion/exclusion, ethics approval
- **Variables**: operationalise each construct; specify units
- **Statistical analysis**: model, software (name + version), α level, correction method
- Write in past tense; passive voice is acceptable

```
Data were collected from [source] between [date] and [date] (N = [n]).
[Outcome] was operationalised as [definition]. [Predictor] was measured
using [instrument] (range: 0–100; α = .87).

All analyses were conducted in R 4.3.1 (R Core Team, 2023) using the
lme4 package (Bates et al., 2015). Statistical significance was set
at α = .05; no corrections for multiple comparisons were applied
because only one primary hypothesis was tested.
```

### Results

- Lead with the research question, then the answer
- Report test statistics first, then interpretation
- Use past tense
- Every number needs a unit or descriptor

```
[Research question restatement]. [Main finding with statistics].
[Secondary finding]. Table 1 presents descriptive statistics;
Figure 2 displays [what the figure shows].
```

### Discussion

Structure:
1. Restate the main finding (1 paragraph, no statistics)
2. Relate to prior work: consistent with? contradicts?
3. Mechanisms / explanations
4. Limitations (be honest; at least 3)
5. Future directions (at least 2 concrete suggestions)
6. Conclusion paragraph

## Style Guidelines

| Rule | Example |
|---|---|
| Numbers < 10 spelled out | "three variables", not "3 variables" |
| Numbers with units use digits | "3 km", "5 participants" |
| p-values three decimals | $p = .023$ (not p = 0.023) |
| Italicise statistics in prose | *t*, *F*, *p*, *M*, *SD* |
| LaTeX dollar notation for math | `$t(48) = 3.21$`, `$p < .001$`, `$\eta^2 = .13$` |
| Avoid "significant" for non-statistical meaning | "substantial" / "notable" |
| Oxford comma | "mean, SD, and range" |

## Math Notation

Use LaTeX dollar notation for **all** mathematical and statistical expressions:

- **Inline**: `$...$` — e.g., `$\bar{x} = 42.5$`, `$H_0: \mu_1 = \mu_2$`,
  `$t(48) = 3.21,\; p = .002$`, `$\beta_1 = 0.42,\; 95\%~\text{CI}~[0.28, 0.56]$`
- **Display**: `$$...$$` — for equations that are referenced in the text or need
  visual prominence, e.g.:

$$\bar{x} \pm z_{\alpha/2} \cdot \frac{\sigma}{\sqrt{n}}$$

This applies equally to Markdown, Quarto, and LaTeX output formats.

## Revision Checklist

- [ ] Each paragraph has one clear main claim
- [ ] First sentence of each paragraph states the claim
- [ ] Passive voice used sparingly (< 30% of verbs)
- [ ] No filler phrases ("it is worth noting that…")
- [ ] All statistics formatted correctly
- [ ] All claims supported by citation or result
- [ ] Methods written in past tense
- [ ] Word count within limit
- [ ] Abstract follows structure above
- [ ] Spell-check run
