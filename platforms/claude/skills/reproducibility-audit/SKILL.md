---
name: reproducibility-audit
description: Audits a project for reproducibility issues — lockfiles, random seeds, absolute paths, data provenance, Docker determinism — and produces a scored checklist with fixes
mcp_servers: []
allowed_tools:
  - Read
  - Write
  - Bash
---

# Reproducibility Audit

Systematically checks a computational project for reproducibility issues and
produces a prioritised fix list with a reproducibility score.

## When to Use

- Before submitting a paper or sharing code
- After onboarding to a project to understand its state
- As part of a CI check
- When a collaborator reports "it doesn't run on my machine"

## Audit Checklist

### 1. Environment (25 points)

```bash
# Check for lockfiles
ls requirements.txt pyproject.toml environment.yml poetry.lock conda-lock.yml 2>/dev/null

# Check for Docker
ls Dockerfile docker-compose.yml 2>/dev/null

# Check for pinned versions (no unpinned >=)
grep -n ">=" requirements.txt 2>/dev/null | head -20
grep -n "^[a-zA-Z]" requirements.txt | grep -v "==" 2>/dev/null
```

Score:
- ✅ +10 pts: Lockfile with pinned versions present
- ✅ +10 pts: Docker or conda environment file present
- ✅ +5 pts: Python version specified (`.python-version`, `pyproject.toml [tool.python]`)

### 2. Random Seeds (20 points)

```bash
# Check for seed-setting in scripts
grep -rn "random_state\|np.random.seed\|random.seed\|torch.manual_seed\|SEED" \
  --include="*.py" --include="*.ipynb" .

# Flag numpy/sklearn/torch usage without seeds
grep -rn "import numpy\|from sklearn\|import torch" \
  --include="*.py" . | head -20
```

Score:
- ✅ +20 pts: All scripts/notebooks set random seeds at top
- ⚠️  +10 pts: Seeds set in some but not all files
- ❌  +0 pts: No seed-setting found

### 3. Data Provenance (20 points)

```bash
# Check for data card
ls data/data_card.md data/README.md README.md 2>/dev/null
grep -r "source\|license\|doi\|url" data/ 2>/dev/null | head -10

# Check for absolute paths (bad)
grep -rn "^/" --include="*.py" --include="*.ipynb" . | grep -v ".git" | head -20
```

Score:
- ✅ +10 pts: Data card present with source, license, version
- ✅ +10 pts: No absolute paths in code (all relative)

### 4. Pipeline Automation (20 points)

```bash
# Check for Makefile, DVC, Snakemake
ls Makefile dvc.yaml Snakefile workflow/ 2>/dev/null

# Check notebooks are runnable top-to-bottom
# (manual check: restart kernel and run all)
```

Score:
- ✅ +20 pts: Single command reproduces all results (`make all`, `dvc repro`)
- ⚠️  +10 pts: Manual steps documented in README
- ❌  +0 pts: No reproducible pipeline

### 5. Code Organisation (15 points)

```bash
# Check for src/ structure
ls src/ 2>/dev/null

# Check notebooks for non-sequential execution
python3 -c "
import json, glob, sys
for nb_path in glob.glob('**/*.ipynb', recursive=True):
    with open(nb_path) as f:
        nb = json.load(f)
    execs = [c.get('execution_count') for c in nb.get('cells', []) if c.get('execution_count')]
    if execs != sorted(execs):
        print(f'WARNING: {nb_path} has non-sequential execution order')
"
```

Score:
- ✅ +10 pts: Reusable logic in `src/` modules
- ✅ +5 pts: Notebooks run sequentially (no out-of-order cells)

## Scoring

| Score | Grade | Meaning |
|---|---|---|
| 90–100 | A | Fully reproducible |
| 70–89 | B | Mostly reproducible; minor fixes needed |
| 50–69 | C | Reproducible with effort; significant fixes needed |
| < 50 | D | Not reproducible without significant work |

## Fix Priority

1. **Critical**: Missing lockfile — add `pip freeze > requirements.txt`
2. **Critical**: Absolute paths — replace with `pathlib.Path` relative paths
3. **High**: Missing random seeds — add seed block at top of each file
4. **High**: No pipeline automation — add `Makefile` with `all` target
5. **Medium**: Missing data card — create `data/data_card.md`

## Review Checklist

- [ ] Lockfile present with pinned versions
- [ ] Environment reproducible (Docker or conda)
- [ ] All random operations seeded
- [ ] No absolute paths
- [ ] Data provenance documented
- [ ] Single command reproduces all results
- [ ] Notebooks run top-to-bottom cleanly
- [ ] Reproducibility score ≥ 70
