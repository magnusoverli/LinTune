"""
System configurator for LinTune

Configures NSS, PAM, systemd services, and Himmelblau configuration.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime


class SystemConfigurator:
    """Configures system for Himmelblau/EntraID"""
    
    # File paths
    NSS_CONF = Path("/etc/nsswitch.conf")
    PAM_CONF = Path("/etc/pam.d/system-auth")
    HIMMELBLAU_CONF_DIR = Path("/etc/himmelblau")
    HIMMELBLAU_CONF = HIMMELBLAU_CONF_DIR / "himmelblau.conf"
    
    # Service paths
    SYSTEMD_DIR = Path("/etc/systemd/system")
    DBUS_DIR = Path("/usr/share/dbus-1/services")
    
    # Cache directories
    CACHE_DIRS = [
        Path("/var/cache/nss-himmelblau"),
        Path("/var/cache/himmelblau-policies"),
        Path("/etc/krb5.conf.d"),
    ]
    
    def __init__(self, build_dir: Path = Path("/tmp/himmelblau")):
        """
        Initialize configurator
        
        Args:
            build_dir: Path to Himmelblau build directory
        """
        self.build_dir = build_dir
    
    def _backup_file(self, file_path: Path) -> bool:
        """
        Create backup of a file
        
        Args:
            file_path: File to backup
            
        Returns:
            True if successful
        """
        if not file_path.exists():
            return True
        
        backup_path = Path(str(file_path) + ".backup")
        
        try:
            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            print(f"Backup failed: {e}")
            return False
    
    def _restore_file(self, file_path: Path) -> bool:
        """
        Restore file from backup
        
        Args:
            file_path: File to restore
            
        Returns:
            True if successful
        """
        backup_path = Path(str(file_path) + ".backup")
        
        if not backup_path.exists():
            return False
        
        try:
            shutil.copy2(backup_path, file_path)
            return True
        except Exception as e:
            print(f"Restore failed: {e}")
            return False
    
    def configure_nss(self) -> bool:
        """
        Configure NSS to use Himmelblau
        
        Returns:
            True if successful
        """
        if not self._backup_file(self.NSS_CONF):
            return False
        
        try:
            with open(self.NSS_CONF, 'r') as f:
                content = f.read()
            
            # Check if already configured
            if 'himmelblau' in content:
                return True
            
            # Modify passwd and group lines
            lines = content.split('\n')
            new_lines = []
            
            for line in lines:
                if line.startswith('passwd:'):
                    # passwd: files systemd himmelblau
                    if 'himmelblau' not in line:
                        line = 'passwd: files systemd himmelblau'
                elif line.startswith('group:'):
                    # group: files [SUCCESS=merge] systemd himmelblau
                    if 'himmelblau' not in line:
                        line = 'group: files [SUCCESS=merge] systemd himmelblau'
                
                new_lines.append(line)
            
            # Write back via temp file
            new_content = '\n'.join(new_lines)
            
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as tmp:
                tmp.write(new_content)
                tmp_path = tmp.name
            
            result = subprocess.run(
                ["sudo", "cp", tmp_path, str(self.NSS_CONF)],
                capture_output=True
            )
            
            Path(tmp_path).unlink(missing_ok=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"NSS configuration failed: {e}")
            self._restore_file(self.NSS_CONF)
            return False
    
    def configure_pam(self) -> bool:
        """
        Configure PAM to use Himmelblau
        
        Returns:
            True if successful
        """
        if not self._backup_file(self.PAM_CONF):
            return False
        
        pam_config = """#%PAM-1.0

auth       required                    pam_faillock.so      preauth
-auth      [success=3 default=ignore]  pam_systemd_home.so
auth       [success=2 default=ignore]  pam_himmelblau.so    ignore_unknown_user try_first_pass
auth       [success=1 default=bad]     pam_unix.so          try_first_pass nullok
auth       [default=die]               pam_faillock.so      authfail
auth       optional                    pam_permit.so
auth       required                    pam_env.so
auth       required                    pam_faillock.so      authsucc

-account   [success=2 default=ignore]  pam_systemd_home.so
account    [success=1 default=ignore]  pam_himmelblau.so    ignore_unknown_user
account    required                    pam_unix.so
account    optional                    pam_permit.so
account    required                    pam_time.so

-password  [success=2 default=ignore]  pam_systemd_home.so
password   [success=1 default=ignore]  pam_himmelblau.so    ignore_unknown_user
password   required                    pam_unix.so          try_first_pass nullok shadow
password   optional                    pam_permit.so

