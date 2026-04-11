#!/usr/bin/env python3
"""
Stats Formatter Tool
Formats statistical results into APA 7th edition strings with optional LaTeX notation.
"""

import math
from typing import Any, Dict, Optional


def _fmt_p(p: float) -> str:
    """Format a p-value per APA 7 (omit leading zero, < .001 threshold)."""
    if p < 0.001:
        return "< .001"
    return f"= {p:.3f}".replace("0.", ".")


def _fmt_stat(v: float, decimals: int = 2) -> str:
    return f"{v:.{decimals}f}"


def _fmt_ci(lo: float, hi: float) -> str:
    return f"[{lo:.2f}, {hi:.2f}]"


EFFECT_LABELS: Dict[str, str] = {
    "d": "d",
    "eta2": "η²",
    "partial_eta2": "η²p",
    "omega2": "ω²",
    "r": "r",
    "phi": "φ",
    "V": "V",
    "f2": "f²",
    "OR": "OR",
}

EFFECT_LATEX: Dict[str, str] = {
    "d": "d",
    "eta2": r"\eta^2",
    "partial_eta2": r"\eta^2_p",
    "omega2": r"\omega^2",
    "r": "r",
    "phi": r"\phi",
    "V": "V",
    "f2": "f^2",
    "OR": r"\text{OR}",
}


def format_result(
    test_type: str,
    statistic: Optional[float] = None,
    df: Optional[str] = None,
    p_value: Optional[float] = None,
    effect_size: Optional[float] = None,
    effect_size_type: Optional[str] = None,
    ci_lower: Optional[float] = None,
    ci_upper: Optional[float] = None,
    n: Optional[int] = None,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """
    Format a statistical result into APA 7th edition notation.

    Args:
        test_type: Type of test (t_test, f_test, chi_square, correlation, z_test,
                   mann_whitney, wilcoxon, kruskal, regression_coef).
        statistic: Test statistic value.
        df: Degrees of freedom string (e.g. "48" or "2, 45").
        p_value: p-value (formatted as < .001 if needed).
        effect_size: Effect size magnitude.
        effect_size_type: Symbol key for the effect size.
        ci_lower: Lower bound of 95% CI.
        ci_upper: Upper bound of 95% CI.
        n: Sample size.
        alpha: Significance threshold.

    Returns:
        dict with apa_string, latex_string, significant, status.
    """
    try:
        parts_apa: list[str] = []
        parts_latex: list[str] = []

        if test_type == "t_test":
            stat_lbl = "t"
            df_str = f"({df})" if df else ""
            if statistic is not None:
                parts_apa.append(f"t{df_str} = {_fmt_stat(statistic)}")
                parts_latex.append(f"$t{df_str} = {_fmt_stat(statistic)}$")
        elif test_type == "f_test":
            df_str = f"({df})" if df else ""
            if statistic is not None:
                parts_apa.append(f"F{df_str} = {_fmt_stat(statistic)}")
                parts_latex.append(f"$F{df_str} = {_fmt_stat(statistic)}$")
        elif test_type == "chi_square":
            df_str = f"({df}" + (f", N = {n}" if n else "") + ")" if df else ""
            if statistic is not None:
                parts_apa.append(f"χ²{df_str} = {_fmt_stat(statistic)}")
                parts_latex.append(f"$\\chi^2{df_str} = {_fmt_stat(statistic)}$")
        elif test_type == "correlation":
            n_str = f"({n - 2})" if n else ""
            if statistic is not None:
                parts_apa.append(f"r{n_str} = {_fmt_stat(statistic)}")
                parts_latex.append(f"$r{n_str} = {_fmt_stat(statistic)}$")
        elif test_type == "z_test":
            if statistic is not None:
                parts_apa.append(f"z = {_fmt_stat(statistic)}")
                parts_latex.append(f"$z = {_fmt_stat(statistic)}$")
        elif test_type in ("mann_whitney",):
            if statistic is not None:
                parts_apa.append(f"U = {_fmt_stat(statistic, 0)}")
                parts_latex.append(f"$U = {_fmt_stat(statistic, 0)}$")
        elif test_type in ("wilcoxon",):
            if statistic is not None:
                parts_apa.append(f"W = {_fmt_stat(statistic, 0)}")
                parts_latex.append(f"$W = {_fmt_stat(statistic, 0)}$")
        elif test_type in ("kruskal",):
            df_str = f"({df})" if df else ""
            if statistic is not None:
                parts_apa.append(f"H{df_str} = {_fmt_stat(statistic)}")
                parts_latex.append(f"$H{df_str} = {_fmt_stat(statistic)}$")
        elif test_type == "regression_coef":
            if statistic is not None:
                parts_apa.append(f"β = {_fmt_stat(statistic)}")
                parts_latex.append(f"$\\beta = {_fmt_stat(statistic)}$")

        if p_value is not None:
            p_fmt = _fmt_p(p_value)
            parts_apa.append(f"p {p_fmt}")
            parts_latex.append(f"$p {p_fmt}$")

        if effect_size is not None and effect_size_type:
            lbl = EFFECT_LABELS.get(effect_size_type, effect_size_type)
            ltx = EFFECT_LATEX.get(effect_size_type, effect_size_type)
            parts_apa.append(f"{lbl} = {_fmt_stat(effect_size)}")
            parts_latex.append(f"${ltx} = {_fmt_stat(effect_size)}$")

        if ci_lower is not None and ci_upper is not None:
            ci = _fmt_ci(ci_lower, ci_upper)
            parts_apa.append(f"95% CI {ci}")
            parts_latex.append(f"95\\% CI {ci}")

        apa_string = ", ".join(parts_apa)
        latex_string = ", ".join(parts_latex)

        significant = (p_value is not None and p_value < alpha)

        return {
            "status": "success",
            "apa_string": apa_string,
            "latex_string": latex_string,
            "significant": significant,
            "message": "Formatted successfully.",
        }

    except Exception as e:
        return {
            "status": "error",
            "apa_string": "",
            "latex_string": "",
            "significant": False,
            "message": str(e),
        }


if __name__ == "__main__":
    import fire
    fire.Fire(format_result)
