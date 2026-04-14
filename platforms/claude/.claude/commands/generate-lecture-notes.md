---
description: "Generate structured lecture notes from a topic outline, slides, or raw\
  \ text \u2014 with definitions, examples, and self-test questions"
argument-hint: $ARGUMENTS
---

Generate comprehensive lecture notes for the following topic or content.

Structure:
1. **Learning Objectives** — 3–5 measurable outcomes (Bloom's taxonomy)
2. **Key Concepts** — term, formal definition, intuitive explanation, LaTeX equation where relevant
3. **Worked Examples** — step-by-step with annotated code (Python and/or R)
4. **Common Pitfalls** — misconceptions and how to avoid them
5. **Self-Test Questions** — at least 5 questions at mixed Bloom levels (recall → application → synthesis)
6. **Further Reading** — 3–5 references with DOI where possible

Use LaTeX dollar notation for all math: `$\mu$`, `$\sigma^2$`, `$$y_i \sim \mathcal{N}(\mu_i, \sigma^2)$$`

Topic / content: $ARGUMENTS
