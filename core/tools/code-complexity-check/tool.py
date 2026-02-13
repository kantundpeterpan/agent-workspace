#!/usr/bin/env python3
"""Code complexity analyzer for pair programming review sessions."""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import fire


class CodeComplexityCheck:
    """Analyzes code complexity metrics to identify functions needing refactoring."""

    def _detect_language(self, file_path: str) -> str:
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

    def _analyze_with_radon(self, file_path: str, threshold: int) -> List[Dict[str, Any]]:
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
            return [{'error': f'Radon analysis failed: {str(e)}'}]

    def _analyze_with_lizard(self, file_path: str, threshold: int) -> List[Dict[str, Any]]:
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
            return [{'error': f'Lizard analysis failed: {str(e)}'}]

    def analyze(self, file_path: str, threshold: int = 10, language: str = "auto") -> str:
        """Calculate cyclomatic complexity and other metrics for code files.
        
        Args:
            file_path: Path to the code file to analyze
            threshold: Complexity threshold (functions above this are flagged, default: 10)
            language: Programming language (python, javascript, typescript, auto for auto-detect)
            
        Returns:
            JSON string with analysis results
        """
        path = Path(file_path)
        
        if not path.exists():
            return json.dumps({'error': f'File not found: {file_path}'}, indent=2)
        
        if language == 'auto':
            language = self._detect_language(file_path)
        
        # Try language-specific analyzer first
        if language == 'python':
            result = self._analyze_with_radon(file_path, threshold)
        else:
            result = self._analyze_with_lizard(file_path, threshold)
        
        # Check if result contains error
        has_error = any('error' in item for item in result)
        
        output = {
            'file': file_path,
            'language': language,
            'threshold': threshold,
            'flagged_functions': [] if has_error else result,
            'error': result[0].get('error') if has_error and result else None
        }
        
        return json.dumps(output, indent=2)


def main():
    """CLI entry point using fire."""
    fire.Fire(CodeComplexityCheck)


if __name__ == '__main__':
    main()
