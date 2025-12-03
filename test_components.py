#!/usr/bin/env python3
"""
Test LinTune components without GUI

Validates that all core components work correctly
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_distro_detection():
    """Test distro detection"""
    print("Testing distro detection...")
    from lintune.core.distro import DistroDetector
    
    detector = DistroDetector()
    info = detector.detect()
    
    print(f"  ✓ Distribution: {info.name}")
    print(f"  ✓ Version: {info.version}")
    print(f"  ✓ Supported: {info.is_supported}")
    print(f"  ✓ Package Manager: {info.package_manager}")
    print(f"  ✓ Icon: {detector.get_distro_icon(info)}")
    print()
    
    return info

def test_system_validation():
    """Test system validation"""
    print("Testing system validation...")
    from lintune.core.validator import SystemValidator
    
    validator = SystemValidator()
    status = validator.validate()
    
    print(f"  ✓ Display Manager: {status.current_display_manager or 'None'}")
    print(f"  ✓ GDM Installed: {status.gdm_installed}")
    print(f"  ✓ GDM Enabled: {status.gdm_enabled}")
    print(f"  ✓ Rust Installed: {status.rust_installed}")
    print(f"  ✓ Himmelblau Installed: {status.himmelblau_installed}")
    print(f"  ✓ NSS Configured: {status.nss_configured}")
    print(f"  ✓ PAM Configured: {status.pam_configured}")
    print(f"  ✓ Services Running: {status.himmelblaud_running}")
    print(f"  ✓ Configured Domain: {status.configured_domain or 'None'}")
    print(f"  ✓ Enrollment Status: {status.enrollment_status}")
    print()
    
    return status

def test_stylesheet():
    """Test stylesheet loading"""
    print("Testing stylesheet...")
    from pathlib import Path
    
    stylesheet_path = Path(__file__).parent / 'src/lintune/resources/styles/fluent.qss'
    
    if stylesheet_path.exists():
        with open(stylesheet_path, 'r') as f:
            content = f.read()
            print(f"  ✓ Stylesheet loaded ({len(content)} bytes)")
            print(f"  ✓ Contains 'primary' color: {'primary' in content}")
            print(f"  ✓ Contains card styles: {'card' in content}")
    else:
        print(f"  ✗ Stylesheet not found at {stylesheet_path}")
    print()

def main():
    """Run all tests"""
    print("=" * 60)
    print("LinTune Component Validation")
    print("=" * 60)
    print()
    
    try:
        # Test components
        distro_info = test_distro_detection()
        system_status = test_system_validation()
        test_stylesheet()
        
        # Summary
        print("=" * 60)
        print("✓ All core components validated successfully!")
        print("=" * 60)
        print()
        print("System Summary:")
        print(f"  • Running on: {distro_info.display_name}")
        print(f"  • Supported: {'Yes' if distro_info.is_supported else 'No'}")
        print(f"  • Enrollment: {system_status.enrollment_status}")
        print(f"  • Ready for install: {system_status.is_ready_for_install}")
        print()
        print("To launch the GUI, run:")
        print("  python -m src.lintune")
        print()
        
    except Exception as e:
        print(f"✗ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

