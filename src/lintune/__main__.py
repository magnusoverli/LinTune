"""
LinTune - Main entry point

EntraID & Intune Setup for Linux
"""

import sys
import os

# Handle imports for both package and frozen (PyInstaller) execution
if getattr(sys, 'frozen', False):
    # Running as frozen executable
    from lintune.gui.main_window import MainWindow
    from lintune.utils.logger import setup_logging, get_log_file
    from lintune import __version__
else:
    # Running as package
    from .gui.main_window import MainWindow
    from .utils.logger import setup_logging, get_log_file
    from . import __version__

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


def main():
    """Main application entry point"""
    
    # Setup logging first
    logger = setup_logging(debug=True)
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Log file: {get_log_file()}")
    
    try:
        # Enable high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("LinTune")
        app.setApplicationVersion(__version__)
        app.setOrganizationName("LinTune")
        logger.info("QApplication created")
        
        # Set application font
        app_font = QFont("Ubuntu", 10)
        app.setFont(app_font)
        
        # Create and show main window
        logger.info("Creating main window...")
        window = MainWindow()
        window.show()
        logger.info("Main window displayed")
        
        # Run application
        logger.info("Entering event loop")
        exit_code = app.exec()
        logger.info(f"Application exited with code {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

