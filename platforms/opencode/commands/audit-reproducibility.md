---
description: "Audit a project for reproducibility \u2014 environment pinning, relative\
  \ paths, random seeds, clean-run verification"
---

Perform a reproducibility audit on the following project directory or file.

Check:
1. Environment specification (requirements.txt / renv.lock / pyproject.toml / environment.yml)
2. All paths are relative (no hardcoded absolute paths)
3. Random seeds are set before every stochastic operation
4. Data files are referenced but not committed (check .gitignore)
5. Analysis scripts run from top to bottom without errors (dry-run if safe)
6. Output files are regenerable from raw data + code

Produce a reproducibility score and a prioritised fix list.

Project path: $ARGUMENTS
