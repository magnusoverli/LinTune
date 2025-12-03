#!/usr/bin/env python3
"""
Test package manager functionality

Tests package detection and dependency resolution
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from lintune.core.distro import DistroDetector
from lintune.core.package_manager import (
    get_package_manager, 
    get_himmelblau_dependencies,
    map_package_name
)


def main():
    print("=" * 60)
    print("Package Manager Test")
    print("=" * 60)
    print()
    
    # Detect distro
    detector = DistroDetector()
    distro_info = detector.detect()
    
    print(f"Distribution: {distro_info.display_name}")
    print(f"Supported: {distro_info.is_supported}")
    print()
    
    # Get package manager
    pm = get_package_manager(distro_info.supported)
    
    if not pm:
        print("✗ No package manager available for this distro")
        return 1
    
    print(f"✓ Package manager: {pm.__class__.__name__}")
    print()
    
    # Test package checking
    print("Checking installed packages:")
    test_packages = ["rust", "cargo", "git", "python"]
    
    for pkg in test_packages:
        mapped = map_package_name(pkg, distro_info.supported)
        installed = pm.is_installed(mapped)
        status = "✓" if installed else "✗"
        print(f"  {status} {pkg} ({mapped}): {'installed' if installed else 'not installed'}")
    
    print()
    
    # Show Himmelblau dependencies
    print("Himmelblau dependencies for this distro:")
    deps = get_himmelblau_dependencies(distro_info.supported)
    for dep in deps:
        installed = pm.is_installed(dep)
        status = "✓" if installed else "✗"
        print(f"  {status} {dep}")
    
    print()
    
    # Count installed
    installed_count = sum(1 for dep in deps if pm.is_installed(dep))
    print(f"Dependencies: {installed_count}/{len(deps)} installed")
    
    if installed_count == len(deps):
        print("✓ All dependencies satisfied!")
    else:
        print(f"⚠ Missing {len(deps) - installed_count} dependencies")
    
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

