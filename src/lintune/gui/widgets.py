"""
Reusable widgets for LinTune

Common UI components used across views.
"""

from PyQt6.QtWidgets import QPushButton, QApplication, QLabel, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor


class StatusBadge(QWidget):
    """
    Semantic status badge with colored dot indicator.
    
    Uses hardcoded green/yellow/red colors for universal status meaning.
    These colors are intentionally NOT from palette - they are semantic.
    """
    
    # Semantic status colors - universal meaning
    COLORS = {
        'success': '#10B981',   # Green - good, running, complete
        'warning': '#F59E0B',   # Amber - caution, pending  
        'error': '#EF4444',     # Red - failed, stopped, error
        'info': '#3B82F6',      # Blue - informational
        'neutral': '#6B7280',   # Gray - unknown, inactive
    }
    
    def __init__(self, status: str = 'neutral', text: str = '', parent=None):
        """
        Create a status badge.
        
        Args:
            status: One of 'success', 'warning', 'error', 'info', 'neutral'
            text: Optional text label next to the dot
            parent: Parent widget
        """
        super().__init__(parent)
        self._status = status
        self._text = text
        self._init_ui()
    
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # Status dot
        self._dot = QLabel("●")
        self._dot.setFixedWidth(16)
        self._update_dot_style()
        layout.addWidget(self._dot)
        
        # Text label (uses palette for text color)
        if self._text:
            self._label = QLabel(self._text)
            self._label.setStyleSheet("font-size: 13px;")
            layout.addWidget(self._label)
        else:
            self._label = None
        
        layout.addStretch()
    
    def _update_dot_style(self):
        color = self.COLORS.get(self._status, self.COLORS['neutral'])
        self._dot.setStyleSheet(f"color: {color}; font-size: 14px;")
    
    def set_status(self, status: str, text: str = None):
        """Update the badge status and optionally the text."""
        self._status = status
        self._update_dot_style()
        
        if text is not None and self._label:
            self._label.setText(text)
    
    def set_text(self, text: str):
        """Update just the text."""
        if self._label:
            self._label.setText(text)
    
    @property
    def status(self) -> str:
        return self._status


class StatusDot(QLabel):
    """
    Simple colored status dot without text.
    
    For use in tables, lists, or tight spaces.
    """
    
    COLORS = StatusBadge.COLORS
    
    def __init__(self, status: str = 'neutral', parent=None):
        super().__init__("●", parent)
        self._status = status
        self.setFixedWidth(16)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_style()
    
    def _update_style(self):
        color = self.COLORS.get(self._status, self.COLORS['neutral'])
        self.setStyleSheet(f"color: {color}; font-size: 14px;")
    
    def set_status(self, status: str):
        """Update the dot status."""
        self._status = status
        self._update_style()
    
    @property
    def status(self) -> str:
        return self._status


class RefreshButton(QPushButton):
    """
    Reusable refresh button with visual feedback.
    
    Shows loading state while refreshing, then success state briefly.
    """
    
    # Signal emitted when refresh is requested
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_timer = None
        self._is_refreshing = False
        
        # Styles - use semantic colors that work in light/dark
        self._default_style = """
            QPushButton {
                background-color: transparent;
                color: palette(highlight);
                border: 1px solid palette(highlight);
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 600;
                min-width: 100px;
            }
            QPushButton:hover { background-color: palette(midlight); }
            QPushButton:disabled { color: palette(mid); border-color: palette(mid); }
        """
        self._success_style = """
            QPushButton {
                background-color: palette(midlight);
                color: palette(highlight);
                border: 1px solid palette(highlight);
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 600;
                min-width: 100px;
            }
        """
        
        self.setText("↻ Refresh")
        self.setStyleSheet(self._default_style)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clicked.connect(self._on_clicked)
    
    def _on_clicked(self):
        """Handle button click"""
        if self._is_refreshing:
            return
        
        # Cancel any pending timer
        if self._status_timer is not None:
            self._status_timer.stop()
            self._status_timer = None
        
        # Emit signal for parent to do actual refresh
        self.refresh_requested.emit()
    
    def start_refresh(self):
        """Call this when starting the refresh operation"""
        self._is_refreshing = True
        self.setEnabled(False)
        self.setText("↻ Refreshing...")
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        QApplication.processEvents()
    
    def finish_refresh(self):
        """Call this when refresh operation is complete"""
        QApplication.restoreOverrideCursor()
        self._is_refreshing = False
        self.setEnabled(True)
        self.setText("✓ Updated")
        self.setStyleSheet(self._success_style)
        QApplication.processEvents()
        
        # Reset button after 2 seconds
        self._status_timer = QTimer()
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._reset)
        self._status_timer.start(2000)
    
    def _reset(self):
        """Reset button to default state"""
        self.setText("↻ Refresh")
        self.setStyleSheet(self._default_style)
        self._status_timer = None

