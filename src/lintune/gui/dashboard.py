"""
Dashboard view for LinTune

Main overview with system status cards and enrollment options
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ..core.distro import DistroInfo
from ..core.validator import SystemStatus
from .widgets import RefreshButton, StatusDot
from .dialogs import DomainInputDialog, InstallProgressDialog, SudoPasswordDialog


class StatusCard(QFrame):
    """Individual status card widget"""
    
    def __init__(self, title: str, items: list[tuple[str, str, str | bool]]):
        """
        Create a status card
        
        Args:
            title: Card title
            items: List of (label, value, status) tuples where status is:
                   - bool: True='success', False='neutral'
                   - str: 'success', 'warning', 'error', 'info', 'neutral'
        """
        super().__init__()
        self.setProperty("class", "card")
        self.setMaximumHeight(180)
        self.init_ui(title, items)
    
    def init_ui(self, title: str, items: list):
        """Initialize card UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: 600; padding-bottom: 4px;")
        layout.addWidget(title_label)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)
        
        # Status items
        for label, value, status in items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(6)
            
            # Convert bool to status string if needed
            if isinstance(status, bool):
                status_str = 'success' if status else 'neutral'
            else:
                status_str = status
            
            # Status dot - semantic colors
            status_dot = StatusDot(status_str)
            item_layout.addWidget(status_dot)
            
            # Label - use system text color (no semantic coloring)
            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-size: 13px;")
            label_widget.setWordWrap(True)
            item_layout.addWidget(label_widget, 1)
            
            # Value - slightly smaller (no semantic coloring)
            if value:
                value_widget = QLabel(value)
                value_widget.setStyleSheet("font-size: 11px;")
                value_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
                item_layout.addWidget(value_widget)
            
            layout.addLayout(item_layout)
        
        layout.addStretch()


