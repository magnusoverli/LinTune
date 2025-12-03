# LinTune Implementation Plan

**Goal:** Cross-distro EntraID & Intune setup tool for Linux  
**Target Distros:** Arch Linux, CachyOS, Ubuntu, Debian  
**Tech Stack:** Python 3.10+ + PyQt6 + AppImage packaging

---

## Technology Stack

### Core
- **Language:** Python 3.10+
- **GUI Framework:** PyQt6
- **Privilege Escalation:** `pkexec` (PolicyKit) - available on all target distros
- **Packaging:** AppImage (single executable, no installation needed)
- **Build Tool:** Poetry for dependency management

### Why This Stack?
1. **Python** - Universal availability, easy system interaction
2. **PyQt6** - Modern, native-looking across DEs (GNOME, KDE, XFCE)
3. **pkexec** - Standard privilege escalation (better UX than sudo in GUI)
4. **AppImage** - Zero-install execution, works on all target distros

### UI Design Philosophy
**Inspired by:** Microsoft Intune Portal / Fluent Design System

**Key Design Elements:**
- Clean, card-based layout with subtle shadows
- Left sidebar navigation with icons
- Microsoft blue accent colors (#0078D4)
- Modern typography (Segoe UI-like fonts)
- Smooth animations and transitions
- Clear status indicators with color coding
- Responsive, spacious layout
- Tab-based content organization

---

## Project Structure

```
LinTune/
├── origin/                          # Original documentation (keep as reference)
├── src/
│   └── lintune/                     # Main package
│       ├── __init__.py
│       ├── __main__.py              # Entry point
│       │
│       ├── core/                    # Business logic (distro-agnostic where possible)
│       │   ├── __init__.py
│       │   ├── distro.py            # Distro detection
│       │   ├── package_manager.py   # Abstract package management
│       │   ├── himmelblau.py        # Build & install Himmelblau
│       │   ├── system_config.py     # NSS/PAM/systemd configuration
│       │   ├── validator.py         # System state validation
│       │   └── steps.py             # Installation step definitions
│       │
│       ├── gui/                     # GUI components
│       │   ├── __init__.py
│       │   ├── main_window.py       # Main application window
│       │   ├── wizard.py            # Step-by-step wizard
│       │   ├── status_panel.py      # System status display
│       │   ├── log_viewer.py        # Real-time log output
│       │   └── dialogs.py           # Confirmation/input dialogs
│       │
│       ├── utils/                   # Utilities
│       │   ├── __init__.py
│       │   ├── privilege.py         # pkexec/sudo handling
│       │   ├── logger.py            # Structured logging
│       │   ├── process.py           # Subprocess management
│       │   └── constants.py         # Constants, paths, etc.
│       │
│       └── resources/               # Embedded resources
│           ├── templates/           # Config file templates
│           │   ├── himmelblau.conf.j2
│           │   ├── system-auth.pam
│           │   └── nsswitch.conf.patch
│           ├── icons/               # Fluent-style icons
│           │   ├── dashboard.svg
│           │   ├── device.svg
│           │   ├── settings.svg
│           │   └── logs.svg
│           └── styles/              # QSS stylesheets
│               ├── fluent.qss       # Main Fluent Design theme
│               ├── colors.qss       # Color scheme
│               └── components.qss   # Individual component styles
│
├── build/                           # Build scripts
│   ├── appimage/
│   │   └── build-appimage.sh
│   └── package/
│       └── lintune.desktop
│
├── tests/                           # Unit & integration tests
│   ├── test_distro.py
│   ├── test_package_manager.py
│   └── test_validator.py
│
├── docs/                            # User documentation
│   ├── README.md
│   ├── DISTRO_SUPPORT.md
│   └── TROUBLESHOOTING.md
│
├── pyproject.toml                   # Poetry config
├── requirements.txt                 # Pip fallback
└── README.md
```

---

## Phase 1: Foundation & Core Logic

### 1.1 Project Setup
**Goal:** Initialize project structure and tooling

**Tasks:**
- [ ] Create directory structure
- [ ] Setup Poetry/pip environment
- [ ] Create pyproject.toml with dependencies
- [ ] Add .gitignore, README
- [ ] Initialize git repository

**Dependencies:**
```toml
[tool.poetry.dependencies]
python = "^3.10"
PyQt6 = "^6.6.0"
PyQt6-Qt6 = "^6.6.0"
jinja2 = "^3.1.0"      # Config template rendering
distro = "^1.9.0"       # Distro detection
psutil = "^5.9.0"       # Process monitoring
qt-material = "^2.14"   # Material/Fluent styling helpers (optional)
```

**Deliverable:** Working Python project skeleton

---

### 1.2 Distro Detection
**Goal:** Reliably detect target distributions

**File:** `src/lintune/core/distro.py`

**Implementation:**
```python
from enum import Enum
import distro

class SupportedDistro(Enum):
    ARCH = "arch"
    CACHYOS = "cachyos"
    UBUNTU = "ubuntu"
    DEBIAN = "debian"
    UNSUPPORTED = "unsupported"

class DistroDetector:
    def detect(self) -> SupportedDistro:
        """Detect current distribution"""
        # Use /etc/os-release ID field
        
    def get_version(self) -> str:
        """Get distro version"""
        
    def is_supported(self) -> bool:
        """Check if distro is supported"""
```

**Testing:**
- Test on Arch, Ubuntu, Debian VMs
- Handle edge cases (derivatives, custom distros)

**Deliverable:** Reliable distro detection

---

### 1.3 Package Manager Abstraction
**Goal:** Unified interface for package operations

**File:** `src/lintune/core/package_manager.py`

**Implementation:**
```python
from abc import ABC, abstractmethod

class PackageManager(ABC):
    @abstractmethod
    def update_repos(self):
        """Update package repositories"""
        
    @abstractmethod
    def install(self, packages: list[str]):
        """Install packages"""
        
    @abstractmethod
    def is_installed(self, package: str) -> bool:
        """Check if package is installed"""

class PacmanManager(PackageManager):
    """Arch/CachyOS"""
    def install(self, packages: list[str]):
        # pacman -S --noconfirm --needed {packages}

class AptManager(PackageManager):
    """Ubuntu/Debian"""
    def install(self, packages: list[str]):
        # apt update && apt install -y {packages}

def get_package_manager(distro: SupportedDistro) -> PackageManager:
    """Factory to get appropriate package manager"""
```

**Package Mapping:**
| Common Name | Arch/CachyOS | Ubuntu/Debian |
|-------------|--------------|---------------|
| rust | rust | rustc |
| cargo | cargo | cargo |
| pkg-config | pkg-config | pkg-config |
| openssl | openssl | libssl-dev |
| sqlite | sqlite | libsqlite3-dev |
| dbus | dbus | libdbus-1-dev |
| tpm2-tss | tpm2-tss | libtss2-dev |
| git | git | git |
| build-essential | base-devel | build-essential |
| python3 | python | python3 |
| cronie | cronie | cron |
| gdm | gdm | gdm3 |

**Deliverable:** Working package abstraction layer

---

### 1.4 System Validator
**Goal:** Check system state at each step

**File:** `src/lintune/core/validator.py`

**Implementation:**
```python
from dataclasses import dataclass
from enum import Enum

class StepStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class SystemStatus:
    display_manager: str  # "gdm", "sddm", etc.
    gdm_installed: bool
    gdm_enabled: bool
    dependencies_installed: bool
    himmelblau_installed: bool
    services_configured: bool
    nss_configured: bool
    pam_configured: bool
    domain_configured: str | None
    cronie_running: bool
    himmelblaud_running: bool
    
class SystemValidator:
    def get_status(self) -> SystemStatus:
        """Get current system state"""
        
    def check_gdm(self) -> bool:
        """Check if GDM is installed and enabled"""
        
    def check_dependencies(self) -> dict[str, bool]:
        """Check required packages"""
        
    def check_himmelblau(self) -> bool:
        """Check if Himmelblau is installed"""
        
    def check_services(self) -> bool:
        """Check systemd services exist"""
```

**Deliverable:** Comprehensive system state checking

---

## Phase 2: Installer Core

### 2.1 Himmelblau Builder
**Goal:** Build and install Himmelblau from source

**File:** `src/lintune/core/himmelblau.py`

**Implementation:**
```python
class HimmelblauBuilder:
    def __init__(self, progress_callback=None):
        self.repo_url = "https://github.com/himmelblau-idm/himmelblau"
        self.build_dir = "/tmp/himmelblau"
        self.progress_callback = progress_callback
        
    def clone_repo(self):
        """Clone Himmelblau repository"""
        
    def build(self):
        """Build with cargo (with progress updates)"""
        # Parse cargo output for progress
        
    def install_binaries(self):
        """Install built binaries to system paths"""
        
    def cleanup(self):
        """Remove build directory"""
```

**Progress Reporting:**
- Parse cargo build output
- Emit progress updates (0-100%)
- Handle build failures gracefully

**Deliverable:** Reliable Himmelblau build process

---

### 2.2 System Configuration
**Goal:** Configure PAM, NSS, systemd services

**File:** `src/lintune/core/system_config.py`

**Implementation:**
```python
class SystemConfigurator:
    def __init__(self, distro: SupportedDistro):
        self.distro = distro
        
    def configure_nss(self):
        """Modify /etc/nsswitch.conf"""
        # Backup original
        # Add himmelblau to passwd/group lines
        
    def configure_pam(self):
        """Configure PAM authentication"""
        # Backup original
        # Install new system-auth config
        
    def install_systemd_services(self):
        """Install and configure systemd services"""
        # Generate service files
        # Modify for Arch (comment HSM PIN lines)
        # Install to /etc/systemd/system/
        # daemon-reload
        
    def create_himmelblau_config(self, domain: str, 
                                  grant_sudo: bool = True):
        """Create /etc/himmelblau/himmelblau.conf"""
        # Use Jinja2 template
        
    def setup_cronie(self):
        """Install and enable cronie/cron"""
```

**Safety Features:**
- Always backup before modifying
- Provide rollback functionality
- Validate configs before applying

**Deliverable:** Safe system configuration

---

### 2.3 Installation Steps
**Goal:** Define discrete installation steps

**File:** `src/lintune/core/steps.py`

**Implementation:**
```python
from enum import Enum
from dataclasses import dataclass
from typing import Callable

class InstallStep(Enum):
    CHECK_DISTRO = "check_distro"
    INSTALL_GDM = "install_gdm"
    INSTALL_DEPS = "install_deps"
    BUILD_HIMMELBLAU = "build_himmelblau"
    CONFIGURE_SYSTEM = "configure_system"
    SET_DOMAIN = "set_domain"
    SETUP_CRONIE = "setup_cronie"
    START_SERVICES = "start_services"
    VERIFY = "verify"

@dataclass
class Step:
    id: InstallStep
    name: str
    description: str
    required: bool
    execute: Callable
    validate: Callable
    revertible: bool = True
    
class StepExecutor:
    def __init__(self):
        self.steps = self._define_steps()
        self.current_step = None
        
    def _define_steps(self) -> list[Step]:
        """Define all installation steps"""
        
    def execute_step(self, step: InstallStep):
        """Execute a single step"""
        
    def execute_all(self):
        """Execute all required steps"""
        
    def revert_step(self, step: InstallStep):
        """Revert a step (if possible)"""
```

**Deliverable:** Modular step execution system

---

## Phase 3: GUI Implementation

### 3.1 Main Window (Intune Portal Style)
**Goal:** Create main application window mimicking Microsoft Intune Portal

**File:** `src/lintune/gui/main_window.py`

**UI Layout (Intune Portal Inspired):**
```
┌────────────────────────────────────────────────────────────────┐
│  LinTune                                    [−] [□] [×]        │
├───┬────────────────────────────────────────────────────────────┤
│ 🏠│  Dashboard                                                 │
│   │ ┌─────────────────────────────────────────────────────┐   │
│ 🖥│ │  Device enrollment                                   │   │
│   │ │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │   │
│ ⚙│ │  │ ●●○○○        │  │   Status      │  │   Ready    │ │   │
│   │ │  │              │  │               │  │            │ │   │
│ 📄│ │  │ Not enrolled │  │ ✓ Arch Linux  │  │ ✓ GDM      │ │   │
│   │ │  │              │  │ ○ Himmelblau  │  │ ○ Enrolled │ │   │
│   │ │  └──────────────┘  └──────────────┘  └────────────┘ │   │
│   │ └─────────────────────────────────────────────────────┘   │
│   │                                                            │
│   │ ┌─────────────────────────────────────────────────────┐   │
│   │ │  Get started                                         │   │
│   │ │                                                      │   │
│   │ │  Configure this device for EntraID authentication   │   │
│   │ │  and Intune management.                             │   │
│   │ │                                                      │   │
│   │ │  [Begin enrollment] [Advanced setup]                │   │
│   │ └─────────────────────────────────────────────────────┘   │
├───┴────────────────────────────────────────────────────────────┤
│  Ready                                    v1.0.0 │ ⓘ Arch     │
└────────────────────────────────────────────────────────────────┘
```

**Navigation Sidebar:**
- 🏠 **Dashboard** - Overview and quick start
- 🖥 **Devices** - Device status and configuration
- ⚙ **Settings** - Domain, policies, advanced options
- 📄 **Logs** - Detailed operation logs
- ℹ **About** - Version, help, troubleshooting

**Color Scheme (Microsoft Fluent):**
- Primary: `#0078D4` (Microsoft Blue)
- Success: `#107C10` (Green)
- Warning: `#FFB900` (Yellow)
- Error: `#E81123` (Red)
- Background: `#F3F2F1` (Light gray)
- Cards: `#FFFFFF` with `box-shadow: 0 2px 4px rgba(0,0,0,0.1)`
- Text: `#323130` (Dark gray)
- Secondary text: `#605E5C` (Medium gray)

**Features:**
- Card-based layout with elevation shadows
- Smooth hover effects and transitions
- Icon-based navigation
- Status indicators with color coding
- Progress visualization
- Responsive spacing (16px/24px/32px grid)

**Deliverable:** Intune Portal-style main window

---

### 3.2 Wizard Interface
**Goal:** Step-by-step guided installation

**File:** `src/lintune/gui/wizard.py`

**Wizard Steps (Intune Enrollment Style):**

**Step Indicator (Top):**
```
●─────●─────○─────○─────○─────○
Check  Prep  Build Config Enroll Done
```

1. **Compatibility Check**
   ```
   ┌────────────────────────────────────────┐
   │  Check system compatibility            │
   │                                        │
   │  ✓ Operating System: Arch Linux        │
   │  ✓ Architecture: x86_64                │
   │  ⚠ Display Manager: SDDM (GDM needed)  │
   │                                        │
   │  [Install GDM]          [Next]         │
   └────────────────────────────────────────┘
   ```

2. **Prerequisites & Dependencies**
   ```
   ┌────────────────────────────────────────┐
   │  Installing prerequisites              │
   │                                        │
   │  ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░ 47%            │
   │  Installing rust (8/15)                │
   │                                        │
   │  [Cancel]                              │
   └────────────────────────────────────────┘
   ```

3. **Build Authentication Components**
   ```
   ┌────────────────────────────────────────┐
   │  Building Himmelblau                   │
   │                                        │
   │  ▓▓▓▓▓▓▓▓░░░░░░░░░░░░ 35%            │
   │  Compiling broker (142/405)            │
   │                                        │
   │  Estimated time: 1m 23s                │
   │                                        │
   │  ▼ Show build output                   │
   └────────────────────────────────────────┘
   ```

4. **Configure System**
   ```
   ┌────────────────────────────────────────┐
   │  System configuration                  │
   │                                        │
   │  The following will be modified:       │
   │  • PAM authentication                  │
   │  • NSS name resolution                 │
   │  • Systemd services                    │
   │                                        │
   │  ⓘ Backups will be created             │
   │                                        │
   │  [Back]                [Configure]     │
   └────────────────────────────────────────┘
   ```

5. **Connect to EntraID**
   ```
   ┌────────────────────────────────────────┐
   │  Connect to your organization          │
   │                                        │
   │  EntraID Domain                        │
   │  ┌──────────────────────────────────┐ │
   │  │ company.onmicrosoft.com          │ │
   │  └──────────────────────────────────┘ │
   │                                        │
   │  ☑ Grant sudo access to EntraID users │
   │                                        │
   │  [Back]                [Connect]       │
   └────────────────────────────────────────┘
   ```

6. **Enrollment Complete**
   ```
   ┌────────────────────────────────────────┐
   │  ✓ Enrollment successful               │
   │                                        │
   │  Your device is now managed by:        │
   │  company.onmicrosoft.com               │
   │                                        │
   │  Next steps:                           │
   │  1. Log out of your current session    │
   │  2. At login, click "Not listed?"      │
   │  3. Enter: user@company.com            │
   │  4. Complete MFA authentication        │
   │                                        │
   │  [View logs]           [Finish]        │
   └────────────────────────────────────────┘
   ```

**UI Components:**
```python
class WizardPage(QWidget):
    """Base class for wizard pages"""
    
class WelcomePage(WizardPage):
    """Welcome and compatibility check"""
    
class DependenciesPage(WizardPage):
    """Install dependencies with progress"""
    
class BuildPage(WizardPage):
    """Build Himmelblau with live output"""
    
class DomainConfigPage(WizardPage):
    """Configure EntraID domain"""
    
class CompletionPage(WizardPage):
    """Show login instructions"""
```

**Deliverable:** Complete wizard flow

---

### 3.3 Status Panel
**Goal:** Real-time system status display

**File:** `src/lintune/gui/status_panel.py`

**Features:**
- Color-coded status indicators
- Animated transitions
- Refresh button
- Detailed tooltips

**Status Items:**
- Display Manager (GDM/other)
- Dependencies installed
- Himmelblau version
- Services status
- Configuration state
- Domain configured
- Daemon running

**Deliverable:** Interactive status panel

---

### 3.4 Log Viewer
**Goal:** Real-time log display

**File:** `src/lintune/gui/log_viewer.py`

**Features:**
- Color-coded log levels
- Auto-scroll (with pause)
- Search/filter
- Export to file
- Clear button

**Deliverable:** Functional log viewer

---

## Phase 4: Utilities & Polish

### 4.1 Privilege Escalation
**Goal:** Handle root operations securely

**File:** `src/lintune/utils/privilege.py`

**Implementation:**
```python
class PrivilegeManager:
    def __init__(self):
        self.use_pkexec = self._check_pkexec()
        
    def _check_pkexec(self) -> bool:
        """Check if pkexec is available"""
        
    def run_as_root(self, command: list[str]) -> subprocess.CompletedProcess:
        """Run command with elevated privileges"""
        # Use pkexec if available, fallback to sudo
        
    def create_root_session(self):
        """Create a persistent root session"""
        # For multiple operations
```

**PolicyKit Integration:**
- Create .policy file for pkexec
- Better UX than sudo (graphical password prompt)

**Deliverable:** Secure privilege handling

---

### 4.2 Logging System
**Goal:** Structured logging with GUI integration

**File:** `src/lintune/utils/logger.py`

**Features:**
- Multiple output targets (file, GUI, console)
- Structured logging (JSON option)
- Log rotation
- Debug mode

**Deliverable:** Comprehensive logging

---

### 4.3 Process Management
**Goal:** Monitor long-running processes

**File:** `src/lintune/utils/process.py`

**Features:**
- Real-time output capture
- Progress estimation
- Timeout handling
- Graceful cancellation

**Deliverable:** Robust process handling

---

## Phase 5: Packaging & Distribution

### 5.1 AppImage Creation
**Goal:** Single-file executable

**File:** `build/appimage/build-appimage.sh`

**Process:**
1. Create AppDir structure
2. Bundle Python + dependencies
3. Include .desktop file
4. Run appimagetool

**AppImage Structure:**
```
LinTune.AppDir/
├── AppRun                    # Entry script
├── lintune.desktop
├── usr/
│   ├── bin/
│   │   └── python3
│   ├── lib/
│   │   └── python3.10/
│   └── share/
│       ├── applications/
│       └── icons/
└── .DirIcon
```

**Build Script:**
```bash
#!/bin/bash
# Build AppImage for LinTune

# 1. Create virtual environment
# 2. Install dependencies
# 3. Create AppDir
# 4. Bundle everything
# 5. Run appimagetool
```

**Deliverable:** Working AppImage

---

### 5.2 Desktop Integration
**Goal:** Proper desktop environment integration

**File:** `build/package/lintune.desktop`

```ini
[Desktop Entry]
Name=LinTune
Comment=EntraID & Intune Setup for Linux
Exec=lintune
Icon=lintune
Terminal=false
Type=Application
Categories=System;Settings;
Keywords=entraid;azure;intune;authentication;
```

**Deliverable:** Desktop file

---

### 5.3 Documentation
**Goal:** Comprehensive user documentation

**Files:**
- `docs/README.md` - Overview and quick start
- `docs/DISTRO_SUPPORT.md` - Distro-specific notes
- `docs/TROUBLESHOOTING.md` - Common issues
- `docs/DEVELOPMENT.md` - Developer guide

**Deliverable:** Complete documentation

---

## Phase 6: Testing & Quality Assurance

### 6.1 Unit Tests
**Coverage:**
- Distro detection
- Package manager operations
- System validation
- Configuration generation

**Tools:**
- pytest
- pytest-qt (GUI testing)
- pytest-mock

---

### 6.2 Integration Tests
**Test Scenarios:**
- Full installation on each distro (VM)
- Rollback functionality
- Error handling
- Edge cases

---

### 6.3 Manual Testing
**Test Matrix:**

| Test | Arch | CachyOS | Ubuntu | Debian |
|------|------|---------|--------|--------|
| Fresh install | ☐ | ☐ | ☐ | ☐ |
| With SDDM installed | ☐ | ☐ | ☐ | ☐ |
| Partial install recovery | ☐ | ☐ | ☐ | ☐ |
| Rollback | ☐ | ☐ | ☐ | ☐ |
| AppImage execution | ☐ | ☐ | ☐ | ☐ |

---

## Distro-Specific Considerations

### Arch Linux / CachyOS
- ✓ Already tested and working
- Use `pacman` for package management
- HSM PIN credentials must be disabled
- `cronie` package name

### Ubuntu
- **GDM Package:** `gdm3` (not `gdm`)
- **Service Name:** `gdm3.service` or `gdm.service` (varies by version)
- **Build Dependencies:** Different package names (see table above)
- **PAM Path:** Same (`/etc/pam.d/system-auth` may need symlinking)
- **SystemD:** Fully supported
- **Versions:** Test on LTS releases (22.04, 24.04)

### Debian
- **Similar to Ubuntu** but more conservative packages
- **GDM Package:** `gdm3`
- **Stable vs Testing:** May need different approaches
- **Build Dependencies:** Similar to Ubuntu
- **Test Versions:** Debian 11 (Bullseye), 12 (Bookworm)

### Cross-Distro Challenges

**Display Manager:**
- Arch: `gdm` package, `gdm.service`
- Ubuntu/Debian: `gdm3` package, `gdm3.service` or `gdm.service`
- **Solution:** Detect and handle both naming schemes

**PAM Configuration:**
- Ubuntu may use `common-auth` instead of `system-auth`
- **Solution:** Detect PAM structure and adapt

**Python:**
- Arch: `python` is Python 3
- Ubuntu/Debian: `python3` explicitly
- **Solution:** Use `python3` everywhere

---

## Risk Mitigation

### Critical Risks

1. **PAM Misconfiguration → System Lockout**
   - **Mitigation:** Always backup, test in VM first, provide recovery instructions

2. **Build Failure**
   - **Mitigation:** Clear error messages, link to troubleshooting, allow retry

3. **Partial Installation**
   - **Mitigation:** Transaction-like steps, rollback capability, resume from failure

4. **Privilege Escalation Issues**
   - **Mitigation:** Test both pkexec and sudo paths, clear error messages

---

## Success Criteria

### Minimum Viable Product (MVP)
- ✓ Works on all 4 target distros
- ✓ Guided installation (wizard)
- ✓ System validation before/after
- ✓ Basic error handling
- ✓ AppImage packaging

### Version 1.0
- ✓ All MVP features
- ✓ Comprehensive error handling
- ✓ Rollback functionality
- ✓ Detailed logging
- ✓ User documentation
- ✓ Tested on all distros

### Future Enhancements
- Support for more distros (Fedora, openSUSE)
- Configuration import/export
- Automated compliance checking
- Policy management UI
- Update mechanism

---

## Timeline Estimate

| Phase | Estimated Time | Deliverables |
|-------|---------------|--------------|
| 1. Foundation | 1-2 days | Project setup, core logic |
| 2. Installer Core | 2-3 days | Build system, configuration |
| 3. GUI | 3-4 days | All UI components |
| 4. Utilities | 1 day | Logging, privileges |
| 5. Packaging | 1-2 days | AppImage, docs |
| 6. Testing | 2-3 days | Testing on all distros |
| **Total** | **10-15 days** | Production-ready v1.0 |

---

## Getting Started

### Immediate Next Steps
1. Create project structure
2. Setup Poetry environment
3. Implement distro detection
4. Create package manager abstraction
5. Build simple CLI prototype
6. Add GUI on top

### Development Order
1. **Core first:** Get installation logic working (CLI mode)
2. **GUI second:** Wrap working logic in interface
3. **Polish third:** Logging, error handling, edge cases
4. **Package last:** AppImage once everything works

---

## Questions to Resolve

1. **Python Version:** ✓ Require 3.10+ (for match/case, better typing)
2. **GUI Style:** ✓ Fluent Design (Microsoft Intune Portal inspired)
3. **Update Mechanism:** Auto-update AppImage or manual download?
4. **Analytics/Telemetry:** Any usage tracking? (Privacy considerations)
5. **License:** What license for the project?
6. **Icon Set:** Use Fluent System Icons (Microsoft's open-source icons)?

---

## Resources Needed

### Development
- VMs for each distro (Arch, CachyOS, Ubuntu, Debian)
- Test EntraID tenant
- Qt Designer (for UI mockups)

### Deployment
- GitHub repository
- CI/CD pipeline (GitHub Actions)
- Release hosting (GitHub Releases)

---

