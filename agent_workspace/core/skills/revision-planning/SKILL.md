---
name: revision-planning
description: Creates structured, evidence-based revision schedules from syllabi, exam dates, and self-assessed weaknesses — using spaced repetition, interleaving, and retrieval practice principles
allowed_tools:
  - Read
  - Write
---

# Revision Planning Skill

## Purpose

Build realistic, evidence-based revision plans that maximise long-term retention
before exams — grounded in cognitive psychology research on learning.

## Evidence-Based Techniques

| Technique | Why it works | How to schedule |
|---|---|---|
| **Spaced repetition** | Fighting the forgetting curve | Revisit material at increasing intervals: 1 day, 3 days, 1 week, 2 weeks |
| **Retrieval practice** | Testing > re-reading | Dedicate ≥ 40% of session time to active recall (flashcards, practice problems, self-explanation) |
| **Interleaving** | Prevents over-specialisation | Mix topics within a session rather than blocking by topic |
| **Elaborative interrogation** | Deep encoding | Ask "why is this true?" for every concept |
| **Concrete examples** | Abstract → concrete | Generate personal examples for every abstract concept |

## Workflow

### 1. Gather Inputs
- Syllabus / topic list
- Exam date(s)
- Self-assessed confidence per topic (0–4 scale)
- Available study hours per day

### 2. Topic Prioritisation

Score each topic:

$$\text{Priority} = \frac{\text{Exam weight} \times (4 - \text{Confidence})}{1 + \text{Days until exam}}$$

Higher score → schedule earlier and more frequently.

### 3. Build the Schedule

```
Week 1 (14 days before exam):
  Mon: Topic A (1.5 h) + Topic B intro (0.5 h)
  Tue: Topic C (1 h) + Topic A retrieval practice (0.5 h)
  ...

Week 2 (7 days before exam):
  Mon: Mixed practice — A + B + C interleaved (2 h)
  Tue: Past paper — timed (2 h) + review errors (1 h)
  ...
```

### 4. Embed Checkpoints

- **Daily**: 10-min retrieval quiz at start of each session
- **Weekly**: Full topic summary from memory (brain-dump)
- **Pre-exam**: Complete past paper under timed conditions

## Output Format

Generate a Markdown revision schedule that can be pasted into Obsidian or a calendar:

```markdown
## Revision Plan: Statistics Exam (2026-05-15)

### Priority Ranking
| # | Topic | Confidence | Sessions |
|---|---|---|---|
| 1 | Bayesian inference | ⭐⭐ (low) | 6 |
| 2 | Hypothesis testing | ⭐⭐⭐ | 4 |
| 3 | Regression | ⭐⭐⭐⭐ | 2 |

### Daily Schedule

#### Week of 2026-05-01
- **Mon**: Bayesian inference — review notes (1h) + 20 flashcards (0.5h)
- **Tue**: Hypothesis testing — retrieval quiz (0.5h) + practice problems (1h)
...
```

## Adaptive Re-planning

At each weekly checkpoint, re-score confidence and regenerate the plan:
1. Topics where confidence improved → reduce session count
2. Topics where quiz scores < 60% → increase session count + add interleaving
3. Final week → switch entirely to past papers and error review

## Integration

- Export daily tasks to Obsidian daily note via the `obsidian-capture` command
- Generate flashcard decks for low-confidence topics via the `flashcard-generation` skill
- Track spaced repetition intervals in Anki (auto-scheduled by the algorithm)
