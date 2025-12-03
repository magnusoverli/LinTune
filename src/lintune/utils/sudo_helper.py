"""
Sudo helper for LinTune

Handles elevated privilege execution with password caching.
"""

import subprocess
import threading
from typing import Optional, List
from pathlib import Path


class SudoHelper:
    """Helper for running commands with sudo"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize sudo helper"""
        if self._initialized:
            return
            
        self.password: Optional[str] = None
        self.validated = False
        self._initialized = True
    
    def set_password(self, password: str) -> bool:
        """
        Set and validate sudo password
        
        Args:
            password: Sudo password
            
        Returns:
            True if password is valid
        """
        try:
            # Test password with a simple command
            result = subprocess.run(
                ["sudo", "-S", "-k", "true"],
                input=f"{password}\n",
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.password = password
                self.validated = True
                # Keep sudo timestamp alive
                subprocess.run(
                    ["sudo", "-S", "-v"],
                    input=f"{password}\n",
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return True
            else:
                self.password = None
                self.validated = False
                return False
                
        except Exception as e:
            print(f"Password validation failed: {e}")
            self.password = None
            self.validated = False
            return False
    
    def refresh_sudo(self) -> bool:
        """
        Refresh sudo timestamp to prevent timeout
        
        Returns:
            True if successful
        """
        if not self.validated or not self.password:
            return False
            
        try:
            result = subprocess.run(
                ["sudo", "-S", "-v"],
                input=f"{self.password}\n",
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def run(self, cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
        """
        Run command with sudo
        
        Args:
            cmd: Command to run (without sudo prefix)
            **kwargs: Additional arguments for subprocess.run
            
        Returns:
            CompletedProcess instance
        """
        if not self.validated or not self.password:
            raise RuntimeError("Sudo password not set or invalid")
        
        # Refresh sudo timestamp before long-running commands
        self.refresh_sudo()
        
        # Prepend sudo -S to command
        sudo_cmd = ["sudo", "-S"] + cmd
        
        # Add password to stdin if not already provided
        if "input" not in kwargs:
            kwargs["input"] = f"{self.password}\n"
        if "text" not in kwargs:
            kwargs["text"] = True
        if "capture_output" not in kwargs:
            kwargs["capture_output"] = True
            
        return subprocess.run(sudo_cmd, **kwargs)
    
    def clear(self):
        """Clear cached password"""
        self.password = None
        self.validated = False
        
        # Clear sudo timestamp
        try:
            subprocess.run(["sudo", "-k"], timeout=5)
        except:
            pass


# Global singleton instance
_sudo_helper = SudoHelper()


def get_sudo_helper() -> SudoHelper:
    """Get the global SudoHelper instance"""
    return _sudo_helper


def run_with_sudo(cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
    """
    Convenience function to run command with sudo
    
    Args:
        cmd: Command to run (without sudo prefix)
        **kwargs: Additional arguments for subprocess.run
        
    Returns:
        CompletedProcess instance
    """
    return _sudo_helper.run(cmd, **kwargs)