class ActionCard(QFrame):
    """Action card with buttons"""
    
    action_clicked = pyqtSignal(str)
    
    def __init__(self, title: str, description: str, actions: list[tuple[str, str, bool]]):
        """
        Create an action card
        
        Args:
            title: Card title
            description: Card description
            actions: List of (action_id, button_text, is_primary) tuples
        """
        super().__init__()
        self.setProperty("class", "card")
        self.init_ui(title, description, actions)
    
    def init_ui(self, title: str, description: str, actions: list):
        """Initialize card UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Icon + Title
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("ⓘ")
        icon_label.setStyleSheet("font-size: 24px; color: palette(highlight);")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setProperty("class", "card-title")
        title_label.setStyleSheet("font-size: 16px; font-weight: 600; ")
        header_layout.addWidget(title_label, 1)
        
        layout.addLayout(header_layout)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("")
        layout.addWidget(sep)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(" font-size: 14px; line-height: 1.5;")
        layout.addWidget(desc_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        for action_id, text, is_primary in actions:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            if is_primary:
                btn.setProperty("class", "primary")
                btn.setStyleSheet("""
                    background-color: palette(highlight);
                    color: palette(highlighted-text);
                    border: none;
                    border-radius: 4px;
                    padding: 8px 24px;
                    font-size: 14px;
                    font-weight: 600;
                    min-height: 32px;
                """)
            else:
                btn.setProperty("class", "secondary")
                btn.setStyleSheet("""
                    background-color: transparent;
                    color: palette(highlight);
                    border: 1px solid palette(highlight);
                    border-radius: 4px;
                    padding: 8px 24px;
                    font-size: 14px;
                    font-weight: 600;
                    min-height: 32px;
                """)
            
            btn.clicked.connect(lambda checked, aid=action_id: self.action_clicked.emit(aid))
            button_layout.addWidget(btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)


class EnrollmentProgressCard(QFrame):
    """Card showing enrollment progress"""
    
    def __init__(self, status: SystemStatus):
        super().__init__()
        self.setProperty("class", "card")
        self.setMaximumHeight(180)
        self.init_ui(status)
    
    def init_ui(self, status: SystemStatus):
        """Initialize card UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel("Device Enrollment")
        title_label.setStyleSheet("font-size: 14px; font-weight: 600;  padding-bottom: 4px;")
        layout.addWidget(title_label)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(" max-height: 1px;")
        layout.addWidget(sep)
        
        # Progress dots (visual indicator)
        steps = [
            ("Check", not status.is_fully_configured),
            ("Build", status.himmelblau_installed),
            ("Config", status.nss_configured and status.pam_configured),
            ("Enroll", status.is_fully_configured),
        ]
        
        dots_layout = QHBoxLayout()
        dots_layout.setSpacing(0)
        for i, (step_name, completed) in enumerate(steps):
            # Semantic colors: green for done, gray for pending
            dot = "●" if completed else "○"
            dot_color = StatusDot.COLORS['success'] if completed else StatusDot.COLORS['neutral']
            
            step_layout = QVBoxLayout()
            step_layout.setSpacing(2)
            
            dot_label = QLabel(dot)
            dot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot_label.setStyleSheet(f"color: {dot_color}; font-size: 16px;")
            step_layout.addWidget(dot_label)
            
            # Text uses palette color (no semantic color for text)
            name_label = QLabel(step_name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet("font-size: 9px;")
            step_layout.addWidget(name_label)
            
            dots_layout.addLayout(step_layout)
            
            # Connector line (except for last)
            if i < len(steps) - 1:
                line = QLabel("───")
                line.setAlignment(Qt.AlignmentFlag.AlignCenter)
                line_color = dot_color if completed else StatusDot.COLORS['neutral']
                line.setStyleSheet(f"color: {line_color}; font-size: 10px;")
                dots_layout.addWidget(line)
        
        layout.addLayout(dots_layout)
        
        # Status text
        status_label = QLabel(status.enrollment_status)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet(" font-size: 13px; padding-top: 6px;")
        layout.addWidget(status_label)
        
        layout.addStretch()


class DashboardView(QWidget):
    """Main dashboard view"""
    
    refresh_requested = pyqtSignal()
    install_requested = pyqtSignal(str)  # mode: "auto", "manual", "advanced"
    navigate_requested = pyqtSignal(int)  # Navigate to view by index
    
    def __init__(self, distro_info: DistroInfo, system_status: SystemStatus):
        super().__init__()
        self.distro_info = distro_info
        self.system_status = system_status
        self.init_ui()
    
    def init_ui(self):
        """Initialize dashboard UI"""
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Dashboard")
        header_label.setStyleSheet("font-size: 24px; font-weight: 600; ")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Last checked timestamp (updates on refresh)
        from datetime import datetime
        self.checked_label = QLabel(f"Checked: {datetime.now().strftime('%H:%M:%S')}")
        self.checked_label.setStyleSheet("font-size: 12px;  padding-right: 12px;")
        header_layout.addWidget(self.checked_label)
        
        # Refresh button in header
        self.refresh_btn = RefreshButton()
        self.refresh_btn.refresh_requested.connect(self.on_refresh_clicked)
        header_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Content layout (no scroll area - responsive)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(16)
        
        # Top row: 3 cards (responsive grid)
        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        
        # Enrollment progress card
        self.enrollment_card = EnrollmentProgressCard(self.system_status)
        self.enrollment_card.setMinimumWidth(200)
        top_row.addWidget(self.enrollment_card, 1)
        
        # System status card
        system_items = [
            ("Operating System", self.distro_info.display_name, True),
            ("Supported", "Yes" if self.distro_info.is_supported else "No", self.distro_info.is_supported),
            ("Display Manager", self.system_status.current_display_manager or "None", 
             self.system_status.gdm_enabled),
        ]
        self.system_card = StatusCard("System", system_items)
        self.system_card.setMinimumWidth(200)
        top_row.addWidget(self.system_card, 1)
        
        # Ready status card
        ready_items = [
            ("GDM Installed", "", self.system_status.gdm_installed),
            ("Dependencies", "", self.system_status.build_deps_installed),
            ("Himmelblau", self.system_status.himmelblau_version or "", 
             self.system_status.himmelblau_installed),
        ]
        self.ready_card = StatusCard("Status", ready_items)
        self.ready_card.setMinimumWidth(200)
        top_row.addWidget(self.ready_card, 1)
        
        content_layout.addLayout(top_row)
        
        # Action card or status message
        if not self.system_status.is_fully_configured:
            action_desc = (
                "Configure this device for EntraID authentication and Intune management. "
                "This will install and configure the necessary components for enterprise "
                "device enrollment."
            )
            
            actions = [
                ("auto", "Begin Enrollment", True),
                ("advanced", "Advanced Setup", False),
            ]
            
            self.action_card = ActionCard("Get Started", action_desc, actions)
            self.action_card.action_clicked.connect(self.start_enrollment)
            self.action_card.setMaximumHeight(200)
            content_layout.addWidget(self.action_card)
        else:
            # Already configured - show quick info row
            info_row = QHBoxLayout()
            info_row.setSpacing(16)
            
            # Intune Status card (use centralized detection)
            intune = self.system_status.intune_status
            
            # Determine enrollment status badge
            if intune and intune.is_enrolled:
                enrollment_status = 'success'
            elif intune and 'limit' in intune.display_enrollment.lower():
                enrollment_status = 'warning'
            else:
                enrollment_status = 'neutral'
            
            # Determine compliance status badge  
            if intune and intune.is_compliant:
                compliance_status = 'success'
            elif intune and intune.display_compliance == 'N/A':
                compliance_status = 'neutral'
            else:
                compliance_status = 'warning'
            
            intune_items = [
                ("Enrollment", intune.display_enrollment if intune else "Unknown", enrollment_status),
                ("Compliance", intune.display_compliance if intune else "Unknown", compliance_status),
                ("Service", intune.last_activity if intune and intune.last_activity else "Unknown", 'success'),
            ]
            intune_card = StatusCard("Intune Status", intune_items)
            intune_card.setMinimumWidth(200)
            info_row.addWidget(intune_card, 1)
            
            # Domain & User card
            domain_items = [
                ("Domain", self.system_status.configured_domain or "Unknown", True),
                ("Service", "Running" if self.system_status.himmelblaud_running else "Stopped",
                 self.system_status.himmelblaud_running),
                ("Policy", "Enabled" if self.system_status.config_exists else "Disabled",
                 self.system_status.config_exists),
            ]
            domain_card = StatusCard("Configuration", domain_items)
            domain_card.setMinimumWidth(200)
            info_row.addWidget(domain_card, 1)
            
            # Quick Actions card
            actions_frame = QFrame()
            actions_frame.setProperty("class", "card")
            actions_frame.setMaximumHeight(180)
            actions_frame.setMinimumWidth(200)
            actions_layout = QVBoxLayout(actions_frame)
            actions_layout.setSpacing(8)
            
            actions_title = QLabel("Quick Actions")
            actions_title.setStyleSheet("font-size: 14px; font-weight: 600;  padding-bottom: 4px;")
            actions_layout.addWidget(actions_title)
            
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(" max-height: 1px;")
            actions_layout.addWidget(sep)
            
            # Action buttons with handlers
            action_btn_style = """
                QPushButton {
                    background-color: transparent;
                    color: palette(highlight);
                    border: none;
                    text-align: left;
                    padding: 6px 8px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: palette(midlight);
                    border-radius: 4px;
                }
            """
            
            # Sync Now button
            sync_btn = QPushButton("🔄  Sync Now")
            sync_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            sync_btn.setStyleSheet(action_btn_style)
            sync_btn.clicked.connect(self.on_sync_clicked)
            actions_layout.addWidget(sync_btn)
            
            # View Logs button
            logs_btn = QPushButton("📄  View Logs")
            logs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            logs_btn.setStyleSheet(action_btn_style)
            logs_btn.clicked.connect(lambda: self.navigate_requested.emit(3))  # Logs view index
            actions_layout.addWidget(logs_btn)
            
            # Check Status button (go to Device view)
            status_btn = QPushButton("✓  Check Status")
            status_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            status_btn.setStyleSheet(action_btn_style)
            status_btn.clicked.connect(lambda: self.navigate_requested.emit(1))  # Device view index
            actions_layout.addWidget(status_btn)
            
            actions_layout.addStretch()
            info_row.addWidget(actions_frame, 1)
            
            content_layout.addLayout(info_row)
        
        # Add stretch to push content to top
        content_layout.addStretch(1)
        
        main_layout.addLayout(content_layout, 1)
    
    def on_refresh_clicked(self):
        """Handle refresh button click"""
        self.refresh_btn.start_refresh()
        self.refresh_requested.emit()
    
    def on_sync_clicked(self):
        """Handle Sync Now button click - uses native aad-tool cache-clear"""
        from ..core.validator import SystemValidator
        from PyQt6.QtWidgets import QMessageBox
        
        # Show loading state
        self.refresh_btn.start_refresh()
        
        # Clear cache using native aad-tool
        validator = SystemValidator()
        success, message = validator.clear_cache()
        
        if success:
            # Refresh status after cache clear
            self.refresh_requested.emit()
        else:
            # Show error but still refresh to show current state
            self.refresh_btn.finish_refresh()
            QMessageBox.warning(
                self,
                "Cache Clear",
                f"Cache clear completed with message:\n{message}"
            )
    
    def update_status(self, system_status: SystemStatus):
        """Update the dashboard with new system status"""
        from datetime import datetime
        self.system_status = system_status
        # Update checked timestamp
        self.checked_label.setText(f"Checked: {datetime.now().strftime('%H:%M:%S')}")
        # Finish refresh button animation
        self.refresh_btn.finish_refresh()
        print(f"Dashboard updated: {system_status.enrollment_status}")
    
    def start_enrollment(self, mode: str):
        """Start the enrollment process"""
        print(f"[DEBUG] start_enrollment called with mode: {mode}")
        if mode == "auto":
            # First, show sudo password dialog
            print("[DEBUG] Showing sudo password dialog...")
            sudo_dialog = SudoPasswordDialog(self)
            result = sudo_dialog.exec()
            print(f"[DEBUG] Sudo dialog result: {result}")
            if result != SudoPasswordDialog.DialogCode.Accepted:
                print("[DEBUG] Sudo dialog cancelled")
                return  # User cancelled
            
            print("[DEBUG] Sudo password validated, showing domain dialog...")
            # Show domain dialog
            dialog = DomainInputDialog(self)
            result = dialog.exec()
            print(f"[DEBUG] Domain dialog result: {result}, domain: {dialog.domain}")
            if result == DomainInputDialog.DialogCode.Accepted:
                print(f"[DEBUG] Starting installation for domain: {dialog.domain}")
                # Start installation
                progress_dialog = InstallProgressDialog(
                    dialog.domain, 
                    dialog.grant_sudo, 
                    self
                )
                progress_dialog.exec()
                
                # Refresh status after installation
                self.refresh_requested.emit()
            else:
                print("[DEBUG] Domain dialog cancelled or rejected")

