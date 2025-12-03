"""
Himmelblau builder for LinTune

Handles cloning, building, and installing Himmelblau components.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum


class BuildStatus(Enum):
    """Build status states"""
    NOT_STARTED = "not_started"
    CLONING = "cloning"
    BUILDING = "building"
    INSTALLING = "installing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BuildProgress:
    """Build progress information"""
    status: BuildStatus
    message: str
    progress: int = 0  # 0-100
    current_step: int = 0
    total_steps: int = 5


class HimmelblauBuilder:
    """Builds and installs Himmelblau from source"""
    
    REPO_URL = "https://github.com/himmelblau-idm/himmelblau"
    BUILD_DIR = Path("/tmp/himmelblau")
    
    # Binary paths
    BINARIES = {
        "himmelblaud": "/usr/sbin/himmelblaud",
        "himmelblaud_tasks": "/usr/sbin/himmelblaud_tasks",
        "aad-tool": "/usr/bin/aad-tool",
        "broker": "/usr/sbin/broker",
        "linux-entra-sso": "/usr/bin/linux-entra-sso",
        "libpam_himmelblau.so": "/usr/lib/security/pam_himmelblau.so",
        "libnss_himmelblau.so": "/usr/lib/libnss_himmelblau.so.2",
    }
    
    def __init__(self, progress_callback: Optional[Callable[[BuildProgress], None]] = None):
        """
        Initialize builder
        
        Args:
            progress_callback: Optional callback for progress updates
        """
        self.progress_callback = progress_callback
        self.current_progress = BuildProgress(BuildStatus.NOT_STARTED, "Ready", 0, 0, 5)
    
    def _update_progress(self, status: BuildStatus, message: str, step: int = None):
        """Update and report progress"""
        if step is not None:
            self.current_progress.current_step = step
        
        self.current_progress.status = status
        self.current_progress.message = message
        self.current_progress.progress = int((self.current_progress.current_step / 
                                              self.current_progress.total_steps) * 100)
        
        if self.progress_callback:
            self.progress_callback(self.current_progress)
    
    def clone_repo(self) -> bool:
        """
        Clone Himmelblau repository
        
        Returns:
            True if successful
        """
        self._update_progress(BuildStatus.CLONING, "Cloning repository...", 1)
        
        # Remove old build dir
        if self.BUILD_DIR.exists():
            try:
                shutil.rmtree(self.BUILD_DIR)
            except Exception as e:
                self._update_progress(BuildStatus.FAILED, f"Failed to clean build dir: {e}")
                return False
        
        try:
            result = subprocess.run(
                ["git", "clone", self.REPO_URL, str(self.BUILD_DIR)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )
            
            if result.returncode != 0:
                self._update_progress(BuildStatus.FAILED, f"Clone failed: {result.stderr}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            self._update_progress(BuildStatus.FAILED, "Clone timeout")
            return False
        except Exception as e:
            self._update_progress(BuildStatus.FAILED, f"Clone error: {e}")
            return False
    
    def build(self) -> bool:
        """
        Build Himmelblau with cargo
        
        Returns:
            True if successful
        """
        self._update_progress(BuildStatus.BUILDING, "Building Himmelblau (this may take 2-5 minutes)...", 2)
        
        if not self.BUILD_DIR.exists():
            self._update_progress(BuildStatus.FAILED, "Build directory not found")
            return False
        
        try:
            # Build with cargo
            env = os.environ.copy()
            env["HIMMELBLAU_ALLOW_MISSING_SELINUX"] = "1"
            
            process = subprocess.Popen(
                ["cargo", "build", "--release"],
                cwd=str(self.BUILD_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Monitor output
            for line in process.stdout:
                if "Compiling" in line:
                    # Extract package being compiled
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        pkg = parts[1]
                        self._update_progress(BuildStatus.BUILDING, f"Compiling {pkg}...")
            
            process.wait(timeout=600)  # 10 minutes
            
            if process.returncode != 0:
                self._update_progress(BuildStatus.FAILED, "Build failed")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            self._update_progress(BuildStatus.FAILED, "Build timeout")
            return False
        except Exception as e:
            self._update_progress(BuildStatus.FAILED, f"Build error: {e}")
            return False
    
    def install_binaries(self) -> bool:
        """
        Install built binaries to system paths
        
        Returns:
            True if successful
        """
        self._update_progress(BuildStatus.INSTALLING, "Installing binaries...", 3)
        
        release_dir = self.BUILD_DIR / "target" / "release"
        
        if not release_dir.exists():
            self._update_progress(BuildStatus.FAILED, "Release directory not found")
            return False
        
        try:
            for binary, dest_path in self.BINARIES.items():
                src = release_dir / binary
                
                if not src.exists():
                    self._update_progress(BuildStatus.FAILED, f"Binary not found: {binary}")
                    return False
                
                # Install with sudo
                result = subprocess.run(
                    ["sudo", "install", "-m", "755", str(src), dest_path],
                    capture_output=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    self._update_progress(BuildStatus.FAILED, f"Failed to install {binary}")
                    return False
            
            return True
            
        except Exception as e:
            self._update_progress(BuildStatus.FAILED, f"Install error: {e}")
            return False
    
    def cleanup(self) -> bool:
        """
        Remove build directory
        
        Returns:
            True if successful
        """
        self._update_progress(BuildStatus.INSTALLING, "Cleaning up...", 4)
        
        try:
            if self.BUILD_DIR.exists():
                shutil.rmtree(self.BUILD_DIR)
            return True
        except Exception as e:
            # Non-critical error
            print(f"Warning: Failed to cleanup: {e}")
            return True
    
    def build_and_install(self) -> bool:
        """
        Complete build process: clone, build, install, cleanup
        
        Returns:
            True if successful
        """
        steps = [
            ("Clone repository", self.clone_repo),
            ("Build binaries", self.build),
            ("Install binaries", self.install_binaries),
            ("Cleanup", self.cleanup),
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                return False
        
        self._update_progress(BuildStatus.COMPLETED, "Installation complete!", 5)
        return True
    
    def is_installed(self) -> bool:
        """
        Check if Himmelblau is already installed
        
        Returns:
            True if installed
        """
        return Path("/usr/sbin/himmelblaud").exists()
    
    def get_version(self) -> Optional[str]:
        """
        Get installed Himmelblau version
        
        Returns:
            Version string or None
        """
        try:
            result = subprocess.run(
                ["/usr/sbin/himmelblaud", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return None

