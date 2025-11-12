#!/usr/bin/env python3
"""
vidgen pdf to video generator
entry point for the application
"""
import sys
from pathlib import Path

# add project root to path
sys.path.insert(0, str(Path(__file__).parent))
# use the cli tool as the main app entry point
from cli.app import main

if __name__ == "__main__":
    main()

