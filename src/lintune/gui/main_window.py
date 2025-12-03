"""
Main application window for LinTune

Microsoft Intune Portal-inspired interface with sidebar navigation
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QStatusBar, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .sidebar import Sidebar
from .dashboard import DashboardView
from .devices_view import DevicesView
from .settings_view import SettingsView
from .logs_view import LogsView
from ..core.distro import DistroDetector
from ..core.validator import SystemValidator


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signals
    status_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Initialize system components
        self.distro_detector = DistroDetector()
        self.system_validator = SystemValidator()
        
        # Detect system on startup
        self.distro_info = self.distro_detector.detect()
        self.system_status = self.system_validator.validate()
        
        # Setup UI
        self.init_ui()
        self.load_stylesheet()
        
        # Initial status
        self.update_status(f"Ready - {self.distro_info.display_name}")
    
    def init_ui(self):
        """Initialize the user interface"""
        
        # Window properties
        self.setWindowTitle("LinTune - EntraID & Intune Setup")
        self.setMinimumSize(960, 600)
        self.resize(1280, 720)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout (horizontal: sidebar + content)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.navigation_changed.connect(self.on_navigation_changed)
        main_layout.addWidget(self.sidebar)
        
        # Content area (stacked widget for different views)
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentArea")
        main_layout.addWidget(self.content_stack)
        
        # Create views
        self.dashboard_view = DashboardView(self.distro_info, self.system_status)
        self.dashboard_view.refresh_requested.connect(self.refresh_status)
        self.dashboard_view.install_requested.connect(self.on_install_requested)
        self.dashboard_view.navigate_requested.connect(self.navigate_to_view)
        
        # Add views to stack
        self.content_stack.addWidget(self.dashboard_view)
        
        # Devices view
        self.devices_view = DevicesView()
        self.content_stack.addWidget(self.devices_view)
        
        # Settings view
        self.settings_view = SettingsView()
        self.settings_view.config_changed.connect(self.refresh_status)
        self.content_stack.addWidget(self.settings_view)
        
        # Logs view
        self.logs_view = LogsView()
        self.content_stack.addWidget(self.logs_view)
        
        # About view
        about_widget = QWidget()
        about_layout = QVBoxLayout(about_widget)
        about_layout.setContentsMargins(24, 24, 24, 24)
        
        about_title = QLabel("About LinTune")
        about_title.setStyleSheet("font-size: 24px; font-weight: 600; ")
        about_layout.addWidget(about_title)
        
        about_text = QLabel(
            "LinTune v0.1.0\n\n"
            "EntraID & Intune Setup for Linux\n\n"
            "A cross-distribution tool for enrolling Linux devices\n"
            "in Microsoft EntraID and Intune MDM.\n\n"
            "Supported distributions:\n"
            "• Arch Linux\n"
            "• CachyOS\n"
            "• Ubuntu (coming soon)\n"
            "• Debian (coming soon)\n\n"
            "Built with Python and PyQt6\n"
            "Using Himmelblau for EntraID integration"
        )
        about_text.setStyleSheet("font-size: 14px;  line-height: 1.6;")
        about_text.setWordWrap(True)
        about_layout.addWidget(about_text)
        about_layout.addStretch()
        
        self.content_stack.addWidget(about_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status bar labels
        self.status_label = QLabel("Ready")
        self.version_label = QLabel("v0.1.0")
        self.distro_label = QLabel(f"⚡ {self.distro_info.name}")
        
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addPermanentWidget(self.version_label)
        self.status_bar.addPermanentWidget(QLabel("|"))
        self.status_bar.addPermanentWidget(self.distro_label)
    
    def load_stylesheet(self):
        """Load minimal stylesheet (relies on system theme)"""
        try:
            from pathlib import Path
            
            current_dir = Path(__file__).parent
            stylesheet_path = current_dir.parent / 'resources' / 'styles' / 'fluent.qss'
            
            with open(stylesheet_path, 'r') as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Warning: Could not load stylesheet: {e}")
    
    def on_navigation_changed(self, index: int):
        """Handle navigation changes from sidebar"""
        self.content_stack.setCurrentIndex(index)
        
        # Update status based on view
        view_names = ["Dashboard", "Device", "Settings", "Logs", "About"]
        if index < len(view_names):
            self.update_status(f"{view_names[index]} - {self.distro_info.display_name}")
    
    def navigate_to_view(self, index: int):
        """Programmatically navigate to a view (used by quick actions)"""
        # Update sidebar selection
        btn = self.sidebar.button_group.button(index)
        if btn:
            btn.setChecked(True)
        # Switch view
        self.on_navigation_changed(index)
    
    def refresh_status(self):
        """Refresh system status"""
        self.update_status("Refreshing system status...")
        
        # Re-validate system
        self.system_status = self.system_validator.validate()
        
        # Update dashboard
        self.dashboard_view.update_status(self.system_status)
        
        self.update_status(f"Ready - {self.distro_info.display_name}")
    
    def on_install_requested(self, mode: str):
        """Handle installation request"""
        self.update_status(f"Installation requested: {mode}")
        # TODO: Implement installation flow
        print(f"Install requested: {mode}")
    
    def update_status(self, message: str):
        """Update status bar message"""
        self.status_label.setText(message)
        self.status_changed.emit(message)

