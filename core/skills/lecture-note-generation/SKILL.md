---
name: lecture-note-generation
description: Generates structured, pedagogically sound lecture notes from syllabi, slides, textbook excerpts, or spoken transcripts, with learning objectives, worked examples, and self-test questions
mcp_servers: []
allowed_tools:
  - Read
  - Write
  - Bash
---

# Lecture Note Generation

Creates well-structured, self-contained lecture notes from raw input materials
(slides, transcripts, textbook chapters, or topic descriptions).

## When to Use

- Converting slide decks into readable lecture notes for self-study
- Generating notes from a course syllabus or reading list
- Creating a revision guide from raw materials
- Producing Obsidian-compatible topic notes from a lecture transcript
- Summarising a textbook chapter as concise study notes

## Output Formats

- **Markdown / Obsidian** — for personal knowledge management
- **Quarto (`.qmd`)** — for rendered PDF or HTML handouts
- **LaTeX** — for typeset handouts
- **Plain text** — for Anki flashcard import (`question::answer` format)

## Workflow

### 1. Identify Inputs and Structure

Parse the source material to identify:
- Topic and subtopics
- Key definitions and theorems
- Worked examples
- Common misconceptions

### 2. Write Learning Objectives

Open every set of lecture notes with explicit, measurable objectives using
Bloom's taxonomy verbs:

```markdown
## Learning Objectives

After this lecture, you will be able to:
1. **Define** the central limit theorem and state its conditions.
2. **Explain** why normality of the sampling distribution arises as n → ∞.
3. **Calculate** standard errors for sample means and proportions.
4. **Apply** the CLT to construct confidence intervals.
5. **Evaluate** when the CLT approximation is adequate.
```

### 3. Use the Standard Note Structure

```
# Lecture N: Topic Title

## Learning Objectives

## 1. Background and Motivation

## 2. Core Concepts and Definitions

## 3. Key Results and Theorems

## 4. Worked Examples

## 5. Common Pitfalls and Misconceptions

## 6. Summary

## 7. Self-Test Questions

## 8. Further Reading
```

### 4. Write Formal Definitions

```markdown
> **Definition (Unbiasedness).** An estimator θ̂ is *unbiased* for θ if
> E[θ̂] = θ for all values of θ in the parameter space.
```

### 5. Write Worked Examples

```markdown
**Example 1.** A sample of n = 36 has x̄ = 42.5 and σ = 12.
Construct a 95% confidence interval for μ.

**Solution.**
1. SE = σ/√n = 12/6 = 2
2. Margin of error = 1.96 × 2 = 3.92
3. CI: **(38.58, 46.42)**

**Interpretation:** We are 95% confident that μ lies between 38.58 and 46.42.
```

### 6. Write Self-Test Questions

Include a mix of Bloom's levels:
- **Recall** (L1): "Define the p-value."
- **Comprehension** (L2): "Explain the difference between Type I and Type II errors."
- **Application** (L3): "Perform a t-test at α = 0.05 for the following data."
- **Analysis** (L4): "Which assumption is violated in this residual plot?"
- **Evaluation** (L5): "Which test would you choose and why?"

### 7. Obsidian Front-matter

When generating for Obsidian:

```yaml
---
title: "Lecture 5: Central Limit Theorem"
date: 2026-04-11
tags:
  - topic/probability
  - type/lecture-note
  - course/stats-foundations
aliases:
  - CLT
status: complete
---
```

## Review Checklist

- [ ] Learning objectives present and measurable
- [ ] Every key term defined formally
- [ ] At least 2 worked examples per major concept
- [ ] Common pitfalls section included
- [ ] Bullet-point summary present
- [ ] Self-test questions at multiple Bloom levels
- [ ] Further reading references provided
- [ ] Mathematical notation consistent
- [ ] Obsidian front-matter added if Markdown output
