---
name: eda-visualization
description: Systematic exploratory data analysis workflow covering distributions, correlations, missingness patterns, outlier detection, and publication-quality visualisation
mcp_servers: []
allowed_tools:
  - Read
  - Write
  - Bash
---

# EDA and Visualisation

Provides a structured exploratory data analysis workflow, from first load to
publication-quality figures and a written EDA report.

## When to Use

- First look at a new dataset
- Before model building to check assumptions
- Generating figures for a report or paper
- Auditing data quality

## EDA Workflow

### 1. Load and Inspect

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

df = pd.read_csv("data/processed/clean.csv")

print(f"Shape: {df.shape}")
print(df.dtypes)
print(df.head())
print(df.describe())
```

### 2. Missingness Analysis

```python
missing = df.isnull().mean().sort_values(ascending=False)
missing = missing[missing > 0]

fig, ax = plt.subplots(figsize=(8, max(3, len(missing) * 0.4)))
missing.plot.barh(ax=ax, color="steelblue")
ax.set_xlabel("Missing fraction")
ax.set_title("Missingness by column")
fig.tight_layout()
fig.savefig("figures/missingness.png", dpi=150)
```

### 3. Univariate Distributions

```python
numeric_cols = df.select_dtypes(include="number").columns
n = len(numeric_cols)
fig, axes = plt.subplots(nrows=(n + 2) // 3, ncols=3, figsize=(14, 4 * ((n + 2) // 3)))
for ax, col in zip(axes.flat, numeric_cols):
    ax.hist(df[col].dropna(), bins=30, edgecolor="white")
    ax.set_title(col); ax.set_xlabel(col); ax.set_ylabel("Count")
for ax in axes.flat[n:]:
    ax.set_visible(False)
fig.suptitle("Univariate distributions")
fig.tight_layout()
fig.savefig("figures/univariate.png", dpi=150)
```

### 4. Correlation Matrix

```python
corr = df[numeric_cols].corr()

mask = np.triu(np.ones_like(corr, dtype=bool))
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="coolwarm",
            center=0, vmin=-1, vmax=1, ax=ax, square=True)
ax.set_title("Pearson correlation matrix")
fig.tight_layout()
fig.savefig("figures/correlation_matrix.png", dpi=150)
```

### 5. Outlier Detection

```python
from scipy import stats

outlier_summary = {}
for col in numeric_cols:
    z = np.abs(stats.zscore(df[col].dropna()))
    iqr_low = df[col].quantile(0.25) - 1.5 * (df[col].quantile(0.75) - df[col].quantile(0.25))
    iqr_high = df[col].quantile(0.75) + 1.5 * (df[col].quantile(0.75) - df[col].quantile(0.25))
    outlier_summary[col] = {
        "z_score_>3": int((z > 3).sum()),
        "iqr_outliers": int(((df[col] < iqr_low) | (df[col] > iqr_high)).sum()),
    }
```

### 6. Categorical Summaries

```python
cat_cols = df.select_dtypes(include="object").columns
for col in cat_cols:
    vc = df[col].value_counts()
    fig, ax = plt.subplots(figsize=(8, max(3, len(vc) * 0.3)))
    vc.plot.barh(ax=ax)
    ax.set_title(f"Counts: {col}")
    fig.tight_layout()
    fig.savefig(f"figures/cat_{col}.png", dpi=150)
    plt.close()
```

### 7. Write EDA Report

Summarise findings in `eda_report.md`:
- Dataset overview (shape, time range if applicable)
- Missingness summary (which columns, what fraction)
- Distribution notes (skewness, multimodality)
- Top correlations (r > 0.5)
- Outlier counts
- Key observations for modelling

## Review Checklist

- [ ] Shape, dtypes, missingness printed
- [ ] Missingness bar chart saved
- [ ] Univariate histograms for all numeric columns
- [ ] Correlation matrix computed and visualised
- [ ] Outlier counts documented
- [ ] Categorical distributions plotted
- [ ] All figures saved to `figures/` with 150 dpi
- [ ] `eda_report.md` written with key findings
- [ ] Axes labelled with units on all plots
