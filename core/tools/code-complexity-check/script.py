#!/usr/bin/env python3
"""Code complexity analyzer for pair programming review sessions."""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional


def detect_language(file_path: str) -> str:
    """Detect language from file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Detected language name
    """
    suffix = Path(file_path).suffix.lower()
    mapping = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript'
    }
    return mapping.get(suffix, 'unknown')


def analyze_with_radon(file_path: str, threshold: int) -> List[Dict[str, Any]]:
    """Analyze Python code with radon.
    
    Args:
        file_path: Path to Python file
        threshold: Complexity threshold
        
    Returns:
        List of flagged functions
    """
    try:
        result = subprocess.run(
            ['radon', 'cc', file_path, '-j'],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        
        flagged = []
        for file_data in data.values():
            for func in file_data:
                if func['complexity'] > threshold:
                    flagged.append({
                        'function': func['name'],
                        'complexity': func['complexity'],
                        'line': func['lineno'],
                        'rank': func['rank']
                    })
        
        return flagged
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        raise Exception(f'Radon analysis failed: {str(e)}')


def analyze_with_lizard(file_path: str, threshold: int) -> List[Dict[str, Any]]:
    """Analyze any language with lizard (fallback).
    
    Args:
        file_path: Path to code file
        threshold: Complexity threshold
        
    Returns:
        List of flagged functions
    """
    try:
        result = subprocess.run(
            ['lizard', file_path, '-C', str(threshold)],
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.strip().split('\n')
        flagged = []
        
        # Parse lizard output
        for line in lines:
            if line and not line.startswith('-') and 'NLOC' not in line:
                parts = line.split()
                if len(parts) >= 4 and parts[0].isdigit():
                    complexity = int(parts[0])
                    if complexity > threshold:
                        flagged.append({
                            'function': parts[3] if len(parts) > 3 else 'unknown',
                            'complexity': complexity,
                            'nloc': int(parts[1]),
                            'tokens': int(parts[2])
                        })
        
        return flagged
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise Exception(f'Lizard analysis failed: {str(e)}')


def analyze(file_path: str, threshold: int = 10, language: str = "auto") -> Dict[str, Any]:
    """Calculate cyclomatic complexity and other metrics for code files.
    
    Args:
        file_path: Path to the code file to analyze
        threshold: Complexity threshold (functions above this are flagged, default: 10)
        language: Programming language (python, javascript, typescript, auto for auto-detect)
        
    Returns:
        Analysis results with flagged functions and recommendations
    """
    path = Path(file_path)
    
    if not path.exists():
        return {
            'status': 'error',
            'file': file_path,
            'error': f'File not found: {file_path}'
        }
    
    if language == 'auto':
        language = detect_language(file_path)
    
    try:
        # Try language-specific analyzer first
        if language == 'python':
            flagged = analyze_with_radon(file_path, threshold)
        else:
            flagged = analyze_with_lizard(file_path, threshold)
        
        # Generate recommendations
        recommendations = []
        if flagged:
            recommendations.append(
                f"{len(flagged)} function(s) exceed complexity threshold. Consider refactoring."
            )
            if len(flagged) > 3:
                recommendations.append(
                    "High number of complex functions. Review overall architecture."
                )
        else:
            recommendations.append("All functions are within acceptable complexity levels.")
        
        return {
            'status': 'success',
            'file': file_path,
            'language': language,
            'threshold': threshold,
            'flagged_functions': flagged,
            'summary': {
                'total_flagged': len(flagged),
                'recommendations': recommendations
            }
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'file': file_path,
            'language': language,
            'threshold': threshold,
            'error': str(e)
        }


if __name__ == '__main__':
    import fire
    fire.Fire(analyze)
