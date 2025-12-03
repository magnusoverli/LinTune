"""
Installation orchestrator for LinTune

Manages the complete installation workflow, combining all components.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable
from pathlib import Path

from .distro import DistroDetector, DistroInfo, SupportedDistro
from .validator import SystemValidator, SystemStatus
from .package_manager import get_package_manager, get_himmelblau_dependencies, PackageManager
from .himmelblau import HimmelblauBuilder, BuildStatus, BuildProgress
from .configurator import SystemConfigurator


class InstallStep(Enum):
    """Installation steps"""
    CHECK_SYSTEM = "check_system"
    INSTALL_GDM = "install_gdm"
    INSTALL_DEPS = "install_deps"
    BUILD_HIMMELBLAU = "build_himmelblau"
    CONFIGURE_SYSTEM = "configure_system"
    START_SERVICES = "start_services"
    VERIFY = "verify"


class InstallStatus(Enum):
    """Installation status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class InstallProgress:
    """Installation progress information"""
    status: InstallStatus
    current_step: InstallStep
    step_number: int
    total_steps: int
    message: str
    progress_percent: int = 0
    error: Optional[str] = None


class Installer:
    """Orchestrates the complete installation process"""
    
    TOTAL_STEPS = 7
    
    def __init__(self, progress_callback: Optional[Callable[[InstallProgress], None]] = None):
        """
        Initialize installer
        
        Args:
            progress_callback: Optional callback for progress updates
        """
        self.progress_callback = progress_callback
        
        # Initialize components
        self.distro_detector = DistroDetector()
        self.validator = SystemValidator()
        self.distro_info: Optional[DistroInfo] = None
        self.system_status: Optional[SystemStatus] = None
        self.package_manager: Optional[PackageManager] = None
        self.builder: Optional[HimmelblauBuilder] = None
        self.configurator: Optional[SystemConfigurator] = None
        
        # State
        self.current_progress = InstallProgress(
            status=InstallStatus.NOT_STARTED,
            current_step=InstallStep.CHECK_SYSTEM,
            step_number=0,
            total_steps=self.TOTAL_STEPS,
            message="Ready"
        )
    
    def _update_progress(self, step: InstallStep, step_num: int, message: str, 
                         status: InstallStatus = InstallStatus.IN_PROGRESS,
                         error: str = None):
        """Update and report progress"""
        self.current_progress = InstallProgress(
            status=status,
            current_step=step,
            step_number=step_num,
            total_steps=self.TOTAL_STEPS,
            message=message,
            progress_percent=int((step_num / self.TOTAL_STEPS) * 100),
            error=error
        )
        
        if self.progress_callback:
            self.progress_callback(self.current_progress)
    
    def _on_build_progress(self, build_progress: BuildProgress):
        """Handle build progress updates"""
        self._update_progress(
            InstallStep.BUILD_HIMMELBLAU,
            4,
            build_progress.message
        )
    
    def check_system(self) -> bool:
        """
        Step 1: Check system compatibility
        
        Returns:
            True if system is compatible
        """
        self._update_progress(InstallStep.CHECK_SYSTEM, 1, "Checking system...")
        
        # Detect distro
        self.distro_info = self.distro_detector.detect()
        
        if not self.distro_info.is_supported:
            self._update_progress(
                InstallStep.CHECK_SYSTEM, 1,
                f"Unsupported distribution: {self.distro_info.name}",
                InstallStatus.FAILED,
                "Distribution not supported"
            )
            return False
        
        # Get package manager
        self.package_manager = get_package_manager(self.distro_info.supported)
        
        if not self.package_manager:
            self._update_progress(
                InstallStep.CHECK_SYSTEM, 1,
                "No package manager available",
                InstallStatus.FAILED,
                "Package manager not found"
            )
            return False
        
        # Validate system
        self.system_status = self.validator.validate()
        
        # Check if already installed
        if self.system_status.is_fully_configured:
            self._update_progress(
                InstallStep.CHECK_SYSTEM, 1,
                "System already configured",
                InstallStatus.COMPLETED
            )
            return True
        
        self._update_progress(InstallStep.CHECK_SYSTEM, 1, 
                            f"System compatible: {self.distro_info.display_name}")
        return True
    
    def install_gdm(self) -> bool:
        """
        Step 2: Install and enable GDM
        
        Returns:
            True if successful
        """
        self._update_progress(InstallStep.INSTALL_GDM, 2, "Checking GDM...")
        
        if self.system_status.gdm_enabled:
            self._update_progress(InstallStep.INSTALL_GDM, 2, "GDM already enabled")
            return True
        
        if not self.system_status.gdm_installed:
            self._update_progress(InstallStep.INSTALL_GDM, 2, "Installing GDM...")
            
            result = self.package_manager.install(["gdm"])
            if not result.success:
                self._update_progress(
                    InstallStep.INSTALL_GDM, 2,
                    "Failed to install GDM",
                    InstallStatus.FAILED,
                    result.error
                )
                return False
        
        # Enable GDM
        self._update_progress(InstallStep.INSTALL_GDM, 2, "Enabling GDM...")
        
        import subprocess
        try:
            subprocess.run(["sudo", "systemctl", "enable", "gdm"], check=True, timeout=30)
        except Exception as e:
            self._update_progress(
                InstallStep.INSTALL_GDM, 2,
                "Failed to enable GDM",
                InstallStatus.FAILED,
                str(e)
            )
            return False
        
        self._update_progress(InstallStep.INSTALL_GDM, 2, "GDM configured")
        return True
    
    def install_dependencies(self) -> bool:
        """
        Step 3: Install build dependencies
        
        Returns:
            True if successful
        """
        self._update_progress(InstallStep.INSTALL_DEPS, 3, "Installing dependencies...")
        
        deps = get_himmelblau_dependencies(self.distro_info.supported)
        
        # Check what's already installed
        missing = [dep for dep in deps if not self.package_manager.is_installed(dep)]
        
        if not missing:
            self._update_progress(InstallStep.INSTALL_DEPS, 3, "All dependencies installed")
            return True
        
        self._update_progress(InstallStep.INSTALL_DEPS, 3, 
                            f"Installing {len(missing)} packages...")
        
        result = self.package_manager.install(missing)
        
        if not result.success:
            self._update_progress(
                InstallStep.INSTALL_DEPS, 3,
                "Failed to install dependencies",
                InstallStatus.FAILED,
                result.error
            )
            return False
        
        self._update_progress(InstallStep.INSTALL_DEPS, 3, "Dependencies installed")
        return True
    
    def build_himmelblau(self) -> bool:
        """
        Step 4: Build and install Himmelblau
        
        Returns:
            True if successful
        """
        self._update_progress(InstallStep.BUILD_HIMMELBLAU, 4, "Building Himmelblau...")
        
        # Check if already installed
        if self.system_status.himmelblau_installed:
            self._update_progress(InstallStep.BUILD_HIMMELBLAU, 4, "Himmelblau already installed")
            return True
        
        # Create builder with progress callback
        self.builder = HimmelblauBuilder(progress_callback=self._on_build_progress)
        
        # Run build
        success = self.builder.build_and_install()
        
        if not success:
            self._update_progress(
                InstallStep.BUILD_HIMMELBLAU, 4,
                "Build failed",
                InstallStatus.FAILED,
                self.builder.current_progress.message
            )
            return False
        
        self._update_progress(InstallStep.BUILD_HIMMELBLAU, 4, "Himmelblau installed")
        return True
    
    def configure_system(self, domain: str, grant_sudo: bool = True) -> bool:
        """
        Step 5: Configure system (NSS, PAM, services)
        
        Args:
            domain: EntraID domain
            grant_sudo: Grant sudo to EntraID users
            
        Returns:
            True if successful
        """
        self._update_progress(InstallStep.CONFIGURE_SYSTEM, 5, "Configuring system...")
        
        self.configurator = SystemConfigurator()
        
        # Create directories
        self._update_progress(InstallStep.CONFIGURE_SYSTEM, 5, "Creating directories...")
        if not self.configurator.create_cache_directories():
            self._update_progress(
                InstallStep.CONFIGURE_SYSTEM, 5,
                "Failed to create directories",
                InstallStatus.FAILED
            )
            return False
        
        # Configure NSS
        self._update_progress(InstallStep.CONFIGURE_SYSTEM, 5, "Configuring NSS...")
        if not self.configurator.configure_nss():
            self._update_progress(
                InstallStep.CONFIGURE_SYSTEM, 5,
                "Failed to configure NSS",
                InstallStatus.FAILED
            )
            return False
        
        # Configure PAM
        self._update_progress(InstallStep.CONFIGURE_SYSTEM, 5, "Configuring PAM...")
        if not self.configurator.configure_pam():
            self._update_progress(
                InstallStep.CONFIGURE_SYSTEM, 5,
                "Failed to configure PAM",
                InstallStatus.FAILED
            )
            return False
        
        # Install services
        self._update_progress(InstallStep.CONFIGURE_SYSTEM, 5, "Installing services...")
        if not self.configurator.install_systemd_services():
            self._update_progress(
                InstallStep.CONFIGURE_SYSTEM, 5,
                "Failed to install services",
                InstallStatus.FAILED
            )
            return False
        
        # Create config
        self._update_progress(InstallStep.CONFIGURE_SYSTEM, 5, "Creating configuration...")
        if not self.configurator.create_himmelblau_config(domain, grant_sudo):
            self._update_progress(
                InstallStep.CONFIGURE_SYSTEM, 5,
                "Failed to create configuration",
                InstallStatus.FAILED
            )
            return False
        
        self._update_progress(InstallStep.CONFIGURE_SYSTEM, 5, "System configured")
        return True
    
    def start_services(self) -> bool:
        """
        Step 6: Start Himmelblau services
        
        Returns:
            True if successful
        """
        self._update_progress(InstallStep.START_SERVICES, 6, "Starting services...")
        
        if self.configurator and self.configurator.start_services():
            self._update_progress(InstallStep.START_SERVICES, 6, "Services started")
            return True
        
        self._update_progress(
            InstallStep.START_SERVICES, 6,
            "Failed to start services",
            InstallStatus.FAILED
        )
        return False
    
    def verify(self) -> bool:
        """
        Step 7: Verify installation
        
        Returns:
            True if successful
        """
        self._update_progress(InstallStep.VERIFY, 7, "Verifying installation...")
        
        # Re-validate system
        self.system_status = self.validator.validate()
        
        if self.system_status.is_fully_configured:
            self._update_progress(
                InstallStep.VERIFY, 7,
                "Installation complete!",
                InstallStatus.COMPLETED
            )
            return True
        
        self._update_progress(
            InstallStep.VERIFY, 7,
            "Verification failed",
            InstallStatus.FAILED,
            f"Status: {self.system_status.enrollment_status}"
        )
        return False
    
    def install(self, domain: str, grant_sudo: bool = True) -> bool:
        """
        Run complete installation
        
        Args:
            domain: EntraID domain
            grant_sudo: Grant sudo to EntraID users
            
        Returns:
            True if successful
        """
        steps = [
            ("Check system", self.check_system),
            ("Install GDM", self.install_gdm),
            ("Install dependencies", self.install_dependencies),
            ("Build Himmelblau", self.build_himmelblau),
            ("Configure system", lambda: self.configure_system(domain, grant_sudo)),
            ("Start services", self.start_services),
            ("Verify installation", self.verify),
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                return False
        
        return True
    
    def rollback(self) -> bool:
        """
        Rollback installation
        
        Returns:
            True if successful
        """
        if self.configurator:
            return self.configurator.rollback()
        return False

