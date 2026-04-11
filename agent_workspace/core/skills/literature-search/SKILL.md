---
name: literature-search
description: Searches and synthesises academic literature for a given research topic, producing annotated bibliographies, gap analyses, and BibTeX exports
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# Literature Search

Provides a structured workflow for discovering, evaluating, and synthesising
academic literature relevant to a research question.

## When to Use

- Starting a new research topic and mapping the field
- Writing a related-work or background section
- Identifying research gaps for thesis ideation
- Building a reference library for a project

## Workflow

### 1. Define the Search Strategy

Before searching, specify:
- **Primary keywords** (2–4 core terms)
- **Synonyms and variants** (e.g., "machine learning" / "statistical learning")
- **Time range** (e.g., 2018–present)
- **Inclusion criteria** (peer-reviewed, English, empirical)
- **Exclusion criteria** (editorials, preprints without peer review)

### 2. Search Sources

Search these sources systematically:

| Source | Best for |
|---|---|
| Google Scholar | Broad coverage, citation counts |
| arXiv (cs.LG, stat.ML, stat.ME) | Latest ML/stats preprints |
| Semantic Scholar | Citation graph, related papers |
| PubMed | Medical/epidemiological stats |
| ACM Digital Library | CS/ML conference papers |
| JSTOR / Web of Science | Classic statistics |

Using Bash to query arXiv API:
```bash
curl "https://export.arxiv.org/api/query?search_query=ti:causal+inference+AND+ti:machine+learning&max_results=20&sortBy=relevance" \
  | python3 -c "
import sys, re
content = sys.stdin.read()
titles = re.findall(r'<title>(.*?)</title>', content)
ids = re.findall(r'<id>(http://arxiv.org/abs/[^<]+)</id>', content)
for t, i in zip(titles[1:], ids):
    print(f'{i}  {t}')
"
```

### 3. Screen and Select

- **Title screen**: read titles, discard obviously irrelevant
- **Abstract screen**: read abstracts of remaining papers
- **Full-text screen**: read selected papers fully
- Record decisions in a screening table (include/exclude + reason)

### 4. Extract Information

For each selected paper, extract:
- Citation key (AuthorYEARkeyword, e.g., `pearl2009causality`)
- Title, authors, venue, year
- Research question
- Methods used
- Key findings
- Limitations
- Relevance to your question (1–3 sentences)

### 5. Synthesise

Group papers by theme and write a narrative synthesis:
- What do we know? (established findings)
- What is contested? (conflicting results)
- What is missing? (gaps your work addresses)

### 6. Export to BibTeX

```python
# Generate BibTeX from DOI using CrossRef API
import requests

def doi_to_bibtex(doi: str) -> str:
    url = f"https://doi.org/{doi}"
    headers = {"Accept": "application/x-bibtex"}
    r = requests.get(url, headers=headers, allow_redirects=True)
    return r.text

# Example
print(doi_to_bibtex("10.1145/3583780.3614923"))
```

## PRISMA Flow Diagram

Document your search in PRISMA format:
```
Records identified: N
    ↓ (after deduplication)
Records screened:   N
    ↓ (after title/abstract screen)
Full-text assessed: N
    ↓ (after full-text screen)
Included:           N
```

## Review Checklist

- [ ] Search strategy documented (keywords, databases, date range)
- [ ] Inclusion/exclusion criteria defined before screening
- [ ] PRISMA flow documented
- [ ] Each paper has citation key, extraction notes, and relevance note
- [ ] Synthesis identifies gaps and contested findings
- [ ] `.bib` file exported and formatted
- [ ] Citation keys follow consistent naming convention
