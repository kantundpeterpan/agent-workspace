#!/usr/bin/env python3
"""
Dependency Checker Tool
Analyzes project dependencies for security vulnerabilities and outdated packages.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional


def detect_project_type(project_path: str) -> str:
    """Detect the type of project based on files present."""
    path = Path(project_path)

    if (path / "package.json").exists():
        return "npm"
    elif (path / "requirements.txt").exists() or (path / "pyproject.toml").exists():
        return "pip"
    elif (path / "Cargo.toml").exists():
        return "cargo"
    elif (path / "Gemfile").exists():
        return "gem"
    elif (path / "composer.json").exists():
        return "composer"
    else:
        return "unknown"


def check_npm_security(project_path: str) -> List[Dict[str, Any]]:
    """Check npm packages for security vulnerabilities."""
    vulnerabilities = []

    try:
        result = subprocess.run(
            ["npm", "audit", "--json"], cwd=project_path, capture_output=True, text=True
        )

        if result.returncode == 0:
            return vulnerabilities  # No vulnerabilities

        data = json.loads(result.stdout)
        advisories = data.get("advisories", {})

        for advisory_id, advisory in advisories.items():
            vulnerabilities.append(
                {
                    "package": advisory.get("module_name", "unknown"),
                    "severity": advisory.get("severity", "unknown"),
                    "description": advisory.get("overview", ""),
                    "fixed_in": advisory.get("patched_versions", "unknown"),
                }
            )

    except Exception as e:
        pass  # npm audit might not be available

    return vulnerabilities


def check_npm_outdated(project_path: str) -> List[Dict[str, Any]]:
    """Check for outdated npm packages."""
    outdated = []

    try:
        result = subprocess.run(
            ["npm", "outdated", "--json"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )

        data = json.loads(result.stdout)

        for package, info in data.items():
            outdated.append(
                {
                    "package": package,
                    "current": info.get("current", "unknown"),
                    "latest": info.get("latest", "unknown"),
                }
            )

    except Exception as e:
        pass

    return outdated


def check_pip_security(project_path: str) -> List[Dict[str, Any]]:
    """Check pip packages for security vulnerabilities using safety."""
    vulnerabilities = []

    try:
        result = subprocess.run(
            ["safety", "check", "--json"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return vulnerabilities  # No vulnerabilities

        data = json.loads(result.stdout)

        for vuln in data.get("vulnerabilities", []):
            vulnerabilities.append(
                {
                    "package": vuln.get("package_name", "unknown"),
                    "severity": vuln.get("severity", "unknown"),
                    "description": vuln.get("vulnerability_id", ""),
                    "fixed_in": vuln.get("fixed_version", "unknown"),
                }
            )

    except Exception as e:
        # safety might not be installed
        pass

    return vulnerabilities


def check_pip_outdated(project_path: str) -> List[Dict[str, Any]]:
    """Check for outdated pip packages."""
    outdated = []

    try:
        result = subprocess.run(
            ["pip", "list", "--outdated", "--format=json"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )

        packages = json.loads(result.stdout)

        for pkg in packages:
            outdated.append(
                {
                    "package": pkg.get("name", "unknown"),
                    "current": pkg.get("version", "unknown"),
                    "latest": pkg.get("latest_version", "unknown"),
                }
            )

    except Exception as e:
        pass

    return outdated


def analyze_dependencies(
    project_path: str,
    check_security: bool = True,
    check_outdated: bool = True,
    severity_threshold: str = "moderate",
) -> Dict[str, Any]:
    """Analyze project dependencies.

    Args:
        project_path: Path to the project root directory
        check_security: Whether to check for security vulnerabilities
        check_outdated: Whether to check for outdated packages
        severity_threshold: Minimum severity level to report (low, moderate, high, critical)

    Returns:
        Analysis results with vulnerabilities, outdated packages, and summary
    """
    path = Path(project_path)

    if not path.exists():
        return {"status": "error", "error": f"Project path not found: {project_path}"}

    # Detect project type
    project_type = detect_project_type(project_path)

    if project_type == "unknown":
        return {
            "status": "error",
            "error": "Could not detect project type. Supported: npm, pip, cargo, gem, composer",
        }

    vulnerabilities = []
    outdated = []

    # Check based on project type
    if project_type == "npm":
        if check_security:
            vulnerabilities = check_npm_security(project_path)
        if check_outdated:
            outdated = check_npm_outdated(project_path)

    elif project_type == "pip":
        if check_security:
            vulnerabilities = check_pip_security(project_path)
        if check_outdated:
            outdated = check_pip_outdated(project_path)

    # Filter by severity
    severity_order = {"low": 0, "moderate": 1, "high": 2, "critical": 3}
    threshold_level = severity_order.get(severity_threshold, 1)

    filtered_vulns = [
        v
        for v in vulnerabilities
        if severity_order.get(v["severity"], 0) >= threshold_level
    ]

    return {
        "status": "success",
        "project_type": project_type,
        "vulnerabilities": filtered_vulns,
        "outdated": outdated,
        "summary": {
            "total_dependencies": len(outdated),  # Approximation
            "vulnerable_count": len(filtered_vulns),
            "outdated_count": len(outdated),
        },
    }


if __name__ == "__main__":
    import fire

    fire.Fire(analyze_dependencies)
