"""
Sidebar navigation for LinTune

Microsoft Fluent-style icon navigation
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QButtonGroup, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class Sidebar(QFrame):
    """Sidebar navigation widget"""
    
    # Signal emitted when navigation changes
    navigation_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.init_ui()
    
    def init_ui(self):
        """Initialize the sidebar UI"""
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Button group for exclusive selection
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)
        
        # Navigation buttons
        nav_items = [
            ("🏠", "Dashboard", 0),
            ("🖥", "Device", 1),
            ("⚙", "Settings", 2),
            ("📄", "Logs", 3),
            ("ℹ", "About", 4),
        ]
        
        for icon, text, index in nav_items:
            btn = self.create_nav_button(icon, text, index)
            self.button_group.addButton(btn, index)
            layout.addWidget(btn)
        
        # Spacer at bottom
        layout.addStretch()
        
        # Select first button by default
        self.button_group.button(0).setChecked(True)
    
    def create_nav_button(self, icon: str, text: str, index: int) -> QPushButton:
        """
        Create a navigation button
        
        Args:
            icon: Emoji icon
            text: Button text
            index: Button index for navigation
            
        Returns:
            Configured QPushButton
        """
        btn = QPushButton()
        btn.setObjectName("navButton")
        btn.setCheckable(True)
        btn.setToolTip(text)
        
        # Button text with icon on top
        btn_text = f"{icon}\n{text}"
        btn.setText(btn_text)
        
        # Set font for text (icon size controlled by text)
        font = QFont()
        font.setPointSize(9)
        btn.setFont(font)
        
        # Connect click
        btn.clicked.connect(lambda: self.on_button_clicked(index))
        
        return btn
    
    def on_button_clicked(self, index: int):
        """Handle navigation button click"""
        self.navigation_changed.emit(index)

