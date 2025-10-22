#!/usr/bin/env python3
"""
Generate coverage badge color based on coverage percentage.
"""

import json
import os
import sys
from pathlib import Path

def main():
    coverage_file = Path('coverage.json')
    
    # Check if coverage file exists
    if not coverage_file.exists():
        print('❌ Error: coverage.json file not found')
        sys.exit(1)
    
    try:
        with open(coverage_file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f'❌ Error: Invalid JSON in coverage file: {e}')
        sys.exit(1)
    except PermissionError:
        print('❌ Error: Permission denied reading coverage.json')
        sys.exit(1)
    except Exception as e:
        print(f'❌ Error reading coverage.json: {e}')
        sys.exit(1)
    
    # Validate data structure
    if 'totals' not in data:
        print('❌ Error: Missing "totals" section in coverage data')
        sys.exit(1)
    
    if 'percent_covered' not in data['totals']:
        print('❌ Error: Missing "percent_covered" in coverage totals')
        sys.exit(1)
    
    try:
        total = float(data['totals']['percent_covered'])
    except (ValueError, TypeError) as e:
        print(f'❌ Error: Invalid coverage percentage value: {e}')
        sys.exit(1)
    
    # Determine badge color based on coverage percentage (using float comparison)
    if total < 70.0:
        color = 'red'
    elif total < 85.0:
        color = 'yellow'
    else:
        color = 'brightgreen'
    
    # Check if GITHUB_ENV exists
    github_env = os.environ.get('GITHUB_ENV')
    if not github_env:
        print('❌ Error: GITHUB_ENV environment variable not set')
        sys.exit(1)
    
    try:
        # Set GitHub environment variables
        with open(github_env, 'a') as env_file:
            env_file.write(f'COVERAGE_PERCENT={total:.1f}\n')
            env_file.write(f'COVERAGE_COLOR={color}\n')
    except PermissionError:
        print(f'❌ Error: Permission denied writing to {github_env}')
        sys.exit(1)
    except Exception as e:
        print(f'❌ Error writing to GitHub environment file: {e}')
        sys.exit(1)
    
    print(f'Coverage: {total:.1f}% - Color: {color}')

if __name__ == '__main__':
    main()