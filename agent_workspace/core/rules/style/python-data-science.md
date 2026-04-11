# Rule: Python Data Science Standards

Guidelines for writing reproducible, readable, and maintainable Python code
in data science and statistical computing projects.

## Notebook Hygiene

- Every notebook must have a top-level Markdown cell with: title, author, date, dataset, purpose
- Cells must be executable top-to-bottom from a fresh kernel without errors
- Do not use `plt.show()` as the only output mechanism — save figures to `figures/` as well
- Restart and re-run the entire notebook before committing

## Reproducibility

- Set all random seeds at the top of every script or notebook:
  ```python
  import random, numpy as np, torch
  SEED = 42
  random.seed(SEED); np.random.seed(SEED)
  # torch.manual_seed(SEED)  # if using PyTorch
  ```
- Pin all package versions in `requirements.txt` or `environment.yml`
- Never use absolute paths — use `pathlib.Path` relative to the project root
- Data loading cells must specify the source URL or local path clearly

## DataFrame Conventions

- Never modify a DataFrame in-place silently; either use `inplace=True` with a comment or assign to a new variable
- Name intermediate DataFrames descriptively: `df_clean`, `df_train`, not `df2`, `temp`
- Document column meaning in a data card or notebook Markdown cell
- Use `.copy()` when slicing to avoid `SettingWithCopyWarning`

## Visualisation

```python
# GOOD — save AND show
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(df["score"], bins=30)
ax.set_xlabel("Score"); ax.set_ylabel("Count"); ax.set_title("Score Distribution")
fig.tight_layout()
fig.savefig("figures/score_distribution.png", dpi=150, bbox_inches="tight")
plt.show()
```

- Axes must have labels and units
- Use colour-blind-safe palettes (`seaborn-colorblind`, `viridis`, `tab10`)
- Figure size: default `(8, 5)` for single plots, `(12, 4)` for multi-panel

## Model Serialisation

- Use versioned filenames: `model_logreg_v1.pkl`, not `model.pkl`
- Save the training configuration alongside the model artefact
- Document the scikit-learn or framework version used at the top of the training script

## Code Organisation

- Extract reusable logic from notebooks into `src/` modules; import them
- Functions longer than 20 lines should be extracted and tested
- Each module has a docstring; each public function has a docstring with Args/Returns

## Review Checklist

- [ ] Random seeds set at the top
- [ ] Notebook runs top-to-bottom cleanly
- [ ] All figures saved to `figures/` directory
- [ ] No absolute paths
- [ ] DataFrame mutations commented or assigned explicitly
- [ ] Package versions pinned
- [ ] Model artefacts versioned
- [ ] Long functions extracted to `src/` modules
