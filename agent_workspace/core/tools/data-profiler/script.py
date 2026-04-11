#!/usr/bin/env python3
"""
Data Profiler Tool
Generates a quick structural summary of a tabular dataset.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _load_dataframe(file_path: str):
    """Load a dataframe from CSV, TSV, Parquet, or Excel."""
    try:
        import pandas as pd
    except ImportError:
        return None, "pandas is required: pip install pandas"

    path = Path(file_path)
    if not path.exists():
        return None, f"File not found: {file_path}"

    suffix = path.suffix.lower()
    try:
        if suffix in (".csv",):
            df = pd.read_csv(file_path)
        elif suffix in (".tsv",):
            df = pd.read_csv(file_path, sep="\t")
        elif suffix in (".parquet",):
            df = pd.read_parquet(file_path)
        elif suffix in (".xlsx", ".xls"):
            df = pd.read_excel(file_path)
        else:
            # Try CSV as fallback
            df = pd.read_csv(file_path)
    except Exception as e:
        return None, f"Could not read file: {e}"

    return df, None


def profile(
    file_path: str,
    sample_rows: int = 5,
    max_categories: int = 20,
) -> Dict[str, Any]:
    """
    Profile a dataset and return shape, column stats, and quality warnings.

    Args:
        file_path: Path to the CSV, TSV, Parquet, or Excel file.
        sample_rows: Number of example rows to include per column.
        max_categories: Max unique values to list for categorical columns.

    Returns:
        Dictionary with status, shape, columns, warnings, and message.
    """
    df, err = _load_dataframe(file_path)
    if err:
        return {"status": "error", "message": err, "shape": {"rows": 0, "columns": 0}}

    import pandas as pd
    import numpy as np

    rows, cols = df.shape
    warnings: List[str] = []
    column_profiles: List[Dict[str, Any]] = []

    for col in df.columns:
        series = df[col]
        missing_count = int(series.isna().sum())
        missing_pct = round(missing_count / rows * 100, 2) if rows > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))
        dtype_str = str(series.dtype)

        # Sample values (non-null)
        sample_vals = series.dropna().head(sample_rows).tolist()
        sample_vals = [v if not isinstance(v, float) or not np.isnan(v) else None for v in sample_vals]

        stats: Dict[str, Any] = {}
        if pd.api.types.is_numeric_dtype(series):
            desc = series.describe()
            stats = {
                "min": round(float(desc["min"]), 4) if not np.isnan(desc["min"]) else None,
                "max": round(float(desc["max"]), 4) if not np.isnan(desc["max"]) else None,
                "mean": round(float(desc["mean"]), 4) if not np.isnan(desc["mean"]) else None,
                "std": round(float(desc["std"]), 4) if not np.isnan(desc["std"]) else None,
                "median": round(float(series.median()), 4),
            }
        else:
            top_cats = series.value_counts().head(max_categories).to_dict()
            stats = {"top_categories": {str(k): int(v) for k, v in top_cats.items()}}

        col_info: Dict[str, Any] = {
            "name": col,
            "dtype": dtype_str,
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "unique_count": unique_count,
            "sample_values": [str(v) for v in sample_vals],
            "stats": stats,
        }
        column_profiles.append(col_info)

        # Quality warnings
        if missing_pct > 50:
            warnings.append(f"Column '{col}' has {missing_pct}% missing values.")
        if unique_count == 1:
            warnings.append(f"Column '{col}' is constant (only one unique value).")
        if unique_count == rows and not pd.api.types.is_numeric_dtype(series):
            warnings.append(f"Column '{col}' may be an ID column (all values unique).")

    return {
        "status": "success",
        "shape": {"rows": rows, "columns": cols},
        "columns": column_profiles,
        "warnings": warnings,
        "message": f"Profiled {cols} columns across {rows} rows from '{Path(file_path).name}'.",
    }


if __name__ == "__main__":
    import fire
    fire.Fire(profile)
