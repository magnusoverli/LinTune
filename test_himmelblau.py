#!/usr/bin/env python3
"""
Test Himmelblau builder (dry run - no actual build)

Checks if Himmelblau is installed and shows what would happen.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from lintune.core.himmelblau import HimmelblauBuilder, BuildProgress


def progress_callback(progress: BuildProgress):
    """Print progress updates"""
    print(f"[{progress.progress:3d}%] {progress.status.value:12s} - {progress.message}")


def main():
    print("=" * 60)
    print("Himmelblau Builder Test")
    print("=" * 60)
    print()
    
    builder = HimmelblauBuilder(progress_callback=progress_callback)
    
    # Check if already installed
    if builder.is_installed():
        print("✓ Himmelblau is already installed")
        version = builder.get_version()
        if version:
            print(f"  Version: {version}")
        print()
        
        # Show binary locations
        print("Installed binaries:")
        for binary, path in builder.BINARIES.items():
            exists = Path(path).exists()
            status = "✓" if exists else "✗"
            print(f"  {status} {path}")
        print()
    else:
        print("✗ Himmelblau is not installed")
        print()
        print("To install, the builder would:")
        print("  1. Clone repository from GitHub")
        print("  2. Build with cargo (2-5 minutes)")
        print("  3. Install binaries to system paths")
        print("  4. Cleanup build directory")
        print()
        print("Note: Actual installation not performed in this test")
        print()
    
    # Show configuration
    print("Builder configuration:")
    print(f"  Repository: {builder.REPO_URL}")
    print(f"  Build directory: {builder.BUILD_DIR}")
    print(f"  Total steps: {builder.current_progress.total_steps}")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

