---
name: obsidian-vault-management
description: Navigates, creates, links, and organises notes in an Obsidian vault — including daily notes, MOCs, tag management, dataview queries, and knowledge-graph maintenance
mcp_servers:
  - obsidian
allowed_tools:
  - Read
  - Write
  - obsidian_*
---

# Obsidian Vault Management

Provides structured workflows for maintaining and growing an Obsidian vault as a
personal knowledge base for academic projects, literature notes, and study materials.

## When to Use

- Capturing lecture notes or paper summaries into the vault
- Creating or updating Map-of-Content (MOC) index notes
- Linking new notes to existing concepts
- Running Dataview queries to survey vault contents
- Managing tags, aliases, and YAML front-matter
- Organising the vault folder structure for a new project or course
- Generating daily/weekly notes for academic journaling

## Vault Conventions

### Recommended Folder Structure

```
vault/
├── 00-inbox/          # Unprocessed captures; reviewed daily
├── 10-projects/       # One folder per active project or course
│   └── stats-msc/
│       ├── _MOC.md    # Map of Content index
│       ├── lectures/
│       ├── papers/
│       └── data/
├── 20-areas/          # Evergreen topic notes (concepts, methods)
├── 30-resources/      # Reference material (textbooks, datasets)
├── 40-archive/        # Completed projects
└── 99-templates/      # Note templates
```

### YAML Front-matter Template

```yaml
---
title: "Note Title"
date: YYYY-MM-DD
tags:
  - topic/statistics
  - type/lecture-note
aliases:
  - Alternative Title
status: draft           # draft | in-progress | complete
related:
  - "[[Related Note]]"
---
```

### Link Conventions

- Use `[[WikiLinks]]` for internal links
- Tag format: `#category/subcategory` (e.g., `#method/regression`)
- Block references (`^blockid`) for stable paragraph-level links
- `![[note]]` embeds only when inline display is truly needed

## Workflows

### Capturing a New Note

1. Create in `00-inbox/` with the YAML template
2. Write the content (summary, key points, questions)
3. Add links to related existing notes
4. Tag with `status: draft`
5. Schedule for processing

### Processing the Inbox

1. Open each note in `00-inbox/`
2. Determine its permanent home (project, area, or resource)
3. Add back-links from related notes
4. Update the relevant MOC (`_MOC.md`)
5. Change `status` to `in-progress` or `complete`
6. Move note to destination folder

### Updating a Map of Content (MOC)

```markdown
---
title: "MOC: Bayesian Statistics"
tags: [type/moc, topic/bayesian]
---

# Bayesian Statistics — Map of Content

## Foundations
- [[Bayes Theorem]]
- [[Prior Distributions]]

## Methods
- [[MCMC Sampling]]
- [[Variational Inference]]
```

### Dataview Queries

```dataview
TABLE date, status, tags
FROM "10-projects/stats-msc/lectures"
WHERE status != "complete"
SORT date DESC
```

```dataview
LIST
FROM #topic/regression
SORT file.mtime DESC
LIMIT 10
```

### Daily Note Template

```markdown
---
title: "Daily Note {{date}}"
date: {{date}}
tags: [type/daily]
---

## Today's Plan
- [ ] 

## Notes

## Links Created
-
```

## Review Checklist

- [ ] Inbox is empty (all captures processed)
- [ ] Every note has YAML front-matter with title, date, tags, status
- [ ] All new notes linked from at least one MOC or related note
- [ ] Orphan notes audited and linked or archived
- [ ] Tags are consistent (no duplicates from typos)
- [ ] Project folders have an up-to-date `_MOC.md`
