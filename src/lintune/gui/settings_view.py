"""
Settings view for LinTune - Compact layout, no scrolling
"""

import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QCheckBox, QMessageBox, QGridLayout,
    QProgressDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject

from .widgets import StatusBadge


class AadToolWorker(QObject):
    """Worker for running aad-tool commands in background thread"""
    
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, command: str, args: list = None):
        super().__init__()
        self.command = command
        self.args = args or []
    
    def run(self):
        """Execute the aad-tool command"""
        try:
            cmd = ['pkexec', 'aad-tool', self.command] + self.args
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            output = result.stdout.strip()
            if result.returncode == 0:
                self.finished.emit(True, output or f"{self.command} completed")
            else:
                error = result.stderr.strip()
                self.finished.emit(False, error or output or f"{self.command} failed")
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Operation timed out")
        except Exception as e:
            self.finished.emit(False, str(e))


class SettingsView(QWidget):
    """Settings management view - compact single-screen layout"""
    
    config_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(24, 24, 24, 24)
        main.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: 600; ")
        header.addWidget(title)
        header.addStretch()
        main.addLayout(header)
        
        # Two-column layout
        columns = QHBoxLayout()
        columns.setSpacing(24)
        
        # === LEFT COLUMN ===
        left = QVBoxLayout()
        left.setSpacing(16)
        
        # EntraID Section
        section1 = QLabel("EntraID Configuration")
        section1.setStyleSheet("font-size: 13px; font-weight: 600; color: palette(highlight); text-transform: uppercase; letter-spacing: 0.5px;")
        left.addWidget(section1)
        
        # Domain
        domain_row = QHBoxLayout()
        domain_lbl = QLabel("Domain")
        domain_lbl.setStyleSheet("font-size: 13px; ")
        domain_lbl.setFixedWidth(80)
        domain_row.addWidget(domain_lbl)
        
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("company.onmicrosoft.com")
        self.domain_input.setStyleSheet("""
            QLineEdit {
                background: palette(base); border: 1px solid palette(mid); border-radius: 4px;
                padding: 6px 10px; font-size: 13px;             }
            QLineEdit:focus { border: 2px solid palette(highlight); padding: 5px 9px; }
        """)
        domain_row.addWidget(self.domain_input)
        left.addLayout(domain_row)
        
        # Sudo checkbox
        self.sudo_checkbox = QCheckBox("Grant sudo access to EntraID users")
        left.addWidget(self.sudo_checkbox)
        
        left.addSpacing(8)
        
        # Options Section
        section2 = QLabel("Options")
        section2.setStyleSheet("font-size: 13px; font-weight: 600; color: palette(highlight); text-transform: uppercase; letter-spacing: 0.5px;")
        left.addWidget(section2)
        
        self.debug_checkbox = QCheckBox("Enable debug logging")
        left.addWidget(self.debug_checkbox)
        
        self.policy_checkbox = QCheckBox("Enable Intune policy enforcement")
        left.addWidget(self.policy_checkbox)
        
        left.addStretch()
        columns.addLayout(left, 1)
        
        # Vertical separator
        vsep = QFrame()
        vsep.setFrameShape(QFrame.Shape.VLine)
        vsep.setStyleSheet("background-color: palette(mid);")
        vsep.setFixedWidth(1)
        columns.addWidget(vsep)
        
        # === RIGHT COLUMN ===
        right = QVBoxLayout()
        right.setSpacing(16)
        
        # Services Section
        section3 = QLabel("Services")
        section3.setStyleSheet("font-size: 13px; font-weight: 600; color: palette(highlight); text-transform: uppercase; letter-spacing: 0.5px;")
        right.addWidget(section3)
        
        # Status row
        status_row = QHBoxLayout()
        status_lbl = QLabel("Himmelblaud")
        status_lbl.setStyleSheet("font-size: 13px; ")
        status_row.addWidget(status_lbl)
        status_row.addStretch()
        self.service_badge = StatusBadge('neutral', '...')
        status_row.addWidget(self.service_badge)
        right.addLayout(status_row)
        
        # Service buttons
        svc_btns = QHBoxLayout()
        svc_btns.setSpacing(8)
        
        self.restart_btn = QPushButton("Restart")
        self.restart_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.restart_btn.setStyleSheet("""
            QPushButton { background: palette(highlight); color: palette(highlighted-text); border: none; border-radius: 4px;
                padding: 6px 16px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { background: palette(dark); }
        """)
        self.restart_btn.clicked.connect(self.restart_services)
        svc_btns.addWidget(self.restart_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setStyleSheet("""
            QPushButton { background: transparent; color: palette(link-visited); border: 1px solid palette(link-visited);
                border-radius: 4px; padding: 6px 16px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { background: palette(midlight); }
        """)
        self.stop_btn.clicked.connect(self.stop_services)
        svc_btns.addWidget(self.stop_btn)
        
        self.verify_btn = QPushButton("Verify")
        self.verify_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.verify_btn.setStyleSheet("""
            QPushButton { background: transparent;  border: 1px solid palette(mid);
                border-radius: 4px; padding: 6px 16px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { background: palette(midlight); }
        """)
        self.verify_btn.clicked.connect(self.verify_status)
        svc_btns.addWidget(self.verify_btn)
        
        svc_btns.addStretch()
        right.addLayout(svc_btns)
        
        right.addSpacing(8)
        
        # Advanced Section (native aad-tool features)
        section4 = QLabel("Advanced")
        section4.setStyleSheet("font-size: 13px; font-weight: 600; color: palette(highlight); text-transform: uppercase; letter-spacing: 0.5px;")
        right.addWidget(section4)
        
        # Advanced action buttons
        adv_btns = QHBoxLayout()
        adv_btns.setSpacing(8)
        
        self.enum_btn = QPushButton("Enumerate Users")
        self.enum_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.enum_btn.setToolTip("Pre-cache EntraID users and groups")
        self.enum_btn.setStyleSheet("""
            QPushButton { background: transparent; color: palette(highlight); border: 1px solid palette(highlight);
                border-radius: 4px; padding: 6px 12px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { background: palette(midlight); }
        """)
        self.enum_btn.clicked.connect(self.enumerate_users)
        adv_btns.addWidget(self.enum_btn)
        
        self.tpm_btn = QPushButton("TPM Status")
        self.tpm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tpm_btn.setToolTip("Check TPM hardware status")
        self.tpm_btn.setStyleSheet("""
            QPushButton { background: transparent; color: palette(highlight); border: 1px solid palette(highlight);
                border-radius: 4px; padding: 6px 12px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { background: palette(midlight); }
        """)
        self.tpm_btn.clicked.connect(self.check_tpm)
        adv_btns.addWidget(self.tpm_btn)
        
        adv_btns.addStretch()
        right.addLayout(adv_btns)
        
        # Offline breakglass
        breakglass_row = QHBoxLayout()
        breakglass_lbl = QLabel("Offline Mode")
        breakglass_lbl.setStyleSheet("font-size: 13px; ")
        breakglass_lbl.setToolTip("Emergency offline authentication when Entra ID unreachable")
        breakglass_row.addWidget(breakglass_lbl)
        breakglass_row.addStretch()
        
        self.breakglass_btn = QPushButton("Enable 2h")
        self.breakglass_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.breakglass_btn.setToolTip("Enable offline breakglass for 2 hours")
        self.breakglass_btn.setStyleSheet("""
            QPushButton { background: transparent; color: palette(bright-text); border: 1px solid palette(bright-text);
                border-radius: 4px; padding: 4px 10px; font-size: 11px; font-weight: 600; }
            QPushButton:hover { background: palette(midlight); }
        """)
        self.breakglass_btn.clicked.connect(lambda: self.set_breakglass("2h"))
        breakglass_row.addWidget(self.breakglass_btn)
        
        self.breakglass_off_btn = QPushButton("Disable")
        self.breakglass_off_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.breakglass_off_btn.setStyleSheet("""
            QPushButton { background: transparent;  border: 1px solid palette(mid);
                border-radius: 4px; padding: 4px 10px; font-size: 11px; font-weight: 600; }
            QPushButton:hover { background: palette(midlight); }
        """)
        self.breakglass_off_btn.clicked.connect(lambda: self.set_breakglass("0"))
        breakglass_row.addWidget(self.breakglass_off_btn)
        
        right.addLayout(breakglass_row)
        
        right.addSpacing(8)
        
        # Backup Section
        section5 = QLabel("Backup & Recovery")
        section5.setStyleSheet("font-size: 13px; font-weight: 600; color: palette(highlight); text-transform: uppercase; letter-spacing: 0.5px;")
        right.addWidget(section5)
        
        # Backup status
        backup_row = QHBoxLayout()
        backup_lbl = QLabel("Backups")
        backup_lbl.setStyleSheet("font-size: 13px; ")
        backup_row.addWidget(backup_lbl)
        backup_row.addStretch()
        self.backup_badge = StatusBadge('neutral', '...')
        backup_row.addWidget(self.backup_badge)
        right.addLayout(backup_row)
        
        # Restore button
        restore_row = QHBoxLayout()
        self.restore_btn = QPushButton("Restore Original Config")
        self.restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.restore_btn.setStyleSheet("""
            QPushButton { background: transparent; color: palette(link-visited); border: 1px solid palette(link-visited);
                border-radius: 4px; padding: 6px 16px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { background: palette(midlight); }
        """)
        self.restore_btn.clicked.connect(self.restore_backups)
        restore_row.addWidget(self.restore_btn)
        restore_row.addStretch()
        right.addLayout(restore_row)
        
        right.addStretch()
        columns.addLayout(right, 1)
        
        main.addLayout(columns, 1)
        
        # Bottom save button
        main.addSpacing(8)
        
        bottom = QHBoxLayout()
        bottom.addStretch()
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton { background: palette(highlight); color: palette(highlighted-text); border: none; border-radius: 4px;
                padding: 10px 32px; font-size: 14px; font-weight: 600; }
            QPushButton:hover { background: palette(dark); }
        """)
        self.save_btn.clicked.connect(self.save_settings)
        bottom.addWidget(self.save_btn)
        
        main.addLayout(bottom)
    
    def load_settings(self):
        """Load settings from config"""
        config = Path("/etc/himmelblau/himmelblau.conf")
        if config.exists():
            try:
                for line in config.read_text().splitlines():
                    if '=' in line and not line.strip().startswith('#'):
                        k, v = line.split('=', 1)
                        k, v = k.strip(), v.strip()
                        if k == 'domains': self.domain_input.setText(v)
                        elif k == 'local_groups': self.sudo_checkbox.setChecked('wheel' in v)
                        elif k == 'debug': self.debug_checkbox.setChecked(v.lower() == 'true')
                        elif k == 'apply_policy': self.policy_checkbox.setChecked(v.lower() == 'true')
            except: pass
        
        self.update_service_status()
        self.update_backup_status()
    
    def update_service_status(self):
        try:
            r = subprocess.run(["systemctl", "is-active", "himmelblaud"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                self.service_badge.set_status('success', 'Running')
            else:
                self.service_badge.set_status('error', 'Stopped')
        except:
            self.service_badge.set_status('neutral', 'Unknown')
    
    def update_backup_status(self):
        b = []
        if Path("/etc/nsswitch.conf.backup").exists(): b.append("NSS")
        if Path("/etc/pam.d/system-auth.backup").exists(): b.append("PAM")
        if b:
            self.backup_badge.set_status('success', ', '.join(b))
        else:
            self.backup_badge.set_status('neutral', 'None')
    
    def verify_status(self):
        try:
            r = subprocess.run(["/usr/bin/aad-tool", "status"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and "working" in r.stdout.lower():
                QMessageBox.information(self, "Status", f"✓ EntraID working!\n\n{r.stdout}")
            else:
                QMessageBox.warning(self, "Status", f"Issue detected:\n\n{r.stdout or r.stderr}")
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", "aad-tool not found")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
    
    def save_settings(self):
        domain = self.domain_input.text().strip()
        if not domain:
            QMessageBox.warning(self, "Error", "Domain required")
            return
        
        cfg = f"""[global]
domains = {domain}
local_groups = {"users,wheel" if self.sudo_checkbox.isChecked() else "users"}
home_attr = CN
home_alias = CN
use_etc_skel = true
enable_hello = false
debug = {"true" if self.debug_checkbox.isChecked() else "false"}
apply_policy = {"true" if self.policy_checkbox.isChecked() else "false"}
"""
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(cfg)
                tmp = f.name
            subprocess.run(["sudo", "cp", tmp, "/etc/himmelblau/himmelblau.conf"], check=True, timeout=10)
            Path(tmp).unlink(missing_ok=True)
            QMessageBox.information(self, "Saved", "Settings saved. Restart services to apply.")
            self.config_changed.emit()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
    
    def restart_services(self):
        try:
            subprocess.run(["sudo", "systemctl", "restart", "himmelblaud"], check=True, timeout=30)
            self.update_service_status()
            QMessageBox.information(self, "Done", "Services restarted")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
    
    def stop_services(self):
        if QMessageBox.question(self, "Stop?", "Stop services? EntraID login will not work.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                subprocess.run(["sudo", "systemctl", "stop", "himmelblaud"], check=True, timeout=30)
                self.update_service_status()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def restore_backups(self):
        if QMessageBox.question(self, "Restore?", 
            "Restore original config?\n\nEntraID will be disabled.\nRestart system afterward.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        try:
            subprocess.run(["sudo", "systemctl", "stop", "himmelblaud"], timeout=30)
            if Path("/etc/nsswitch.conf.backup").exists():
                subprocess.run(["sudo", "cp", "/etc/nsswitch.conf.backup", "/etc/nsswitch.conf"], check=True)
            if Path("/etc/pam.d/system-auth.backup").exists():
                subprocess.run(["sudo", "cp", "/etc/pam.d/system-auth.backup", "/etc/pam.d/system-auth"], check=True)
            self.update_service_status()
            QMessageBox.information(self, "Done", "Restored. Please restart system.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
    
    def enumerate_users(self):
        """Enumerate and cache EntraID users using native aad-tool (async)"""
        
        reply = QMessageBox.question(self, "Enumerate Users",
            "This will pre-cache EntraID users and groups.\n\n"
            "This may take a while and requires authentication.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Create progress dialog
        self.enum_progress = QProgressDialog("Enumerating users...", "Cancel", 0, 0, self)
        self.enum_progress.setWindowTitle("Please Wait")
        self.enum_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.enum_progress.setMinimumDuration(0)
        self.enum_progress.setValue(0)
        self.enum_progress.show()
        QApplication.processEvents()
        
        # Run in background thread
        self.enum_worker = AadToolWorker("enumerate")
        self.enum_thread = QThread()
        self.enum_worker.moveToThread(self.enum_thread)
        
        self.enum_thread.started.connect(self.enum_worker.run)
        self.enum_worker.finished.connect(self.on_enumerate_finished)
        self.enum_worker.finished.connect(self.enum_thread.quit)
        self.enum_worker.finished.connect(self.enum_worker.deleteLater)
        self.enum_thread.finished.connect(self.enum_thread.deleteLater)
        
        self.enum_thread.start()
    
    def on_enumerate_finished(self, success: bool, message: str):
        """Handle enumeration completion"""
        self.enum_progress.close()
        
        if success:
            QMessageBox.information(self, "Enumeration", f"✓ {message}")
        else:
            QMessageBox.warning(self, "Enumeration", f"Failed:\n{message}")
    
    def check_tpm(self):
        """Check TPM status using native aad-tool"""
        from ..core.validator import SystemValidator
        
        validator = SystemValidator()
        in_use, message = validator.get_tpm_status()
        
        if in_use:
            QMessageBox.information(self, "TPM Status", 
                f"✓ TPM In Use\n\n{message}\n\n"
                f"Your device keys are protected by hardware TPM.")
        else:
            QMessageBox.information(self, "TPM Status", 
                f"TPM Not In Use\n\n{message}\n\n"
                f"Himmelblau is using software key storage.\n"
                f"This is normal and secure for most setups.")
    
    def set_breakglass(self, ttl: str):
        """Set offline breakglass mode using native aad-tool"""
        from ..core.validator import SystemValidator
        
        action = "disable" if ttl == "0" else f"enable for {ttl}"
        
        if QMessageBox.question(self, "Offline Breakglass",
            f"This will {action} offline breakglass mode.\n\n"
            f"When enabled, cached passwords can be used when Entra ID is unreachable.\n\n"
            f"Note: Must be enabled in himmelblau.conf first.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        
        validator = SystemValidator()
        success, message = validator.set_offline_breakglass(ttl)
        
        if success:
            QMessageBox.information(self, "Breakglass", f"✓ {message}")
        else:
            QMessageBox.warning(self, "Breakglass", f"Failed:\n{message}")
