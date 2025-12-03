#!/usr/bin/env python3
"""
Comprehensive detection verification for LinTune

Validates that all detection logic is accurate by cross-checking
with actual system state using multiple methods.
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from lintune.core.distro import DistroDetector
from lintune.core.validator import SystemValidator
from lintune.core.package_manager import PacmanManager


def run_cmd(cmd: list[str], timeout: int = 5) -> tuple[int, str, str]:
    """Run command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def verify_distro_detection():
    """Verify distribution detection"""
    print("=" * 60)
    print("1. DISTRIBUTION DETECTION")
    print("=" * 60)
    
    detector = DistroDetector()
    info = detector.detect()
    
    # Cross-check with /etc/os-release
    code, stdout, _ = run_cmd(["cat", "/etc/os-release"])
    
    print(f"\nOur detection:")
    print(f"  ID: {info.distro_id}")
    print(f"  Name: {info.name}")
    print(f"  Version: {info.version}")
    print(f"  Supported: {info.is_supported}")
    
    print(f"\n/etc/os-release says:")
    for line in stdout.split('\n')[:5]:
        print(f"  {line}")
    
    # Verify
    os_id = ""
    for line in stdout.split('\n'):
        if line.startswith('ID='):
            os_id = line.split('=')[1].strip('"')
    
    match = info.distro_id == os_id
    print(f"\n{'✓' if match else '✗'} Detection matches: {match}")
    return match


def verify_display_manager():
    """Verify display manager detection"""
    print("\n" + "=" * 60)
    print("2. DISPLAY MANAGER DETECTION")
    print("=" * 60)
    
    validator = SystemValidator()
    status = validator.validate()
    
    print(f"\nOur detection:")
    print(f"  Current DM: {status.current_display_manager}")
    print(f"  GDM installed: {status.gdm_installed}")
    print(f"  GDM enabled: {status.gdm_enabled}")
    
    # Cross-check with systemctl
    print(f"\nSystemctl verification:")
    
    dms = ['gdm', 'gdm3', 'sddm', 'lightdm']
    active_dm = None
    
    for dm in dms:
        code, stdout, _ = run_cmd(["systemctl", "is-enabled", f"{dm}.service"])
        is_enabled = code == 0
        code2, stdout2, _ = run_cmd(["systemctl", "is-active", f"{dm}.service"])
        is_active = code2 == 0
        
        if is_enabled or is_active:
            print(f"  {dm}: enabled={is_enabled}, active={is_active}")
            if is_enabled:
                active_dm = dm
    
    # Check if GDM package is installed
    pm = PacmanManager()
    gdm_pkg_installed = pm.is_installed("gdm")
    print(f"\n  GDM package installed (pacman -Q): {gdm_pkg_installed}")
    
    match = (status.current_display_manager == active_dm or 
             (active_dm and active_dm.startswith(status.current_display_manager or "")))
    print(f"\n{'✓' if match else '✗'} DM detection matches: {match}")
    return match


def verify_himmelblau_installation():
    """Verify Himmelblau installation detection"""
    print("\n" + "=" * 60)
    print("3. HIMMELBLAU INSTALLATION DETECTION")
    print("=" * 60)
    
    validator = SystemValidator()
    status = validator.validate()
    
    print(f"\nOur detection:")
    print(f"  Installed: {status.himmelblau_installed}")
    print(f"  Version: {status.himmelblau_version}")
    
    # Cross-check binary existence
    binaries = [
        "/usr/sbin/himmelblaud",
        "/usr/sbin/himmelblaud_tasks",
        "/usr/bin/aad-tool",
        "/usr/sbin/broker",
        "/usr/lib/security/pam_himmelblau.so",
        "/usr/lib/libnss_himmelblau.so.2",
    ]
    
    print(f"\nBinary verification:")
    all_exist = True
    for binary in binaries:
        exists = Path(binary).exists()
        all_exist = all_exist and exists
        print(f"  {'✓' if exists else '✗'} {binary}")
    
    # Check version
    code, stdout, _ = run_cmd(["/usr/sbin/himmelblaud", "--version"])
    print(f"\n  Version from binary: {stdout if code == 0 else 'N/A'}")
    
    match = status.himmelblau_installed == all_exist
    print(f"\n{'✓' if match else '✗'} Installation detection matches: {match}")
    return match


def verify_nss_configuration():
    """Verify NSS configuration detection"""
    print("\n" + "=" * 60)
    print("4. NSS CONFIGURATION DETECTION")
    print("=" * 60)
    
    validator = SystemValidator()
    status = validator.validate()
    
    print(f"\nOur detection:")
    print(f"  NSS configured: {status.nss_configured}")
    
    # Read actual file
    try:
        with open("/etc/nsswitch.conf", "r") as f:
            content = f.read()
        
        print(f"\n/etc/nsswitch.conf relevant lines:")
        for line in content.split('\n'):
            if line.startswith('passwd:') or line.startswith('group:'):
                print(f"  {line}")
        
        has_himmelblau = 'himmelblau' in content
        print(f"\n  Contains 'himmelblau': {has_himmelblau}")
        
        match = status.nss_configured == has_himmelblau
        print(f"\n{'✓' if match else '✗'} NSS detection matches: {match}")
        return match
        
    except Exception as e:
        print(f"  Error reading file: {e}")
        return False


