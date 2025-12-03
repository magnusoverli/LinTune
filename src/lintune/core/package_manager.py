"""
Package manager abstraction for LinTune

Handles package installation across different distributions.
"""

import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from .distro import SupportedDistro


@dataclass
class PackageInstallResult:
    """Result of package installation"""
    success: bool
    packages_installed: list[str]
    packages_failed: list[str]
    output: str
    error: str = ""


class PackageManager(ABC):
    """Abstract base class for package managers"""
    
    @abstractmethod
    def update_repos(self) -> bool:
        """Update package repositories"""
        pass
    
    @abstractmethod
    def install(self, packages: list[str]) -> PackageInstallResult:
        """Install packages"""
        pass
    
    @abstractmethod
    def is_installed(self, package: str) -> bool:
        """Check if package is installed"""
        pass
    
    @abstractmethod
    def remove(self, packages: list[str]) -> bool:
        """Remove packages"""
        pass


class PacmanManager(PackageManager):
    """Package manager for Arch/CachyOS"""
    
    def __init__(self):
        self.cmd = "pacman"
    
    def update_repos(self) -> bool:
        """Update package repositories"""
        try:
            result = subprocess.run(
                ["sudo", self.cmd, "-Sy"],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def install(self, packages: list[str]) -> PackageInstallResult:
        """Install packages"""
        if not packages:
            return PackageInstallResult(True, [], [], "")
        
        try:
            # Use --noconfirm and --needed
            result = subprocess.run(
                ["sudo", self.cmd, "-S", "--noconfirm", "--needed"] + packages,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )
            
            success = result.returncode == 0
            installed = packages if success else []
            failed = [] if success else packages
            
            return PackageInstallResult(
                success=success,
                packages_installed=installed,
                packages_failed=failed,
                output=result.stdout,
                error=result.stderr
            )
            
        except subprocess.TimeoutExpired:
            return PackageInstallResult(
                success=False,
                packages_installed=[],
                packages_failed=packages,
                output="",
                error="Installation timeout"
            )
        except Exception as e:
            return PackageInstallResult(
                success=False,
                packages_installed=[],
                packages_failed=packages,
                output="",
                error=str(e)
            )
    
    def is_installed(self, package: str) -> bool:
        """Check if package is installed"""
        try:
            result = subprocess.run(
                [self.cmd, "-Q", package],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def remove(self, packages: list[str]) -> bool:
        """Remove packages"""
        if not packages:
            return True
        
        try:
            result = subprocess.run(
                ["sudo", self.cmd, "-R", "--noconfirm"] + packages,
                capture_output=True,
                timeout=300
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False


# Package name mapping between distros
PACKAGE_MAP = {
    # Common name -> {distro: package_name}
    "rust": {
        SupportedDistro.ARCH: "rust",
        SupportedDistro.CACHYOS: "rust",
    },
    "cargo": {
        SupportedDistro.ARCH: "cargo",
        SupportedDistro.CACHYOS: "cargo",
    },
    "pkg-config": {
        SupportedDistro.ARCH: "pkg-config",
        SupportedDistro.CACHYOS: "pkg-config",
    },
    "openssl": {
        SupportedDistro.ARCH: "openssl",
        SupportedDistro.CACHYOS: "openssl",
    },
    "sqlite": {
        SupportedDistro.ARCH: "sqlite",
        SupportedDistro.CACHYOS: "sqlite",
    },
    "dbus": {
        SupportedDistro.ARCH: "dbus",
        SupportedDistro.CACHYOS: "dbus",
    },
    "tpm2-tss": {
        SupportedDistro.ARCH: "tpm2-tss",
        SupportedDistro.CACHYOS: "tpm2-tss",
    },
    "git": {
        SupportedDistro.ARCH: "git",
        SupportedDistro.CACHYOS: "git",
    },
    "base-devel": {
        SupportedDistro.ARCH: "base-devel",
        SupportedDistro.CACHYOS: "base-devel",
    },
    "python": {
        SupportedDistro.ARCH: "python",
        SupportedDistro.CACHYOS: "python",
    },
    "cronie": {
        SupportedDistro.ARCH: "cronie",
        SupportedDistro.CACHYOS: "cronie",
    },
    "gdm": {
        SupportedDistro.ARCH: "gdm",
        SupportedDistro.CACHYOS: "gdm",
    },
}


def get_package_manager(distro: SupportedDistro) -> Optional[PackageManager]:
    """
    Factory function to get the appropriate package manager
    
    Args:
        distro: Distribution type
        
    Returns:
        PackageManager instance or None
    """
    if distro in (SupportedDistro.ARCH, SupportedDistro.CACHYOS):
        return PacmanManager()
    
    return None


def map_package_name(common_name: str, distro: SupportedDistro) -> Optional[str]:
    """
    Map common package name to distro-specific name
    
    Args:
        common_name: Common package identifier
        distro: Target distribution
        
    Returns:
        Distro-specific package name or None
    """
    if common_name not in PACKAGE_MAP:
        return common_name  # Return as-is, might work
    
    return PACKAGE_MAP[common_name].get(distro)


def get_himmelblau_dependencies(distro: SupportedDistro) -> list[str]:
    """
    Get list of dependencies needed to build Himmelblau
    
    Args:
        distro: Target distribution
        
    Returns:
        List of package names
    """
    common_deps = [
        "rust", "cargo", "pkg-config", "openssl", 
        "sqlite", "dbus", "tpm2-tss", "git", "base-devel"
    ]
    
    mapped = []
    for dep in common_deps:
        pkg = map_package_name(dep, distro)
        if pkg:
            mapped.append(pkg)
    
    return mapped

