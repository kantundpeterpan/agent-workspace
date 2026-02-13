#!/usr/bin/env python3
"""
Complexity Analyzer Tool
Analyzes cyclomatic and cognitive complexity of source code files.
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional


def calculate_cyclomatic_complexity(code: str) -> int:
    """Calculate cyclomatic complexity for a code block."""
    # Count decision points
    complexity = 1  # Base complexity

    # Pattern matching for decision points
    patterns = [
        r"\bif\b",
        r"\belif\b",
        r"\belse\b(?![:}]\s*\bif\b)",
        r"\bfor\b",
        r"\bwhile\b",
        r"\bexcept\b",
        r"\bfinally\b",
        r"\bwith\b",
        r"\bassert\b",
        r"\braise\b",
        r"\band\b",
        r"\bor\b",
        r"\?\w+\s*:",
    ]

    for pattern in patterns:
        complexity += len(re.findall(pattern, code, re.IGNORECASE))

    return complexity


def calculate_cognitive_complexity(code: str) -> int:
    """Calculate cognitive complexity for a code block."""
    complexity = 0
    nesting_level = 0

    lines = code.split("\n")
    for line in lines:
        stripped = line.strip()

        # Increase nesting
        if re.search(r"\b(def|class|if|for|while|with|try|except)\b", stripped):
            complexity += 1 + nesting_level
            if stripped.endswith(":"):
                nesting_level += 1

        # Decrease nesting
        elif stripped and not stripped.startswith("#"):
            # Check for dedent
            leading_space = len(line) - len(line.lstrip())
            if leading_space < nesting_level * 4:  # Assuming 4-space indentation
                nesting_level = max(0, leading_space // 4)

    return complexity


def extract_functions(code: str, language: str) -> List[Dict[str, Any]]:
    """Extract function definitions from code."""
    functions = []

    if language in ["python", "py"]:
        # Match Python function definitions
        pattern = r"^(def|class)\s+(\w+)\s*\([^)]*\)\s*:"
        for match in re.finditer(pattern, code, re.MULTILINE):
            line_num = code[: match.start()].count("\n") + 1
            func_name = match.group(2)

            # Extract function body
            start = match.end()
            end = start
            indent = None
            for i, line in enumerate(code[start:].split("\n")):
                if i == 0:
                    continue
                if line.strip():
                    current_indent = len(line) - len(line.lstrip())
                    if indent is None:
                        indent = current_indent
                    elif current_indent <= indent and not line.strip().startswith("#"):
                        break
                end = start + sum(len(l) + 1 for l in code[start:].split("\n")[: i + 1])

            func_code = code[start:end]
            functions.append({"name": func_name, "line": line_num, "code": func_code})

    return functions


def analyze_file(
    file_path: str, threshold: int, include_cognitive: bool
) -> Dict[str, Any]:
    """Analyze a single file for complexity."""
    path = Path(file_path)

    if not path.exists():
        return {"status": "error", "error": f"File not found: {file_path}"}

    try:
        code = path.read_text()
    except Exception as e:
        return {"status": "error", "error": f"Error reading file: {str(e)}"}

    # Detect language
    language = path.suffix.lstrip(".")

    # Extract functions
    functions = extract_functions(code, language)

    # Analyze each function
    results = []
    total_complexity = 0
    high_complexity_count = 0

    for func in functions:
        cyclomatic = calculate_cyclomatic_complexity(func["code"])

        result = {"name": func["name"], "line": func["line"], "complexity": cyclomatic}

        if include_cognitive:
            result["cognitive"] = calculate_cognitive_complexity(func["code"])

        # Check threshold
        warnings = []
        if cyclomatic > threshold:
            warnings.append(
                f"Cyclomatic complexity ({cyclomatic}) exceeds threshold ({threshold})"
            )
            high_complexity_count += 1

        if include_cognitive and result.get("cognitive", 0) > threshold * 1.5:
            warnings.append(f"Cognitive complexity ({result['cognitive']}) is high")

        if warnings:
            result["warnings"] = warnings

        results.append(result)
        total_complexity += cyclomatic

    # Calculate overall score
    avg_complexity = total_complexity / len(functions) if functions else 0

    # Generate recommendations
    recommendations = []
    if high_complexity_count > 0:
        recommendations.append(
            f"{high_complexity_count} function(s) exceed complexity threshold. Consider refactoring."
        )
    if avg_complexity > threshold:
        recommendations.append(
            f"Average complexity ({avg_complexity:.1f}) is high. Consider simplifying code."
        )
    if not functions:
        recommendations.append(
            "No functions detected. File may be a module-level script."
        )

    return {
        "status": "success",
        "file": str(file_path),
        "score": avg_complexity,
        "functions": results,
        "summary": {
            "total_functions": len(functions),
            "high_complexity_count": high_complexity_count,
            "average_complexity": round(avg_complexity, 2),
            "recommendations": recommendations,
        },
    }


def main():
    """Main entry point."""
    # Read input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "error": f"Invalid JSON input: {str(e)}"}))
        sys.exit(1)

    # Extract parameters
    file_path = input_data.get("file_path")
    threshold = input_data.get("threshold", 10)
    include_cognitive = input_data.get("include_cognitive", True)

    if not file_path:
        print(
            json.dumps(
                {"status": "error", "error": "Missing required parameter: file_path"}
            )
        )
        sys.exit(1)

    # Analyze
    result = analyze_file(file_path, threshold, include_cognitive)

    # Output JSON
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
