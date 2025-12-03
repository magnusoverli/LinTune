"""
Logs view for LinTune

Shows system logs related to Himmelblau and enrollment.
"""

import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor

from .widgets import RefreshButton


class LogsView(QWidget):
    """Logs viewer with filtering and auto-refresh"""
    
    LOG_SOURCES = {
        "Himmelblau Daemon": "himmelblaud",
        "Himmelblau Tasks": "himmelblaud-tasks",
        "GDM": "gdm",
        "System Auth": "system-auth",
    }
    
    def __init__(self):
        super().__init__()
        self.auto_refresh = False
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_logs)
        self.init_ui()
        self.load_logs()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Logs")
        title.setStyleSheet("font-size: 24px; font-weight: 600; ")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Auto-refresh toggle
        self.auto_refresh_btn = QPushButton("Auto-refresh: Off")
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:checked {
                background-color: palette(highlight);
                color: palette(highlighted-text);
                border: none;
            }
        """)
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        header_layout.addWidget(self.auto_refresh_btn)
        
        # Refresh button
        self.refresh_btn = RefreshButton()
        self.refresh_btn.refresh_requested.connect(self.on_refresh_clicked)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Filter bar
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 8px;
            }
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(12, 8, 12, 8)
        
        # Source selector
        source_label = QLabel("Source:")
        source_label.setStyleSheet(" font-size: 13px;")
        filter_layout.addWidget(source_label)
        
        self.source_combo = QComboBox()
        self.source_combo.addItems(list(self.LOG_SOURCES.keys()))
        self.source_combo.setStyleSheet("""
            QComboBox {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 150px;
            }
        """)
        self.source_combo.currentIndexChanged.connect(self.load_logs)
        filter_layout.addWidget(self.source_combo)
        
        filter_layout.addSpacing(16)
        
        # Lines selector
        lines_label = QLabel("Lines:")
        lines_label.setStyleSheet(" font-size: 13px;")
        filter_layout.addWidget(lines_label)
        
        self.lines_combo = QComboBox()
        self.lines_combo.addItems(["50", "100", "200", "500"])
        self.lines_combo.setCurrentText("100")
        self.lines_combo.setStyleSheet("""
            QComboBox {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
        """)
        self.lines_combo.currentIndexChanged.connect(self.load_logs)
        filter_layout.addWidget(self.lines_combo)
        
        filter_layout.addSpacing(16)
        
        # Search
        search_label = QLabel("🔍")
        filter_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter logs...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 200px;
            }
        """)
        self.search_input.textChanged.connect(self.filter_logs)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addStretch()
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: palette(midlight); }
        """)
        clear_btn.clicked.connect(self.clear_logs)
        filter_layout.addWidget(clear_btn)
        
        layout.addWidget(filter_frame)
        
        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Monospace", 10))
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: palette(base);
                color: palette(text);
                border: 1px solid palette(mid);
                border-radius: 4px;
                padding: 12px;
                font-family: "Cascadia Code", "Fira Code", monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.log_output, 1)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(" font-size: 12px;")
        layout.addWidget(self.status_label)
    
    def on_refresh_clicked(self):
        """Handle refresh button click with visual feedback"""
        self.refresh_btn.start_refresh()
        self.load_logs()
        self.refresh_btn.finish_refresh()
    
    def load_logs(self):
        """Load logs from journalctl"""
        source_name = self.source_combo.currentText()
        service = self.LOG_SOURCES.get(source_name, "himmelblaud")
        lines = self.lines_combo.currentText()
        
        try:
            result = subprocess.run(
                ["journalctl", "-u", f"{service}.service", "-n", lines, "--no-pager"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            self.full_log_content = result.stdout
            self.display_logs(self.full_log_content)
            self.status_label.setText(f"Loaded {len(self.full_log_content.splitlines())} lines from {service}")
            
        except subprocess.TimeoutExpired:
            self.log_output.setText("Timeout loading logs")
            self.status_label.setText("Error: Timeout")
        except Exception as e:
            self.log_output.setText(f"Error loading logs: {e}")
            self.status_label.setText(f"Error: {e}")
    
    def display_logs(self, content: str):
        """Display logs with syntax highlighting using palette colors"""
        self.log_output.clear()
        
        # Get colors from palette for theme compatibility
        palette = self.palette()
        error_color = palette.linkVisited().color().name()  # Typically reddish
        warn_color = palette.brightText().color().name()    # Bright/attention
        info_color = palette.highlight().color().name()     # Accent color
        success_color = palette.highlight().color().name()  # Accent color
        
        for line in content.split('\n'):
            if 'error' in line.lower() or 'fail' in line.lower():
                self.log_output.append(f'<span style="color: {error_color};">{line}</span>')
            elif 'warn' in line.lower():
                self.log_output.append(f'<span style="color: {warn_color};">{line}</span>')
            elif 'info' in line.lower():
                self.log_output.append(f'<span style="color: {info_color};">{line}</span>')
            elif 'success' in line.lower() or 'ok' in line.lower():
                self.log_output.append(f'<span style="color: {success_color};">{line}</span>')
            else:
                self.log_output.append(line)
        
        # Scroll to bottom
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_output.setTextCursor(cursor)
    
    def filter_logs(self, text: str):
        """Filter displayed logs"""
        if not hasattr(self, 'full_log_content'):
            return
        
        if not text:
            self.display_logs(self.full_log_content)
            return
        
        filtered = '\n'.join(
            line for line in self.full_log_content.split('\n')
            if text.lower() in line.lower()
        )
        self.display_logs(filtered)
    
    def clear_logs(self):
        """Clear log display"""
        self.log_output.clear()
        self.status_label.setText("Cleared")
    
    def toggle_auto_refresh(self, checked: bool):
        """Toggle auto-refresh"""
        self.auto_refresh = checked
        if checked:
            self.auto_refresh_btn.setText("Auto-refresh: On")
            self.refresh_timer.start(5000)  # 5 seconds
        else:
            self.auto_refresh_btn.setText("Auto-refresh: Off")
            self.refresh_timer.stop()

