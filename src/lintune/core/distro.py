"""
Distribution detection for LinTune

Detects the current Linux distribution and determines if it's supported.
"""

from enum import Enum
from dataclasses import dataclass
import distro


class SupportedDistro(Enum):
    """Supported Linux distributions"""
    ARCH = "arch"
    CACHYOS = "cachyos"
    UBUNTU = "ubuntu"
    DEBIAN = "debian"
    UNSUPPORTED = "unsupported"


@dataclass
class DistroInfo:
    """Information about the detected distribution"""
    distro_id: str
    name: str
    version: str
    version_codename: str
    supported: SupportedDistro
    package_manager: str
    
    @property
    def is_supported(self) -> bool:
        """Check if this distro is supported"""
        return self.supported != SupportedDistro.UNSUPPORTED
    
    @property
    def display_name(self) -> str:
        """Get friendly display name"""
        return f"{self.name} {self.version}"


class DistroDetector:
    """Detects and validates the current Linux distribution"""
    
    # Mapping of distro IDs to supported distros
    DISTRO_MAP = {
        'arch': SupportedDistro.ARCH,
        'cachyos': SupportedDistro.CACHYOS,
        'ubuntu': SupportedDistro.UBUNTU,
        'debian': SupportedDistro.DEBIAN,
    }
    
    # Package manager for each distro family
    PACKAGE_MANAGERS = {
        SupportedDistro.ARCH: 'pacman',
        SupportedDistro.CACHYOS: 'pacman',
        SupportedDistro.UBUNTU: 'apt',
        SupportedDistro.DEBIAN: 'apt',
    }
    
    def detect(self) -> DistroInfo:
        """
        Detect the current distribution
        
        Returns:
            DistroInfo object with distribution details
        """
        distro_id = distro.id().lower()
        name = distro.name()
        version = distro.version()
        codename = distro.codename()
        
        # Determine if supported
        supported = self.DISTRO_MAP.get(distro_id, SupportedDistro.UNSUPPORTED)
        
        # Get package manager
        pkg_manager = self.PACKAGE_MANAGERS.get(supported, 'unknown')
        
        return DistroInfo(
            distro_id=distro_id,
            name=name,
            version=version,
            version_codename=codename,
            supported=supported,
            package_manager=pkg_manager
        )
    
    def get_distro_icon(self, info: DistroInfo) -> str:
        """
        Get emoji icon for distro (for display)
        
        Args:
            info: DistroInfo object
            
        Returns:
            Emoji icon string
        """
        icons = {
            SupportedDistro.ARCH: "🐧",
            SupportedDistro.CACHYOS: "⚡",
            SupportedDistro.UBUNTU: "🟠",
            SupportedDistro.DEBIAN: "🔴",
            SupportedDistro.UNSUPPORTED: "❓",
        }
        return icons.get(info.supported, "❓")