def verify_pam_configuration():
    """Verify PAM configuration detection"""
    print("\n" + "=" * 60)
    print("5. PAM CONFIGURATION DETECTION")
    print("=" * 60)
    
    validator = SystemValidator()
    status = validator.validate()
    
    print(f"\nOur detection:")
    print(f"  PAM configured: {status.pam_configured}")
    
    # Read actual file
    pam_files = ["/etc/pam.d/system-auth", "/etc/pam.d/common-auth"]
    
    for pam_file in pam_files:
        if Path(pam_file).exists():
            try:
                with open(pam_file, "r") as f:
                    content = f.read()
                
                print(f"\n{pam_file} (first 10 lines with himmelblau):")
                count = 0
                for line in content.split('\n'):
                    if 'himmelblau' in line.lower() or 'pam_himmelblau' in line:
                        print(f"  {line[:70]}")
                        count += 1
                
                has_pam = 'pam_himmelblau' in content
                print(f"\n  Contains 'pam_himmelblau': {has_pam}")
                
                match = status.pam_configured == has_pam
                print(f"\n{'✓' if match else '✗'} PAM detection matches: {match}")
                return match
                
            except Exception as e:
                print(f"  Error reading file: {e}")
    
    return False


def verify_service_status():
    """Verify systemd service status detection"""
    print("\n" + "=" * 60)
    print("6. SERVICE STATUS DETECTION")
    print("=" * 60)
    
    validator = SystemValidator()
    status = validator.validate()
    
    print(f"\nOur detection:")
    print(f"  himmelblaud running: {status.himmelblaud_running}")
    print(f"  himmelblaud-tasks running: {status.himmelblaud_tasks_running}")
    print(f"  cronie running: {status.cronie_running}")
    
    # Cross-check with systemctl
    print(f"\nSystemctl verification:")
    
    services = [
        ("himmelblaud", status.himmelblaud_running),
        ("himmelblaud-tasks", status.himmelblaud_tasks_running),
        ("cronie", status.cronie_running),
    ]
    
    all_match = True
    for service, our_status in services:
        code, _, _ = run_cmd(["systemctl", "is-active", f"{service}.service"])
        actual_running = code == 0
        match = our_status == actual_running
        all_match = all_match and match
        print(f"  {service}: ours={our_status}, actual={actual_running} {'✓' if match else '✗'}")
    
    print(f"\n{'✓' if all_match else '✗'} Service detection matches: {all_match}")
    return all_match


def verify_domain_configuration():
    """Verify domain configuration detection"""
    print("\n" + "=" * 60)
    print("7. DOMAIN CONFIGURATION DETECTION")
    print("=" * 60)
    
    validator = SystemValidator()
    status = validator.validate()
    
    print(f"\nOur detection:")
    print(f"  Config exists: {status.config_exists}")
    print(f"  Domain: {status.configured_domain}")
    
    # Read actual config
    config_file = Path("/etc/himmelblau/himmelblau.conf")
    
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                content = f.read()
            
            print(f"\n/etc/himmelblau/himmelblau.conf:")
            for line in content.split('\n'):
                if line.strip() and not line.strip().startswith('#'):
                    print(f"  {line}")
            
            # Extract domain
            actual_domain = None
            for line in content.split('\n'):
                if line.strip().startswith('domains'):
                    parts = line.split('=')
                    if len(parts) == 2:
                        actual_domain = parts[1].strip()
            
            print(f"\n  Extracted domain: {actual_domain}")
            
            match = status.configured_domain == actual_domain
            print(f"\n{'✓' if match else '✗'} Domain detection matches: {match}")
            return match
            
        except Exception as e:
            print(f"  Error reading file: {e}")
            return False
    else:
        print(f"\n  Config file does not exist")
        return status.config_exists == False


def verify_enrollment_status():
    """Verify enrollment status detection"""
    print("\n" + "=" * 60)
    print("8. ENROLLMENT STATUS DETECTION")
    print("=" * 60)
    
    validator = SystemValidator()
    status = validator.validate()
    
    print(f"\nOur detection:")
    print(f"  is_fully_configured: {status.is_fully_configured}")
    print(f"  enrollment_status: {status.enrollment_status}")
    
    # Check aad-tool status
    code, stdout, stderr = run_cmd(["/usr/bin/aad-tool", "status"])
    print(f"\naad-tool status:")
    print(f"  Exit code: {code}")
    print(f"  Output: {stdout}")
    
    # Manual check
    fully_configured = (
        status.himmelblau_installed and
        status.nss_configured and
        status.pam_configured and
        status.himmelblaud_running and
        status.config_exists
    )
    
    print(f"\nManual verification:")
    print(f"  Himmelblau installed: {status.himmelblau_installed}")
    print(f"  NSS configured: {status.nss_configured}")
    print(f"  PAM configured: {status.pam_configured}")
    print(f"  Service running: {status.himmelblaud_running}")
    print(f"  Config exists: {status.config_exists}")
    print(f"  -> Fully configured: {fully_configured}")
    
    match = status.is_fully_configured == fully_configured
    print(f"\n{'✓' if match else '✗'} Enrollment detection matches: {match}")
    return match


def main():
    print("\n" + "=" * 60)
    print("LINTUNE DETECTION VERIFICATION")
    print("=" * 60)
    print("\nThis script validates that all detection logic")
    print("accurately reflects the actual system state.\n")
    
    results = {
        "Distribution": verify_distro_detection(),
        "Display Manager": verify_display_manager(),
        "Himmelblau": verify_himmelblau_installation(),
        "NSS Config": verify_nss_configuration(),
        "PAM Config": verify_pam_configuration(),
        "Services": verify_service_status(),
        "Domain": verify_domain_configuration(),
        "Enrollment": verify_enrollment_status(),
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_pass = True
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        all_pass = all_pass and passed
    
    print()
    if all_pass:
        print("✓ ALL DETECTIONS VERIFIED SUCCESSFULLY!")
    else:
        print("✗ SOME DETECTIONS NEED ATTENTION")
    
    print()
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())

