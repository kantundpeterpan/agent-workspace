---
name: flashcard-generation
description: Creates high-quality spaced-repetition flashcards (Anki-compatible) from lecture notes, textbook passages, or concept lists — applying cognitive science best practices for long-term retention
custom_tools:
  - anki-exporter
allowed_tools:
  - Read
  - Write
---

# Flashcard Generation Skill

## Purpose

Transform source material (notes, slides, textbooks, papers) into effective
spaced-repetition flashcards ready to import into Anki or similar systems.

## Cognitive Science Principles

### 1. Minimum Information Principle
Each card tests **exactly one atomic fact or concept**.
- ❌ "Describe the central limit theorem and its conditions."
- ✅ Front: "What does the Central Limit Theorem state?"  
  Back: "As $n \to \infty$, the sampling distribution of $\bar{x}$ approaches $\mathcal{N}(\mu, \sigma^2/n)$, regardless of the population distribution."

### 2. Active Recall Formulation
Cards should require retrieval, not recognition.
- ❌ "True/False: The p-value is the probability that H₀ is true."
- ✅ Front: "What is a p-value?"  
  Back: "The probability of observing a result at least as extreme as the data, **assuming $H_0$ is true**. It is *not* the probability that $H_0$ is true."

### 3. Card Types

| Type | Use case | Example |
|---|---|---|
| **Basic** | Single fact | Definition, formula |
| **Cloze deletion** | Fill-in-the-blank | `{{c1::brms}} uses Stan for Bayesian mixed models in R` |
| **Reverse** | Both directions | Term↔definition |

### 4. Math in Cards

Use LaTeX dollar notation for all mathematical content:
- Inline: `$p < .05$`, `$\hat{\beta} = 0.43$`, `$n \to \infty$`
- Display: `$$\bar{x} \sim \mathcal{N}\!\left(\mu, \frac{\sigma^2}{n}\right)$$`

Anki renders MathJax; use `[latex]...[/latex]` tags only for legacy decks.

## Workflow

1. **Parse source** — identify key terms, definitions, formulas, processes, examples
2. **Draft cards** — one card per atomic concept; vary types (Basic, Cloze, Reverse)
3. **Tag cards** — by topic, difficulty level, and source chapter
4. **Export** — use the `anki-exporter` tool to produce a `.txt` import file

## Card Quality Checklist

- [ ] Each card tests exactly ONE concept
- [ ] Front is a clear, unambiguous question or cue
- [ ] Back contains the complete answer (no "look it up")
- [ ] Math rendered with `$...$` / `$$...$$`
- [ ] Tags assigned (topic + difficulty + source)
- [ ] No trivial cards ("What year was X published?")

## Export Format (plain-text import)

```
#deck:Statistics — Hypothesis Testing
#notetype:Basic
What is the definition of a Type I error?	Rejecting $H_0$ when $H_0$ is actually true; false positive. Its probability is $\alpha$.	stats hypothesis-testing
What does $\beta$ represent in hypothesis testing?	The probability of a **Type II error**: failing to reject $H_0$ when $H_1$ is true.	stats hypothesis-testing
```

## Example Cards: Bayesian Inference

| Front | Back | Tags |
|---|---|---|
| What is the prior predictive distribution? | $$p(\tilde{y}) = \int p(\tilde{y}\mid\theta)\,p(\theta)\,d\theta$$ — the distribution of new data implied by the prior alone, before seeing any data. | bayesian prior |
| When is $\hat{R} > 1.01$ a problem? | It signals lack of convergence between MCMC chains. Re-run with more warm-up iterations, reparametrize, or simplify the model. | bayesian mcmc |
| Cloze: The 94% HDI contains the {{c1::most credible}} 94% of the posterior. | | bayesian hdi |

## Integration with Obsidian

If an Obsidian vault is available, flashcards can be embedded directly in notes
using the `#flashcard` tag convention and synced via the Obsidian-to-Anki plugin.
