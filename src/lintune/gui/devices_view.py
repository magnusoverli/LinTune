"""
Devices view for LinTune

Shows device information and enrollment status.
"""

import subprocess
import socket
import platform
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt

from ..core.validator import SystemValidator
from .widgets import RefreshButton, StatusDot


class DevicesView(QWidget):
    """Device information view"""
    
    def __init__(self):
        super().__init__()
        self.validator = SystemValidator()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Device")
        title.setStyleSheet("font-size: 24px; font-weight: 600; ")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.refresh_btn = RefreshButton()
        self.refresh_btn.refresh_requested.connect(self.on_refresh_clicked)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Main content - two columns
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left column
        left_column = QVBoxLayout()
        left_column.setSpacing(20)
        
        # Device Info Section
        left_column.addWidget(self._create_section_header("DEVICE INFORMATION"))
        self.device_grid = self._create_info_grid()
        left_column.addLayout(self.device_grid)
        
        left_column.addSpacing(10)
        
        # Network Section
        left_column.addWidget(self._create_section_header("NETWORK"))
        self.network_grid = self._create_info_grid()
        left_column.addLayout(self.network_grid)
        
        left_column.addStretch()
        content_layout.addLayout(left_column, 1)
        
        # Right column
        right_column = QVBoxLayout()
        right_column.setSpacing(20)
        
        # Enrollment Section
        right_column.addWidget(self._create_section_header("ENROLLMENT STATUS"))
        self.enrollment_grid = self._create_info_grid()
        right_column.addLayout(self.enrollment_grid)
        
        right_column.addSpacing(10)
        
        # Compliance Section
        right_column.addWidget(self._create_section_header("COMPLIANCE"))
        self.compliance_grid = self._create_info_grid()
        right_column.addLayout(self.compliance_grid)
        
        right_column.addStretch()
        content_layout.addLayout(right_column, 1)
        
        layout.addLayout(content_layout, 1)
        
        # Load data
        self.refresh()
    
    def _create_section_header(self, text: str) -> QLabel:
        """Create a blue uppercase section header"""
        label = QLabel(text)
        label.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            color: palette(highlight);
            letter-spacing: 1px;
            padding-bottom: 8px;
            border-bottom: 1px solid palette(mid);
        """)
        return label
    
    def _create_info_grid(self) -> QGridLayout:
        """Create an info grid layout"""
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setColumnStretch(0, 0)  # Label column - fit content
        grid.setColumnStretch(1, 1)  # Value column - stretch
        return grid
    
    def _clear_grid(self, grid: QGridLayout):
        """Clear all widgets from a grid"""
        while grid.count():
            item = grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _add_info_row(self, grid: QGridLayout, row: int, label: str, value: str, 
                      status: str = None) -> int:
        """
        Add an info row to the grid
        
        Args:
            grid: Target grid layout
            row: Row index
            label: Label text
            value: Value text
            status: Optional status indicator ('success', 'warning', 'error', 'pending')
        
        Returns:
            Next row index
        """
        # Label - fixed width, no wrap
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 13px; ")
        label_widget.setFixedWidth(110)
        
        # Value with optional status indicator (badge before text)
        if status:
            # Create container for badge + text
            value_widget = QWidget()
            value_layout = QHBoxLayout(value_widget)
            value_layout.setContentsMargins(0, 0, 0, 0)
            value_layout.setSpacing(6)
            
            # Status badge (semantic colors)
            status_dot = StatusDot(status)
            value_layout.addWidget(status_dot)
            
            # Text (neutral color - no semantic color on text)
            value_label = QLabel(value)
            value_label.setStyleSheet("font-size: 13px;")
            value_label.setWordWrap(False)
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_layout.addWidget(value_label)
            value_layout.addStretch()
            
            value_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            value_widget.setMinimumWidth(200)
        else:
            value_widget = QLabel(value)
            value_widget.setStyleSheet("font-size: 13px;")
            value_widget.setWordWrap(False)
            value_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            value_widget.setMinimumWidth(200)
        
        grid.addWidget(label_widget, row, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(value_widget, row, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        return row + 1
    
    def on_refresh_clicked(self):
        """Handle refresh button click with visual feedback"""
        self.refresh_btn.start_refresh()
        self.refresh()
        self.refresh_btn.finish_refresh()
    
    def refresh(self):
        """Refresh all device information"""
        self.load_device_info()
        self.load_network_info()
        self.load_enrollment_info()
        self.load_compliance_info()
    
    def load_device_info(self):
        """Load device hardware/OS info"""
        self._clear_grid(self.device_grid)
        row = 0
        
        # Hostname
        row = self._add_info_row(self.device_grid, row, "Hostname", socket.gethostname())
        
        # OS
        os_name = "Unknown"
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        os_name = line.split("=", 1)[1].strip().strip('"')
                        break
        except Exception:
            os_name = platform.system()
        row = self._add_info_row(self.device_grid, row, "Operating System", os_name)
        
        # Kernel
        row = self._add_info_row(self.device_grid, row, "Kernel", platform.release())
        
        # Architecture
        row = self._add_info_row(self.device_grid, row, "Architecture", platform.machine())
        
        # Uptime
        try:
            with open("/proc/uptime") as f:
                uptime_seconds = float(f.read().split()[0])
                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                if days > 0:
                    uptime_str = f"{days}d {hours}h {minutes}m"
                else:
                    uptime_str = f"{hours}h {minutes}m"
                row = self._add_info_row(self.device_grid, row, "Uptime", uptime_str)
        except Exception:
            pass
        
        # Memory
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_kb = int(line.split()[1])
                        mem_gb = mem_kb / 1024 / 1024
                        row = self._add_info_row(self.device_grid, row, "Memory", f"{mem_gb:.1f} GB")
                        break
        except Exception:
            pass
        
        # CPU
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        cpu_name = line.split(":", 1)[1].strip()
                        # Truncate long CPU names
                        if len(cpu_name) > 40:
                            cpu_name = cpu_name[:37] + "..."
                        row = self._add_info_row(self.device_grid, row, "CPU", cpu_name)
                        break
        except Exception:
            pass
    
    def load_network_info(self):
        """Load network information"""
        self._clear_grid(self.network_grid)
        row = 0
        
        # Hostname FQDN
        fqdn = socket.getfqdn()
        row = self._add_info_row(self.network_grid, row, "FQDN", fqdn)
        
        # Primary IP Address
        ip = "Unknown"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except Exception:
            # Fallback: try to get any non-loopback IP
            try:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
            except Exception:
                pass
        row = self._add_info_row(self.network_grid, row, "IP Address", ip)
        
        # Default gateway
        try:
            result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and result.stdout:
                # Parse: default via 192.168.1.1 dev eth0
                parts = result.stdout.split()
                if len(parts) >= 3 and parts[0] == "default":
                    gateway = parts[2]
                    row = self._add_info_row(self.network_grid, row, "Gateway", gateway)
        except Exception:
            pass
        
        # DNS servers
        try:
            dns_servers = []
            resolv_path = Path("/etc/resolv.conf")
            if resolv_path.exists():
                with open(resolv_path) as f:
                    for line in f:
                        if line.startswith("nameserver"):
                            dns_servers.append(line.split()[1])
            if dns_servers:
                row = self._add_info_row(self.network_grid, row, "DNS", ", ".join(dns_servers[:2]))
        except Exception:
            pass
    
    def load_enrollment_info(self):
        """Load enrollment status"""
        self._clear_grid(self.enrollment_grid)
        row = 0
        
        status = self.validator.validate()
        
        # aad-tool status (native check)
        daemon_ok, daemon_msg = self.validator.check_aad_tool_status()
        row = self._add_info_row(
            self.enrollment_grid, row, "Daemon",
            daemon_msg, status='success' if daemon_ok else 'error'
        )
        
        # Domain
        if status.configured_domain:
            row = self._add_info_row(
                self.enrollment_grid, row, "Domain", 
                status.configured_domain, status='success'
            )
        else:
            row = self._add_info_row(
                self.enrollment_grid, row, "Domain", 
                "Not configured", status='pending'
            )
        
        # Enrollment status
        if status.is_fully_configured:
            row = self._add_info_row(
                self.enrollment_grid, row, "Status", 
                "Enrolled", status='success'
            )
        elif status.himmelblau_installed:
            row = self._add_info_row(
                self.enrollment_grid, row, "Status", 
                "Partially configured", status='warning'
            )
        else:
            row = self._add_info_row(
                self.enrollment_grid, row, "Status", 
                "Not enrolled", status='pending'
            )
        
        # Himmelblau version
        if status.himmelblau_version:
            row = self._add_info_row(
                self.enrollment_grid, row, "Agent Version", 
                status.himmelblau_version
            )
        
        # Service status
        if status.himmelblaud_running:
            row = self._add_info_row(
                self.enrollment_grid, row, "Service", 
                "Running", status='success'
            )
        else:
            row = self._add_info_row(
                self.enrollment_grid, row, "Service", 
                "Stopped", status='error' if status.himmelblau_installed else 'pending'
            )
        
        # Config file
        if status.config_exists:
            row = self._add_info_row(
                self.enrollment_grid, row, "Configuration", 
                "Present", status='success'
            )
        else:
            row = self._add_info_row(
                self.enrollment_grid, row, "Configuration", 
                "Missing", status='pending'
            )
    
    def load_compliance_info(self):
        """Load compliance status"""
        self._clear_grid(self.compliance_grid)
        row = 0
        
        status = self.validator.validate()
        
        if not status.is_fully_configured:
            row = self._add_info_row(
                self.compliance_grid, row, "Status", 
                "Not enrolled", status='pending'
            )
            row = self._add_info_row(
                self.compliance_grid, row, "Policy", 
                "N/A", status='pending'
            )
            return
        
        # Get Intune status from centralized validator
        intune = self.validator.get_intune_status()
        
        # Enrollment status
        enrollment_state_map = {
            'enrolled': 'success',
            'not_enrolled': 'warning',
            'device_limit': 'error',
            'failed': 'error',
            'unknown': 'pending',
        }
        row = self._add_info_row(
            self.compliance_grid, row, "Intune Status", 
            intune.display_enrollment,
            status=enrollment_state_map.get(intune.enrollment_state, 'pending')
        )
        
        # Show error detail if present
        if intune.enrollment_error:
            row = self._add_info_row(
                self.compliance_grid, row, "Error", 
                intune.enrollment_error, status='error'
            )
        
        # Compliance status
        compliance_state_map = {
            'compliant': 'success',
            'non_compliant': 'error',
            'unknown': 'warning',
            'not_applicable': 'pending',
        }
        row = self._add_info_row(
            self.compliance_grid, row, "Compliance",
            intune.display_compliance,
            status=compliance_state_map.get(intune.compliance_state, 'pending')
        )
        
        # Policy enforcement
        row = self._add_info_row(
            self.compliance_grid, row, "Policy", 
            "Enabled" if status.config_exists else "Disabled",
            status='success' if status.config_exists else 'pending'
        )
        
        # Task scheduler (cronie)
        if status.cronie_running:
            row = self._add_info_row(
                self.compliance_grid, row, "Task Scheduler", 
                "Running", status='success'
            )
        else:
            row = self._add_info_row(
                self.compliance_grid, row, "Task Scheduler", 
                "Not running", status='warning'
            )
        
        # Last check-in (from journal)
        try:
            result = subprocess.run(
                ["journalctl", "-u", "himmelblaud", "-n", "1", "--no-pager", 
                 "-o", "short-iso", "--output-fields=__REALTIME_TIMESTAMP"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                # Get just the date part from the journal entry
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line and not line.startswith('--'):
                        # Format: 2024-01-15T10:30:45+0000 hostname...
                        parts = line.split()
                        if parts:
                            timestamp = parts[0]
                            if 'T' in timestamp:
                                date_part = timestamp.split('T')[0]
                                time_part = timestamp.split('T')[1].split('+')[0].split('-')[0][:5]
                                row = self._add_info_row(
                                    self.compliance_grid, row, "Last Activity", 
                                    f"{date_part} {time_part}"
                                )
                        break
        except Exception:
            pass
