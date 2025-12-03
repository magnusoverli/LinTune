#!/usr/bin/env python3
"""
Test system configurator (checks only, no actual changes)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from lintune.core.configurator import SystemConfigurator


def main():
    print("=" * 60)
    print("System Configurator Test")
    print("=" * 60)
    print()
    
    configurator = SystemConfigurator()
    
    # Check file existence
    print("Configuration files:")
    files = [
        ("NSS config", configurator.NSS_CONF),
        ("PAM config", configurator.PAM_CONF),
        ("Himmelblau config", configurator.HIMMELBLAU_CONF),
    ]
    
    for name, path in files:
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {name}: {path}")
    
    print()
    
    # Check backups
    print("Backup files:")
    for name, path in files:
        backup = Path(str(path) + ".backup")
        exists = backup.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {name} backup: {backup}")
    
    print()
    
    # Check systemd services
    print("Systemd services:")
    services = [
        configurator.SYSTEMD_DIR / "himmelblaud.service",
        configurator.SYSTEMD_DIR / "himmelblaud-tasks.service",
    ]
    
    for service in services:
        exists = service.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {service.name}")
    
    print()
    
    # Check cache directories
    print("Cache directories:")
    for cache_dir in configurator.CACHE_DIRS:
        exists = cache_dir.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {cache_dir}")
    
    print()
    
    # Check NSS configuration
    if configurator.NSS_CONF.exists():
        with open(configurator.NSS_CONF, 'r') as f:
            content = f.read()
        
        has_himmelblau = 'himmelblau' in content
        status = "✓" if has_himmelblau else "✗"
        print(f"{status} NSS configured for Himmelblau")
    
    # Check PAM configuration
    if configurator.PAM_CONF.exists():
        with open(configurator.PAM_CONF, 'r') as f:
            content = f.read()
        
        has_himmelblau = 'pam_himmelblau' in content
        status = "✓" if has_himmelblau else "✗"
        print(f"{status} PAM configured for Himmelblau")
    
    print()
    print("Note: This is a read-only test, no changes made")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

