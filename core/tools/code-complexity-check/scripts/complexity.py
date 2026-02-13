#!/usr/bin/env python3
"""Code complexity analyzer for pair programming review sessions."""

import sys
import json
import subprocess
from pathlib import Path

def detect_language(file_path):
    """Detect language from file extension."""
    suffix = Path(file_path).suffix.lower()
    mapping = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript'
    }
    return mapping.get(suffix, 'unknown')

def analyze_with_radon(file_path, threshold):
    """Analyze Python code with radon."""
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
        return {'error': f'Radon analysis failed: {str(e)}'}

def analyze_with_lizard(file_path, threshold):
    """Analyze any language with lizard (fallback)."""
    try:
        result = subprocess.run(
            ['lizard', file_path, '-l', 'javascript', '-C', str(threshold)],
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
        return {'error': f'Lizard analysis failed: {str(e)}'}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: complexity.py <file_path> [threshold] [language]'}))
        sys.exit(1)
    
    file_path = sys.argv[1]
    threshold = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    language = sys.argv[3] if len(sys.argv) > 3 else 'auto'
    
    if not Path(file_path).exists():
        print(json.dumps({'error': f'File not found: {file_path}'}))
        sys.exit(1)
    
    if language == 'auto':
        language = detect_language(file_path)
    
    # Try language-specific analyzer first
    if language == 'python':
        result = analyze_with_radon(file_path, threshold)
    else:
        result = analyze_with_lizard(file_path, threshold)
    
    output = {
        'file': file_path,
        'language': language,
        'threshold': threshold,
        'flagged_functions': result if not isinstance(result, dict) else [],
        'error': result.get('error') if isinstance(result, dict) else None
    }
    
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()
