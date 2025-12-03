"""
Dialogs for LinTune
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QProgressBar, QFrame, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from ..core.installer import Installer, InstallProgress, InstallStatus


class DomainInputDialog(QDialog):
    """Dialog for entering EntraID domain"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.domain = ""
        self.grant_sudo = True
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Connect to Organization")
        self.setFixedSize(450, 280)
        self.setStyleSheet("background-color: palette(window);")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("Connect to your organization")
        title.setStyleSheet("font-size: 18px; font-weight: 600; ")
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Enter your EntraID domain to configure this device for enterprise management.")
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; ")
        layout.addWidget(desc)
        
        layout.addSpacing(8)
        
        # Domain input
        domain_label = QLabel("EntraID Domain")
        domain_label.setStyleSheet("font-size: 12px; font-weight: 600; ")
        layout.addWidget(domain_label)
        
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("company.onmicrosoft.com")
        self.domain_input.setStyleSheet("""
            QLineEdit {
                background-color: palette(window);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 10px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid palette(highlight);
            }
        """)
        layout.addWidget(self.domain_input)
        
        # Sudo checkbox
        self.sudo_checkbox = QCheckBox("Grant sudo access to EntraID users")
        self.sudo_checkbox.setChecked(True)
        self.sudo_checkbox.setStyleSheet("font-size: 13px; ")
        layout.addWidget(self.sudo_checkbox)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: palette(midlight);
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        connect_btn = QPushButton("Connect")
        connect_btn.setStyleSheet("""
            QPushButton {
                background-color: palette(highlight);
                color: palette(highlighted-text);
                border: none;
                border-radius: 4px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: palette(dark);
            }
        """)
        connect_btn.clicked.connect(self.on_connect)
        btn_layout.addWidget(connect_btn)
        
        layout.addLayout(btn_layout)
    
    def on_connect(self):
        domain = self.domain_input.text().strip()
        if domain:
            self.domain = domain
            self.grant_sudo = self.sudo_checkbox.isChecked()
            self.accept()


class InstallWorker(QThread):
    """Worker thread for installation"""
    
    progress = pyqtSignal(object)  # InstallProgress
    finished = pyqtSignal(bool)
    
    def __init__(self, domain: str, grant_sudo: bool):
        super().__init__()
        self.domain = domain
        self.grant_sudo = grant_sudo
        self.installer = None
    
    def run(self):
        self.installer = Installer(progress_callback=self.on_progress)
        success = self.installer.install(self.domain, self.grant_sudo)
        self.finished.emit(success)
    
    def on_progress(self, progress: InstallProgress):
        self.progress.emit(progress)


class InstallProgressDialog(QDialog):
    """Dialog showing installation progress"""
    
    def __init__(self, domain: str, grant_sudo: bool, parent=None):
        super().__init__(parent)
        self.domain = domain
        self.grant_sudo = grant_sudo
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Installing...")
        self.setFixedSize(500, 350)
        self.setStyleSheet("background-color: palette(window);")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        self.title_label = QLabel("Configuring device...")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600; ")
        layout.addWidget(self.title_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: palette(mid);
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 palette(highlight), stop:1 palette(dark));
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status message
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("font-size: 14px; ")
        layout.addWidget(self.status_label)
        
        # Step indicator
        self.step_label = QLabel("Step 0/7")
        self.step_label.setStyleSheet("font-size: 12px; color: palette(mid);")
        layout.addWidget(self.step_label)
        
        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(120)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: palette(midlight);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 8px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.log_output)
        
        layout.addStretch()
        
        # Close button (hidden during install)
        self.close_btn = QPushButton("Close")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: palette(highlight);
                color: palette(highlighted-text);
                border: none;
                border-radius: 4px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: palette(dark);
            }
        """)
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.hide()
        layout.addWidget(self.close_btn, alignment=Qt.AlignmentFlag.AlignRight)
    
    def start_installation(self):
        """Start the installation process"""
        self.worker = InstallWorker(self.domain, self.grant_sudo)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
    
    def on_progress(self, progress: InstallProgress):
        """Update UI with progress"""
        self.progress_bar.setValue(progress.progress_percent)
        self.status_label.setText(progress.message)
        self.step_label.setText(f"Step {progress.step_number}/{progress.total_steps}: {progress.current_step.value}")
        
        # Log message
        self.log_output.append(f"[{progress.progress_percent:3d}%] {progress.message}")
        
        # Auto-scroll
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_finished(self, success: bool):
        """Handle installation completion"""
        if success:
            self.title_label.setText("✓ Installation Complete!")
            self.title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: palette(highlight);")
            self.status_label.setText(f"Device configured for {self.domain}")
            self.log_output.append("\n✓ Installation completed successfully!")
            self.log_output.append("\nNext steps:")
            self.log_output.append("  1. Log out of your current session")
            self.log_output.append("  2. At login screen, click 'Not listed?'")
            self.log_output.append(f"  3. Enter your email: user@{self.domain}")
            self.log_output.append("  4. Complete MFA authentication")
        else:
            self.title_label.setText("✗ Installation Failed")
            self.title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: palette(link-visited);")
            self.status_label.setText("An error occurred during installation")
            self.log_output.append("\n✗ Installation failed")
        
        self.progress_bar.setValue(100 if success else self.progress_bar.value())
        self.close_btn.show()
    
    def showEvent(self, event):
        """Start installation when dialog is shown"""
        super().showEvent(event)
        self.start_installation()

