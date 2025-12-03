"""
System validation for LinTune

Checks the current state of the system to determine what's installed
and configured for EntraID/Intune enrollment.
"""

import os
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ComponentStatus(Enum):
    """Status of a system component"""
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    CONFIGURED = "configured"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class IntuneStatus:
    """Intune enrollment and compliance status"""
    enrollment_state: str  # "enrolled", "not_enrolled", "device_limit", "failed"
    enrollment_error: str | None
    compliance_state: str  # "compliant", "non_compliant", "unknown", "not_applicable"
    last_activity: str | None
    
    @property
    def is_enrolled(self) -> bool:
        return self.enrollment_state == "enrolled"
    
    @property
    def is_compliant(self) -> bool:
        return self.compliance_state == "compliant"
    
    @property
    def display_enrollment(self) -> str:
        """Human-readable enrollment status"""
        states = {
            "enrolled": "Enrolled",
            "not_enrolled": "Not enrolled",
            "device_limit": "Device limit reached",
            "failed": "Enrollment failed",
        }
        return states.get(self.enrollment_state, "Unknown")
    
    @property
    def display_compliance(self) -> str:
        """Human-readable compliance status"""
        states = {
            "compliant": "Compliant",
            "non_compliant": "Non-compliant",
            "unknown": "Unknown",
            "not_applicable": "N/A",
        }
        return states.get(self.compliance_state, "Unknown")


@dataclass
class SystemStatus:
    """Complete system status for EntraID/Intune setup"""
    
    # Display Manager
    current_display_manager: str | None
    gdm_installed: bool
    gdm_enabled: bool
    
    # Dependencies
    rust_installed: bool
    cargo_installed: bool
    build_deps_installed: bool
    
    # Himmelblau
    himmelblau_installed: bool
    himmelblau_version: str | None
    
    # System Configuration
    nss_configured: bool
    pam_configured: bool
    services_installed: bool
    
    # Runtime
    himmelblaud_running: bool
    himmelblaud_tasks_running: bool
    cronie_running: bool
    
    # Configuration
    config_exists: bool
    configured_domain: str | None
    
    # Backups
    has_backups: bool
    
    # Intune Status
    intune_status: IntuneStatus | None = None
    
    @property
    def is_ready_for_install(self) -> bool:
        """Check if system is ready for installation"""
        return self.gdm_installed and not self.himmelblau_installed
    
    @property
    def is_partially_installed(self) -> bool:
        """Check if installation was started but not completed"""
        return self.himmelblau_installed and not self.himmelblaud_running
    
    @property
    def is_fully_configured(self) -> bool:
        """Check if system is fully configured and running"""
        return (
            self.himmelblau_installed
            and self.nss_configured
            and self.pam_configured
            and self.himmelblaud_running
            and self.config_exists
        )
    
    @property
    def enrollment_status(self) -> str:
        """Get human-readable enrollment status"""
        if self.is_fully_configured:
            return "Enrolled and running"
        elif self.is_partially_installed:
            return "Partially configured"
        elif self.himmelblau_installed:
            return "Installed, not configured"
        else:
            return "Not enrolled"


