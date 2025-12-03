#!/usr/bin/env python3
"""
LinTune Launcher for PyInstaller

This script provides a proper entry point for PyInstaller that avoids
relative import issues by using absolute imports.
"""

import sys
import os

# When running as a frozen executable, ensure the bundled package is importable
if getattr(sys, 'frozen', False):
    # Running as compiled
    bundle_dir = sys._MEIPASS
    sys.path.insert(0, bundle_dir)
else:
    # Running as script - add src to path
    src_dir = os.path.join(os.path.dirname(__file__), 'src')
    sys.path.insert(0, src_dir)

# Now import and run
from lintune.__main__ import main

if __name__ == "__main__":
    main()