-session   optional                    pam_systemd_home.so
session    optional                    pam_himmelblau.so
session    required                    pam_limits.so
session    required                    pam_unix.so
session    optional                    pam_permit.so
"""
        
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pam', delete=False) as tmp:
                tmp.write(pam_config)
                tmp_path = tmp.name
            
            result = subprocess.run(
                ["sudo", "cp", tmp_path, str(self.PAM_CONF)],
                capture_output=True
            )
            
            Path(tmp_path).unlink(missing_ok=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"PAM configuration failed: {e}")
            self._restore_file(self.PAM_CONF)
            return False
    
    def install_systemd_services(self) -> bool:
        """
        Install systemd service files
        
        Returns:
            True if successful
        """
        try:
            # Generate service files
            services_dir = Path("/tmp/himmelblau-services")
            
            result = subprocess.run(
                ["python3", str(self.build_dir / "scripts" / "gen_servicefiles.py"),
                 "--out-dir", str(services_dir)],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return False
            
            # Modify for Arch (comment out HSM PIN lines)
            himmelblaud_service = services_dir / "himmelblaud.service"
            
            if himmelblaud_service.exists():
                with open(himmelblaud_service, 'r') as f:
                    content = f.read()
                
                content = content.replace('LoadCredentialEncrypted=', '#LoadCredentialEncrypted=')
                content = content.replace('Environment=HIMMELBLAU_HSM_PIN_PATH=', 
                                        '#Environment=HIMMELBLAU_HSM_PIN_PATH=')
                
                with open(himmelblaud_service, 'w') as f:
                    f.write(content)
            
            # Install services
            subprocess.run(
                ["sudo", "cp", str(services_dir / "himmelblaud.service"),
                 str(self.SYSTEMD_DIR / "himmelblaud.service")],
                check=True
            )
            
            subprocess.run(
                ["sudo", "cp", str(services_dir / "himmelblaud-tasks.service"),
                 str(self.SYSTEMD_DIR / "himmelblaud-tasks.service")],
                check=True
            )
            
            # Install D-Bus service
            subprocess.run(
                ["sudo", "install", "-m", "644",
                 str(self.build_dir / "platform" / "debian" / "com.microsoft.identity.broker1.service"),
                 str(self.DBUS_DIR / "com.microsoft.identity.broker1.service")],
                check=True
            )
            
            # Reload systemd
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            
            return True
            
        except Exception as e:
            print(f"Service installation failed: {e}")
            return False
    
    def create_cache_directories(self) -> bool:
        """
        Create required cache directories
        
        Returns:
            True if successful
        """
        try:
            for cache_dir in self.CACHE_DIRS:
                subprocess.run(
                    ["sudo", "mkdir", "-p", str(cache_dir)],
                    check=True
                )
            return True
        except Exception as e:
            print(f"Cache directory creation failed: {e}")
            return False
    
    def create_himmelblau_config(self, domain: str, grant_sudo: bool = True) -> bool:
        """
        Create Himmelblau configuration file
        
        Args:
            domain: EntraID domain
            grant_sudo: Whether to grant sudo access to EntraID users
            
        Returns:
            True if successful
        """
        local_groups = "users,wheel" if grant_sudo else "users"
        
        config = f"""[global]
# EntraID domain
domains = {domain}

# Local groups for EntraID users
local_groups = {local_groups}

# Home directory attributes
home_attr = CN
home_alias = CN

# Use /etc/skel for new home directories
use_etc_skel = true

# Disable Hello PIN (use MFA)
enable_hello = false

# Enable debug logging
debug = true

# Enable Intune MDM compliance
apply_policy = true
"""
        
        try:
            # Create directory
            subprocess.run(
                ["sudo", "mkdir", "-p", str(self.HIMMELBLAU_CONF_DIR)],
                check=True
            )
            
            # Write config via temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as tmp:
                tmp.write(config)
                tmp_path = tmp.name
            
            result = subprocess.run(
                ["sudo", "cp", tmp_path, str(self.HIMMELBLAU_CONF)],
                capture_output=True
            )
            
            Path(tmp_path).unlink(missing_ok=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Config creation failed: {e}")
            return False
    
    def start_services(self) -> bool:
        """
        Enable and start Himmelblau services
        
        Returns:
            True if successful
        """
        try:
            # Enable services
            subprocess.run(
                ["sudo", "systemctl", "enable", "himmelblaud", "himmelblaud-tasks"],
                check=True,
                timeout=30
            )
            
            # Start main service (tasks service starts via Upholds=)
            subprocess.run(
                ["sudo", "systemctl", "start", "himmelblaud"],
                check=True,
                timeout=30
            )
            
            return True
            
        except Exception as e:
            print(f"Service start failed: {e}")
            return False
    
    def configure_all(self, domain: str, grant_sudo: bool = True) -> bool:
        """
        Complete configuration process
        
        Args:
            domain: EntraID domain
            grant_sudo: Whether to grant sudo access
            
        Returns:
            True if successful
        """
        steps = [
            ("Create cache directories", lambda: self.create_cache_directories()),
            ("Configure NSS", lambda: self.configure_nss()),
            ("Configure PAM", lambda: self.configure_pam()),
            ("Install systemd services", lambda: self.install_systemd_services()),
            ("Create Himmelblau config", lambda: self.create_himmelblau_config(domain, grant_sudo)),
            ("Start services", lambda: self.start_services()),
        ]
        
        for step_name, step_func in steps:
            print(f"  {step_name}...")
            if not step_func():
                print(f"  Failed: {step_name}")
                return False
        
        return True
    
    def rollback(self) -> bool:
        """
        Rollback configuration changes
        
        Returns:
            True if successful
        """
        success = True
        
        # Stop services
        try:
            subprocess.run(["sudo", "systemctl", "stop", "himmelblaud"], timeout=30)
            subprocess.run(["sudo", "systemctl", "disable", "himmelblaud"], timeout=30)
        except:
            pass
        
        # Restore backups
        if not self._restore_file(self.NSS_CONF):
            success = False
        
        if not self._restore_file(self.PAM_CONF):
            success = False
        
        return success

