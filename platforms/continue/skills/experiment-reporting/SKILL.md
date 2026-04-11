---
name: experiment-reporting
description: Generates structured experiment reports from MLflow/W&B logs or raw metrics — comparison tables, run summaries, and LaTeX/Markdown methods sections
mcp_servers: []
allowed_tools:
  - Read
  - Write
  - Bash
---

# Experiment Reporting

Converts raw experiment logs, metrics files, or tracking backend outputs
into structured, readable reports.

## When to Use

- Summarising results from a hyperparameter sweep
- Writing the Results section of a paper from experiment logs
- Comparing multiple runs in a leaderboard table
- Generating a methods section from a run config

## Workflow

### 1. Load Experiment Results

```python
import pandas as pd
import json
from pathlib import Path

# From a directory of JSON metric files
records = []
for p in Path("results/").glob("*.json"):
    with open(p) as f:
        run = json.load(f)
    records.append({
        "run_id": p.stem,
        "model": run["config"]["model"],
        "lr": run["config"]["lr"],
        "n_estimators": run["config"].get("n_estimators"),
        "cv_auc_mean": run["metrics"]["cv_auc_mean"],
        "cv_auc_std":  run["metrics"]["cv_auc_std"],
        "test_auc":    run["metrics"].get("test_auc"),
    })

results = pd.DataFrame(records).sort_values("cv_auc_mean", ascending=False)
```

### 2. Generate Leaderboard Table

```python
# Markdown table
print(results.to_markdown(index=False, floatfmt=".4f"))

# LaTeX table
latex = results.to_latex(
    index=False, float_format="%.4f",
    caption="Cross-validation results (mean ± SD over 5 folds).",
    label="tab:cv_results",
    bold_rows=False,
)
Path("tables/cv_leaderboard.tex").write_text(latex)
```

### 3. Highlight Best Run

```python
best = results.iloc[0]
print(f"""
Best run: {best['run_id']}
  Model:       {best['model']}
  CV AUC:      {best['cv_auc_mean']:.4f} ± {best['cv_auc_std']:.4f}
  Test AUC:    {best['test_auc']:.4f}
  Config:      lr={best['lr']}, n_estimators={best['n_estimators']}
""")
```

### 4. Plot Results

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# CV AUC by model type
by_model = results.groupby("model")["cv_auc_mean"]
by_model.mean().sort_values().plot.barh(ax=axes[0], xerr=by_model.std())
axes[0].set_xlabel("Mean CV AUC"); axes[0].set_title("CV AUC by Model")

# Learning rate sensitivity
lr_sweep = results.sort_values("lr")
axes[1].errorbar(lr_sweep["lr"], lr_sweep["cv_auc_mean"],
                  yerr=lr_sweep["cv_auc_std"], fmt="o-")
axes[1].set_xscale("log"); axes[1].set_xlabel("Learning rate")
axes[1].set_ylabel("CV AUC"); axes[1].set_title("LR Sensitivity")

fig.tight_layout()
fig.savefig("figures/experiment_results.png", dpi=150)
```

### 5. Generate Methods Section Text

```python
config = best.to_dict()
methods_text = f"""
We evaluated {len(results)} model configurations using {5}-fold stratified
cross-validation. Models included: {', '.join(results['model'].unique())}.
Hyperparameter search used random search over {len(results)} configurations.

The best-performing model was {config['model']} (CV AUC = {config['cv_auc_mean']:.3f}
± {config['cv_auc_std']:.3f}), with learning rate {config['lr']:.4f} and
{int(config['n_estimators'])} estimators. Final evaluation on the held-out
test set yielded AUC = {config['test_auc']:.3f}.
"""
Path("reports/methods_snippet.md").write_text(methods_text)
print(methods_text)
```

### 6. MLflow Integration

```python
import mlflow

runs = mlflow.search_runs(
    experiment_names=["my_experiment"],
    filter_string="metrics.cv_auc > 0.8",
    order_by=["metrics.cv_auc DESC"],
)
print(runs[["run_id", "params.model", "metrics.cv_auc", "metrics.test_auc"]].head(10))
```

## Review Checklist

- [ ] All runs loaded with consistent schema
- [ ] Leaderboard table generated (Markdown and/or LaTeX)
- [ ] Best run identified with full config
- [ ] Results plot saved to `figures/`
- [ ] Methods section snippet generated from best run config
- [ ] CV metric reported as mean ± SD (not just mean)
- [ ] Baseline comparison included in the table
