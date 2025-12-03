#!/usr/bin/env python3
"""
Test installation orchestrator (dry run)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from lintune.core.installer import Installer, InstallProgress, InstallStatus


def progress_callback(progress: InstallProgress):
    """Print progress updates"""
    pct = progress.progress_percent
    step = progress.current_step.value
    print(f"[{pct:3d}%] Step {progress.step_number}/{progress.total_steps}: {step:20s} - {progress.message}")


def main():
    print("=" * 60)
    print("Installer Orchestrator Test")
    print("=" * 60)
    print()
    
    installer = Installer(progress_callback=progress_callback)
    
    # Run system check only (safe, no changes)
    print("Running system check...")
    print()
    
    result = installer.check_system()
    
    print()
    print(f"System check: {'✓ Passed' if result else '✗ Failed'}")
    print()
    
    if installer.distro_info:
        print(f"Distribution: {installer.distro_info.display_name}")
        print(f"Supported: {installer.distro_info.is_supported}")
        print(f"Package Manager: {installer.distro_info.package_manager}")
    
    print()
    
    if installer.system_status:
        print("Current system status:")
        print(f"  GDM installed: {installer.system_status.gdm_installed}")
        print(f"  GDM enabled: {installer.system_status.gdm_enabled}")
        print(f"  Himmelblau: {installer.system_status.himmelblau_installed}")
        print(f"  NSS configured: {installer.system_status.nss_configured}")
        print(f"  PAM configured: {installer.system_status.pam_configured}")
        print(f"  Services running: {installer.system_status.himmelblaud_running}")
        print(f"  Domain: {installer.system_status.configured_domain}")
        print()
        print(f"  Status: {installer.system_status.enrollment_status}")
    
    print()
    print("=" * 60)
    print("Installation Steps (what would happen):")
    print("=" * 60)
    print()
    print("  1. Check system compatibility")
    print("  2. Install/enable GDM")
    print("  3. Install build dependencies")
    print("  4. Clone & build Himmelblau (~2-5 min)")
    print("  5. Configure NSS, PAM, systemd")
    print("  6. Start services")
    print("  7. Verify installation")
    print()
    
    if installer.system_status and installer.system_status.is_fully_configured:
        print("✓ System is already fully configured!")
        print("  No installation needed.")
    else:
        print("To install, call: installer.install('your-domain.com')")
    
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