class SystemValidator:
    """Validates system state for EntraID/Intune setup"""
    
    def __init__(self):
        self.status = None
    
    def validate(self) -> SystemStatus:
        """
        Perform a complete system validation
        
        Returns:
            SystemStatus object with all checks
        """
        self.status = SystemStatus(
            # Display Manager
            current_display_manager=self._get_current_dm(),
            gdm_installed=self._check_gdm_installed(),
            gdm_enabled=self._check_gdm_enabled(),
            
            # Dependencies
            rust_installed=self._check_package('rust') or self._check_package('rustc'),
            cargo_installed=self._check_package('cargo'),
            build_deps_installed=self._check_build_deps(),
            
            # Himmelblau
            himmelblau_installed=self._check_himmelblau_installed(),
            himmelblau_version=self._get_himmelblau_version(),
            
            # System Configuration
            nss_configured=self._check_nss_configured(),
            pam_configured=self._check_pam_configured(),
            services_installed=self._check_services_installed(),
            
            # Runtime
            himmelblaud_running=self._check_service_running('himmelblaud'),
            himmelblaud_tasks_running=self._check_service_running('himmelblaud-tasks'),
            cronie_running=self._check_service_running('cronie') or self._check_service_running('cron'),
            
            # Configuration
            config_exists=Path('/etc/himmelblau/himmelblau.conf').exists(),
            configured_domain=self._get_configured_domain(),
            
            # Backups
            has_backups=self._check_backups_exist(),
        )
        
        # Get Intune status (after basic status is set)
        self.status.intune_status = self.get_intune_status()
        
        return self.status
    
    def _get_current_dm(self) -> str | None:
        """Get the currently enabled display manager"""
        display_managers = ['gdm', 'gdm3', 'sddm', 'lightdm', 'lxdm', 'xdm']
        
        for dm in display_managers:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-enabled', f'{dm}.service'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return dm
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        return None
    
    def _check_gdm_installed(self) -> bool:
        """Check if GDM is installed"""
        return self._check_package('gdm') or self._check_package('gdm3')
    
    def _check_gdm_enabled(self) -> bool:
        """Check if GDM is enabled"""
        dm = self._get_current_dm()
        return dm in ['gdm', 'gdm3']
    
    def _check_package(self, package: str) -> bool:
        """Check if a package is installed (works for pacman and dpkg)"""
        # Try pacman first (Arch/CachyOS)
        try:
            result = subprocess.run(
                ['pacman', '-Q', package],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Try dpkg (Debian/Ubuntu)
        try:
            result = subprocess.run(
                ['dpkg', '-s', package],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return False
    
    def _check_build_deps(self) -> bool:
        """Check if basic build dependencies are installed"""
        required = ['pkg-config', 'git']
        return all(self._check_package(pkg) for pkg in required)
    
    def _check_himmelblau_installed(self) -> bool:
        """Check if Himmelblau binaries are installed"""
        return Path('/usr/sbin/himmelblaud').exists()
    
    def _get_himmelblau_version(self) -> str | None:
        """Get Himmelblau version if installed using native aad-tool"""
        if not self._check_himmelblau_installed():
            return None
        
        # Use native aad-tool version command
        try:
            result = subprocess.run(
                ['aad-tool', 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback to direct binary
        try:
            result = subprocess.run(
                ['/usr/sbin/himmelblaud', '--version'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return "installed"
    
    def _check_nss_configured(self) -> bool:
        """Check if NSS is configured for Himmelblau"""
        try:
            with open('/etc/nsswitch.conf', 'r') as f:
                content = f.read()
                return 'himmelblau' in content
        except (FileNotFoundError, PermissionError):
            return False
    
    def _check_pam_configured(self) -> bool:
        """Check if PAM is configured for Himmelblau"""
        try:
            with open('/etc/pam.d/system-auth', 'r') as f:
                content = f.read()
                return 'pam_himmelblau' in content
        except FileNotFoundError:
            # Try common-auth for Debian/Ubuntu
            try:
                with open('/etc/pam.d/common-auth', 'r') as f:
                    content = f.read()
                    return 'pam_himmelblau' in content
            except (FileNotFoundError, PermissionError):
                return False
        except PermissionError:
            return False
    
    def _check_services_installed(self) -> bool:
        """Check if systemd services are installed"""
        return Path('/etc/systemd/system/himmelblaud.service').exists()
    
    def _check_service_running(self, service: str) -> bool:
        """Check if a systemd service is running"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', f'{service}.service'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_aad_tool_status(self) -> tuple[bool, str]:
        """
        Check himmelblaud status using native aad-tool.
        
        Returns:
            Tuple of (is_working, status_message)
        """
        try:
            result = subprocess.run(
                ['aad-tool', 'status'],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = result.stdout.strip()
            if result.returncode == 0 and output == "working!":
                return True, "working!"
            else:
                return False, output or result.stderr.strip() or "Unknown error"
        except FileNotFoundError:
            return False, "aad-tool not found"
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
    
    def clear_cache(self, use_pkexec: bool = True) -> tuple[bool, str]:
        """
        Clear himmelblau cache using native aad-tool cache-clear.
        Forces a refresh of cached user/group data.
        
        Note: Requires root privileges.
        
        Args:
            use_pkexec: If True, use pkexec for privilege escalation (GUI-friendly)
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if use_pkexec:
                cmd = ['pkexec', 'aad-tool', 'cache-clear']
            else:
                cmd = ['aad-tool', 'cache-clear']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # Longer timeout for pkexec auth dialog
            )
            
            output = result.stdout.strip()
            if result.returncode == 0 and "success" in output.lower():
                return True, "Cache cleared successfully"
            elif result.returncode == 0:
                return True, output or "Cache cleared"
            elif "must be run as root" in result.stderr:
                return False, "Root privileges required"
            else:
                return False, result.stderr.strip() or output or "Cache clear failed"
        except FileNotFoundError:
            return False, "aad-tool or pkexec not found"
        except subprocess.TimeoutExpired:
            return False, "Timeout or auth cancelled"
        except Exception as e:
            return False, str(e)
    
    def test_auth(self, username: str) -> tuple[bool, str]:
        """
        Test authentication for a user using native aad-tool auth-test.
        
        Args:
            username: The EntraID username to test
            
        Returns:
            Tuple of (success, message)
        """
        try:
            result = subprocess.run(
                ['aad-tool', 'auth-test', '--name', username],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return True, result.stdout.strip() or "Authentication test passed"
            else:
                return False, result.stderr.strip() or result.stdout.strip() or "Auth test failed"
        except FileNotFoundError:
            return False, "aad-tool not found"
        except subprocess.TimeoutExpired:
            return False, "Timeout - user may need to complete MFA"
        except Exception as e:
            return False, str(e)
    
    def get_tpm_status(self) -> tuple[bool, str]:
        """
        Check TPM status using native aad-tool tpm.
        
        Note: Requires root privileges.
        
        Returns:
            Tuple of (tpm_in_use, status_message)
        """
        import re
        
        try:
            result = subprocess.run(
                ['pkexec', 'aad-tool', 'tpm'],
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout.strip()
            
            # Strip ANSI escape codes (colors)
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            output = ansi_escape.sub('', output)
            
            if result.returncode == 0:
                # Check if TPM is actually in use
                output_lower = output.lower()
                if "not in use" in output_lower:
                    return False, output
                elif "in use" in output_lower or "tpm" in output_lower:
                    return True, output
                return True, output or "TPM check completed"
            else:
                error = result.stderr.strip()
                error = ansi_escape.sub('', error)  # Strip colors from errors too
                if "must be run as root" in error:
                    return False, "Root privileges required"
                return False, error or output or "TPM check failed"
        except FileNotFoundError:
            return False, "aad-tool or pkexec not found"
        except subprocess.TimeoutExpired:
            return False, "Timeout or auth cancelled"
        except Exception as e:
            return False, str(e)
    
    def set_offline_breakglass(self, ttl: str = None) -> tuple[bool, str]:
        """
        Activate offline breakglass mode using native aad-tool.
        
        Allows cached password authentication when Entra ID is unreachable.
        
        Args:
            ttl: Time-to-live (e.g., "2h", "1d"). None uses default from config.
                 Use "0" to disable breakglass mode.
        
        Note: Requires root privileges and must be enabled in himmelblau.conf.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            cmd = ['pkexec', 'aad-tool', 'offline-breakglass']
            if ttl:
                cmd.extend(['--ttl', ttl])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout.strip()
            if result.returncode == 0:
                return True, output or "Breakglass mode updated"
            else:
                error = result.stderr.strip()
                return False, error or output or "Breakglass command failed"
        except FileNotFoundError:
            return False, "aad-tool or pkexec not found"
        except subprocess.TimeoutExpired:
            return False, "Timeout or auth cancelled"
        except Exception as e:
            return False, str(e)
    
    def enumerate_users(self, username: str = None) -> tuple[bool, str]:
        """
        Enumerate and cache Entra ID users/groups using native aad-tool.
        
        Pre-caches user/group data so UID/GID mappings are available
        before authentication.
        
        Args:
            username: Optional username to authenticate as for enumeration
        
        Note: Requires root privileges and Entra ID enrollment.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            cmd = ['pkexec', 'aad-tool', 'enumerate']
            if username:
                cmd.extend(['--name', username])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # Enumeration can take time
            )
            output = result.stdout.strip()
            if result.returncode == 0:
                return True, output or "Enumeration completed"
            else:
                error = result.stderr.strip()
                return False, error or output or "Enumeration failed"
        except FileNotFoundError:
            return False, "aad-tool or pkexec not found"
        except subprocess.TimeoutExpired:
            return False, "Timeout - enumeration may take a while"
        except Exception as e:
            return False, str(e)
    
    def get_version(self) -> str:
        """
        Get himmelblau version using native aad-tool version.
        
        Returns:
            Version string or "unknown"
        """
        try:
            result = subprocess.run(
                ['aad-tool', 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return "unknown"
        except Exception:
            return "unknown"
    
    def _get_configured_domain(self) -> str | None:
        """Get the configured EntraID domain"""
        config_file = Path('/etc/himmelblau/himmelblau.conf')
        
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    if line.strip().startswith('domains'):
                        # Parse: domains = example.com
                        parts = line.split('=')
                        if len(parts) == 2:
                            return parts[1].strip()
        except (FileNotFoundError, PermissionError):
            pass
        
        return None
    
    def _check_backups_exist(self) -> bool:
        """Check if configuration backups exist"""
        backups = [
            Path('/etc/pam.d/system-auth.backup'),
            Path('/etc/nsswitch.conf.backup'),
        ]
        return any(backup.exists() for backup in backups)
    
    def get_intune_status(self) -> IntuneStatus:
        """
        Get Intune enrollment and compliance status.
        
        Uses aad-tool status for daemon health, plus journal for detailed status.
        This is the single source of truth for Intune status detection.
        """
        enrollment_state = "unknown"
        enrollment_error = None
        compliance_state = "unknown"
        last_activity = None
        
        # First check if daemon is working using native aad-tool
        daemon_working, daemon_msg = self.check_aad_tool_status()
        
        if not daemon_working:
            return IntuneStatus(
                enrollment_state="unknown",
                enrollment_error=f"Daemon not responding: {daemon_msg}",
                compliance_state="unknown",
                last_activity=None,
            )
        
        try:
            # Get himmelblaud journal for detailed status
            result = subprocess.run(
                ["journalctl", "-u", "himmelblaud", "-n", "500", "--no-pager"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout
                output_lower = output.lower()
                
                # Determine enrollment state (check most specific errors first)
                if "reached their enrolled device limit" in output_lower:
                    enrollment_state = "device_limit"
                    enrollment_error = "User has reached enrolled device limit in Intune"
                elif "failed to enroll in intune" in output_lower:
                    enrollment_state = "failed"
                    if "badrequest" in output_lower:
                        enrollment_error = "Intune enrollment returned BadRequest"
                    else:
                        enrollment_error = "Intune enrollment failed"
                elif "device is not enrolled" in output_lower:
                    enrollment_state = "not_enrolled"
                elif self.status and self.status.is_fully_configured:
                    # Daemon working + system configured = enrolled
                    enrollment_state = "enrolled"
                else:
                    enrollment_state = "not_enrolled"
                
                # Determine compliance state
                if enrollment_state != "enrolled":
                    compliance_state = "not_applicable"
                elif "non-compliant" in output_lower or "not compliant" in output_lower:
                    compliance_state = "non_compliant"
                elif "compliant" in output_lower:
                    compliance_state = "compliant"
                else:
                    compliance_state = "unknown"
                
                # Get last activity timestamp
                result2 = subprocess.run(
                    ["journalctl", "-u", "himmelblaud", "-n", "1", "--no-pager", "-o", "short"],
                    capture_output=True, text=True, timeout=5
                )
                if result2.returncode == 0 and result2.stdout.strip():
                    lines = result2.stdout.strip().split('\n')
                    for line in lines:
                        if line and not line.startswith('--'):
                            parts = line.split()
                            if len(parts) >= 3:
                                last_activity = f"{parts[0]} {parts[1]} {parts[2]}"
                            break
                            
        except subprocess.TimeoutExpired:
            enrollment_state = "unknown"
            enrollment_error = "Timeout checking status"
        except Exception as e:
            enrollment_state = "unknown"
            enrollment_error = str(e)
        
        return IntuneStatus(
            enrollment_state=enrollment_state,
            enrollment_error=enrollment_error,
            compliance_state=compliance_state,
            last_activity=last_activity,
        )

