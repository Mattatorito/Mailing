#!/usr/bin/env python3
"""
Check if coverage meets the required threshold.
"""

import json
import sys
import os
from pathlib import Path

def main():
    coverage_file = Path('coverage.json')
    
    # Check if coverage file exists
    if not coverage_file.exists():
        print('❌ Error: coverage.json file not found')
        print('Make sure to run coverage analysis before checking threshold')
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
    
    try:
        threshold = float(os.environ.get('COVERAGE_THRESHOLD', '90'))
    except ValueError:
        print('❌ Error: Invalid COVERAGE_THRESHOLD environment variable')
        sys.exit(1)
    
    print(f'Current coverage: {total:.2f}%')
    print(f'Required threshold: {threshold}%')
    
    if total < threshold:
        print(f'❌ Coverage {total:.2f}% is below required {threshold}%')
        print('Coverage regression detected!')
        sys.exit(1)
    else:
        print(f'✅ Coverage {total:.2f}% meets requirement')

if __name__ == '__main__':
    main()