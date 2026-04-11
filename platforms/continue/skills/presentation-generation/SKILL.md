---
name: presentation-generation
description: Creates structured slide decks for academic and technical presentations in Beamer (LaTeX), reveal.js (Quarto), or PowerPoint, with clear visual hierarchy and speaker notes
mcp_servers: []
allowed_tools:
  - Read
  - Write
  - Bash
---

# Presentation Generation

Creates professional, well-structured slide presentations for seminars, defences,
conference talks, and course lectures.

## When to Use

- Preparing a thesis defence or project presentation
- Creating conference or seminar slides from a written report
- Generating course lecture slides from notes or a syllabus
- Producing a progress update deck for a supervisor or team

## Output Formats

| Format | Best for | Toolchain |
|---|---|---|
| **Beamer (LaTeX)** | Academic / conference presentations | `pdflatex` / `latexmk` |
| **Quarto reveal.js** | Interactive HTML slides with code output | `quarto render` |
| **Quarto PowerPoint** | Institutional templates, collaboration | `quarto render --to pptx` |
| **Marp (Markdown)** | Lightweight, version-controllable slides | `marp` CLI |

## Slide Design Principles

1. **One idea per slide** — if a slide needs more than 6 bullet points, split it
2. **Figures over bullets** — replace bullet lists with diagrams wherever possible
3. **Large font** — minimum 18 pt body text; titles ≥ 24 pt
4. **High contrast** — black on white or white on dark; avoid light grey text
5. **Consistent theme** — do not mix more than two font families
6. **Speaker notes** — every slide has notes with what you will say

## Workflow

### 1. Gather Content

Inputs to collect before generating slides:
- Written report, notes, or outline
- Key figures and tables (as image files or code)
- Talk duration and intended audience
- Any required institutional template

### 2. Design the Arc

Every presentation follows a narrative arc:
```
Title slide
├── Problem / Motivation        (1–2 slides)
├── Background / Related Work   (2–3 slides)
├── Methods / Approach          (3–5 slides)
├── Results / Findings          (3–6 slides)
├── Discussion / Implications   (1–2 slides)
└── Conclusion + Future Work    (1 slide)
   Thank You / Questions        (1 slide)
```

Rule of thumb: **1 slide per minute of talk time**.

### 3. Write Declarative Slide Titles

Every slide title should be a complete claim, not a topic label:
- ❌ "Results"
- ✅ "Random forests outperform logistic regression on all metrics"

### 4. Insert Figures and Tables

- Figures should fill ≥ 50% of the slide area
- Tables on slides: maximum 5 columns, 6 rows; larger tables go in appendix
- Always include a clear takeaway label on every figure slide

### 5. Add Speaker Notes

Every slide must have speaker notes (2–4 sentences):
- What is the key message of this slide?
- What transition phrase leads to the next slide?

### 6. Math Notation on Slides

Use **LaTeX dollar notation** for all mathematical expressions:

- **Beamer/LaTeX** — dollar notation is native: `$\hat{\beta}_1 = 0.42$`,
  `$H_0: \mu_1 = \mu_2$`, display with `\[ \]` or `$$...$$`
- **Quarto reveal.js** — MathJax is enabled by default; use `$...$` and `$$...$$`
- **Marp** — enable math with `math: mathjax` in front-matter; same `$...$`/`$$...$$`

Keep equations **large** ($\geq$ 20 pt in the rendered output) and number any
equation that is referred to verbally. Avoid LaTeX in plain PowerPoint — use
Unicode or an image instead.

## Beamer Template Snippet

```latex
\documentclass{beamer}
\usetheme{Madrid}

\title{My Analysis Results}
\author{Your Name}
\date{\today}

\begin{document}

\begin{frame}{Random Forests Outperform Logistic Regression}
  \begin{columns}
    \column{0.5\textwidth}
      \includegraphics[width=\linewidth]{figures/roc_comparison.pdf}
    \column{0.5\textwidth}
      \begin{itemize}
        \item AUC: RF 0.91 vs LR 0.83
        \item Recall: RF 0.87 vs LR 0.79
        \item 5-fold CV, $n = 1200$
      \end{itemize}
  \end{columns}
  \note{Emphasise the AUC gap is statistically significant (p < .001).}
\end{frame}

\end{document}
```

## Quarto reveal.js Template Snippet

```yaml
---
title: "My Analysis Results"
author: "Your Name"
format:
  revealjs:
    theme: simple
    slide-number: true
---

## Random Forests Outperform Logistic Regression

:::: {.columns}
::: {.column width="50%"}
![ROC curves](figures/roc_comparison.png)
:::
::: {.column width="50%"}
- AUC: RF 0.91 vs LR 0.83
- Recall: RF 0.87 vs LR 0.79
- 5-fold CV, n = 1200
:::
::::

::: notes
Emphasise the AUC gap is statistically significant.
:::
```

## Review Checklist

- [ ] Slide count matches talk duration (≈ 1 slide / minute)
- [ ] Every slide has a declarative claim as title
- [ ] No slide has more than 6 bullet points
- [ ] Every figure has a clear takeaway label
- [ ] Speaker notes present on every slide
- [ ] Font size ≥ 18 pt throughout
- [ ] Consistent colour scheme
- [ ] Title slide includes name, date, and affiliation
- [ ] Thank You / Questions slide at the end
