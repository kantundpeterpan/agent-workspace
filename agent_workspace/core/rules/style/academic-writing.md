# Rule: Academic Writing Standards

Guidelines for writing clear, rigorous, and well-structured academic documents
(reports, theses, papers, lecture notes, presentations).

## Structure

**Every written artefact must have:**
- A descriptive title, author, and date in the header or YAML front-matter
- An abstract or executive summary (reports/papers) or learning objectives (lecture notes)
- Numbered sections with meaningful headings
- A references section with full citations

**Section order for empirical reports:**
1. Introduction (motivation, research question, contributions)
2. Background / Related Work
3. Methods (data, models, procedures)
4. Results (tables, figures, descriptive text)
5. Discussion (interpretation, limitations)
6. Conclusion
7. References / Bibliography

## Language

- Use plain, precise language; avoid jargon without definition
- Define all mathematical notation on first use
- Prefer active constructions where permitted by discipline norms
- Avoid filler phrases ("it can be seen that", "it is worth noting that")
- Numbers below ten are spelled out unless in a formula or table

## Mathematical Notation

- All variables must be italicised: *n*, *p*, *β*
- Vectors and matrices in bold: **X**, **β**
- Use `\hat{}` for estimates: *β̂*
- Equations that are referenced must be numbered
- Inline maths only for simple expressions; display maths for anything complex

## Tables and Figures

- Every table and figure must have a numbered caption
- Tables: title above the table; note below (if any)
- Figures: caption below the figure
- Reference every table/figure in the text before it appears
- Provide alt-text descriptions for accessibility

## Citations

- Use consistent citation style throughout (APA, IEEE, or journal-specified)
- All claims that are not common knowledge must be cited
- Use `[@key]` in Quarto/Markdown, `\cite{key}` in LaTeX
- DOIs must be resolvable

## Review Checklist

- [ ] Title, author, date present
- [ ] Abstract / learning objectives present
- [ ] All sections numbered and labelled
- [ ] All notation defined on first use
- [ ] All figures and tables captioned and referenced
- [ ] Citation style consistent throughout
- [ ] Spell-check and grammar-check run
- [ ] References section complete
