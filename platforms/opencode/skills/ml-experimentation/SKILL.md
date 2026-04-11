---
name: ml-experimentation
description: Runs reproducible ML experiments with cross-validation, hyperparameter tuning, model comparison, and a formatted leaderboard
mcp_servers:
  - context7
allowed_tools:
  - Read
  - Write
  - Bash
---

# ML Experimentation

Structured workflow for designing, running, tracking, and reporting machine
learning experiments with full reproducibility.

## When to Use

- Benchmarking multiple models on a dataset
- Hyperparameter optimisation
- Feature selection experiments
- Comparing preprocessing pipelines

## Experiment Workflow

### 1. Define the Experiment

Before running anything, document:
```yaml
# experiment_config.yaml
experiment_id: "exp001_baseline_models"
dataset: "data/processed/clean.csv"
target: "outcome"
task: "classification"          # classification | regression
metric: "roc_auc"               # primary metric
cv_folds: 5
cv_strategy: "stratified"
random_seed: 42
models:
  - LogisticRegression
  - RandomForestClassifier
  - GradientBoostingClassifier
```

### 2. Set Up Cross-Validation Pipeline

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

SEED = 42
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

models = {
    "LogReg": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, random_state=SEED)),
    ]),
    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=SEED),
    "GBM": GradientBoostingClassifier(n_estimators=100, random_state=SEED),
}

results = []
for name, model in models.items():
    scores = cross_validate(
        model, X_train, y_train, cv=cv,
        scoring=["roc_auc", "f1", "accuracy"],
        return_train_score=True,
    )
    results.append({
        "model": name,
        "AUC (CV mean)": scores["test_roc_auc"].mean().round(4),
        "AUC (CV std)":  scores["test_roc_auc"].std().round(4),
        "F1 (CV mean)":  scores["test_f1"].mean().round(4),
    })

leaderboard = pd.DataFrame(results).sort_values("AUC (CV mean)", ascending=False)
print(leaderboard.to_markdown(index=False))
```

### 3. Hyperparameter Tuning

```python
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint, uniform

param_dist = {
    "n_estimators": randint(50, 500),
    "max_depth": [None, 3, 5, 10],
    "min_samples_leaf": randint(1, 20),
}

search = RandomizedSearchCV(
    RandomForestClassifier(random_state=SEED),
    param_distributions=param_dist,
    n_iter=50,
    cv=cv,
    scoring="roc_auc",
    random_state=SEED,
    n_jobs=-1,
)
search.fit(X_train, y_train)
print(f"Best AUC: {search.best_score_:.4f}")
print(f"Best params: {search.best_params_}")
```

### 4. Feature Importance

```python
import matplotlib.pyplot as plt

best_model = search.best_estimator_
importances = pd.Series(best_model.feature_importances_, index=feature_names)
importances = importances.sort_values(ascending=False).head(20)

fig, ax = plt.subplots(figsize=(8, 6))
importances.plot.barh(ax=ax)
ax.set_xlabel("Importance"); ax.set_title("Top 20 Feature Importances")
fig.tight_layout()
fig.savefig("figures/feature_importance.png", dpi=150)
```

### 5. Save the Best Model

```python
import joblib
joblib.dump(search.best_estimator_, f"models/rf_best_v1.pkl")
# Also save config
import yaml
with open("models/rf_best_v1_config.yaml", "w") as f:
    yaml.dump({"params": search.best_params_, "cv_auc": search.best_score_}, f)
```

## Review Checklist

- [ ] Experiment config written before running
- [ ] Random seed fixed everywhere
- [ ] Cross-validation strategy appropriate for task (stratified for imbalanced)
- [ ] Leaderboard table generated with mean ± std metrics
- [ ] Best model hyperparameters documented
- [ ] Feature importance or coefficient plot saved
- [ ] Best model saved with versioned filename
- [ ] No test-set leakage (test set untouched until final evaluation)
