---
name: report-writing
description: Drafts, structures, and polishes academic and technical reports in LaTeX, Quarto, or Markdown, following discipline-specific conventions
mcp_servers: []
allowed_tools:
  - Read
  - Write
  - Bash
---

# Report Writing

Produces well-structured academic and technical reports — from outline to final
polished document — in LaTeX, Quarto (`.qmd`), or plain Markdown.

## When to Use

- Writing a statistics or data science project report
- Producing a thesis chapter or section
- Creating a reproducible analysis report with embedded code
- Preparing a technical deliverable for a course or supervisor
- Generating an executive summary from analysis results

## Document Formats

| Format | Best for | Toolchain |
|---|---|---|
| **Quarto (`.qmd`)** | Reproducible reports with R/Python code | `quarto render` |
| **LaTeX** | Formal papers, thesis, journal submission | `pdflatex` / `latexmk` |
| **Markdown + Pandoc** | Quick reports, README-style | `pandoc` |
| **Jupyter Notebook** | Interactive exploration write-up | `nbconvert` |

## Workflow

### 1. Clarify Requirements

Before drafting, establish:
- Target audience (supervisor, journal, general reader)
- Required citation style (APA, IEEE, custom `.bib`)
- Output format and page/word limit
- Whether code output should be embedded or in an appendix

### 2. Build the Outline

Create a hierarchical section outline:
```
1. Introduction
2. Background
3. Methods
   3.1 Data
   3.2 Statistical Model
   3.3 Evaluation
4. Results
   4.1 Descriptive Statistics
   4.2 Main Findings
5. Discussion
6. Conclusion
7. References
```

### 3. Draft Each Section

Write sections in this recommended order:
1. **Methods** — most concrete; grounds subsequent writing
2. **Results** — guided by methods; describe tables/figures
3. **Discussion** — interpret results
4. **Introduction** — written last so you know what you're introducing
5. **Abstract** — written very last; summarises everything

### 4. Integrate Tables and Figures

- Insert tables as proper LaTeX `\begin{table}` or Quarto code blocks
- Reference every table/figure in text before it appears
- Caption tables above, figures below
- Include units in column headers and axis labels

### 5. Manage References

- Maintain a `.bib` file with consistent keys (e.g., `smith2023bayesian`)
- Use `\cite{}` (LaTeX) or `[@key]` (Quarto/Pandoc)
- Run spell-check after inserting all citations
- Verify every reference appears in the bibliography

### 6. Revise and Polish

- Read aloud to catch awkward phrasing
- Ensure each paragraph has one main claim
- Check that all notation is defined
- Run `aspell` or `hunspell` for spell-check
- Check consistency of terminology throughout

## LaTeX Template Snippet

```latex
\usepackage{booktabs}
\begin{table}[htbp]
  \centering
  \caption{Descriptive statistics for the study variables.}
  \begin{tabular}{lrrrr}
    \toprule
    Variable & $n$ & $M$ & $SD$ & Range \\
    \midrule
    Age      & 120 & 24.3 & 3.1 & 18--42 \\
    Score    & 120 & 72.4 & 11.2 & 35--98 \\
    \bottomrule
  \end{tabular}
  \label{tab:descriptives}
\end{table}
```

## Quarto Front-matter Template

```yaml
---
title: "Analysis Report"
author: "Your Name"
date: today
format:
  pdf:
    toc: true
    number-sections: true
  html:
    toc: true
bibliography: references.bib
---
```

## Review Checklist

- [ ] All sections present and numbered
- [ ] Abstract ≤ 250 words with problem, method, finding, conclusion
- [ ] All figures and tables captioned and cross-referenced
- [ ] All statistical results reported with test statistic, df, *p*, effect size
- [ ] Citation style consistent throughout
- [ ] Bibliography complete and formatted
- [ ] Spelling and grammar checked
- [ ] Page/word limit respected
