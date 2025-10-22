#!/usr/bin/env python3
"""
Professional Email Marketing Platform
Entry point for command-line interface

Usage:
    python main.py [options]

For development:
    Make sure to install the package in development mode:
    pip install -e .
    
    Or add src to PYTHONPATH:
    export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
"""

import sys
from pathlib import Path

def main():
    """Main entry point for the email marketing platform."""
    try:
        # Try proper package import first
        from src.mailing.cli import main as cli_main
        cli_main()
    except ImportError as e:
        # Provide helpful error message instead of silent fallback
        project_root = Path(__file__).parent
        src_dir = project_root / "src"
        
        if not src_dir.exists():
            print("❌ Error: src directory not found.")
            print(f"Expected location: {src_dir}")
            print("Please run from project root directory.")
            sys.exit(1)
        
        print("❌ Import Error: Package not properly installed.")
        print(f"Details: {e}")
        print("\nTo fix this, install the package in development mode:")
        print("  pip install -e .")
        print("\nOr set PYTHONPATH:")
        print(f"  export PYTHONPATH=\"$PYTHONPATH:{src_dir}\"")
        print("  python main.py")
        print("\nOr use absolute imports:")
        print("  python -m src.mailing.cli")
        sys.exit(1)

if __name__ == "__main__":
    main()