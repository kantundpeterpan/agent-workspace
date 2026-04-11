---
name: dataset-documentation
description: Produces a structured data card for a dataset covering provenance, schema, quality metrics, missingness, and ethical considerations
mcp_servers: []
allowed_tools:
  - Read
  - Write
  - Bash
---

# Dataset Documentation

Generates machine-readable and human-readable data cards that document a
dataset's origin, structure, quality, and ethical considerations.

## When to Use

- Beginning work with a new dataset
- Preparing data for sharing or publication
- Complying with reproducibility requirements
- Auditing a dataset for a project

## Data Card Structure

```markdown
# Data Card: {Dataset Name}

## Overview
- **Name**: 
- **Version**: 
- **Date accessed / created**: 
- **Source URL**: 
- **License**: 
- **Citation**: 

## Purpose
- **Intended use**: 
- **Out-of-scope uses**: 

## Schema
| Column | Type | Unit | Description | Example |
|---|---|---|---|---|

## Statistics
- **Rows**: 
- **Columns**: 
- **Time range** (if temporal): 

## Data Quality
| Column | Missing (%) | Unique values | Min | Max | Mean | SD |
|---|---|---|---|---|---|---|

## Known Issues
- 

## Ethical Considerations
- PII columns: 
- Sensitive attributes: 
- Potential biases: 
- Consent / data collection method: 

## Preprocessing Applied
- 

## How to Load
```python
import pandas as pd
df = pd.read_csv("data/raw/dataset.csv")
```
```

## Automated Profiling Script

```python
import pandas as pd
import json
from pathlib import Path

def profile_dataset(path: str) -> dict:
    df = pd.read_csv(path)
    profile = {
        "rows": len(df),
        "columns": len(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missingness": (df.isnull().mean() * 100).round(2).to_dict(),
        "numeric_stats": df.describe().round(4).to_dict(),
        "categorical_stats": {
            col: df[col].value_counts().head(5).to_dict()
            for col in df.select_dtypes(include="object").columns
        },
    }
    return profile

profile = profile_dataset("data/raw/dataset.csv")
print(json.dumps(profile, indent=2))
```

## Review Checklist

- [ ] Source URL and access date recorded
- [ ] License identified
- [ ] Schema table complete (all columns documented)
- [ ] Missing value percentages computed for all columns
- [ ] Descriptive statistics for numeric columns
- [ ] PII columns identified
- [ ] Known biases or quality issues documented
- [ ] Loading instructions provided
- [ ] Data card saved to `data/data_card.md`
