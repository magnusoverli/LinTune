# LinTune

**EntraID & Intune Setup for Linux**

A cross-distribution tool for enrolling Linux devices in Microsoft EntraID and Intune MDM, with a familiar Microsoft Intune Portal-inspired interface.

![Status: Alpha/PoC](https://img.shields.io/badge/status-alpha-orange)
![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

---

## Features

- 🎨 **Modern UI** - Microsoft Fluent Design-inspired interface
- 🐧 **Cross-Distro** - Supports Arch (untested), CachyOS, Ubuntu (coming soon), Debian (coming soon)
- 🔒 **Enterprise Ready** - Full EntraID authentication & Intune compliance
- 📦 **Easy Installation** - Single executable download, no dependencies
- 🔄 **Automated Setup** - Guided installation process
- 🛡️ **Safe Configuration** - Automatic backups before system changes

---

## Supported Distributions

- ✅ **Arch Linux** (untested)
- ✅ **CachyOS** (tested)
- ✅ **Ubuntu** (coming soon)
- ✅ **Debian** (coming soon)

---

## Quick Start

### For End Users (Recommended)

Download the pre-built executable - no Python installation required!

1. **Download the latest build:**
   - Go to [Actions](https://github.com/magnusoverli/LinTune/actions)
   - Click the latest successful workflow
   - Download `LinTune-linux-x64` artifact

2. **Extract and run:**
   ```bash
   tar -xzf LinTune-linux-x64.tar.gz
   chmod +x LinTune
   ./LinTune
   ```

3. **Optional: Install system-wide:**
   ```bash
   sudo cp LinTune /usr/local/bin/
   sudo chmod +x /usr/local/bin/LinTune
   ```

### For Developers

#### Prerequisites

- One of the supported Linux distributions
- Python 3.10 or higher
- Internet connection
- Sudo access

#### Installation (Development)

```bash
# Clone the repository
git clone https://github.com/magnusoverli/LinTune.git
cd LinTune

# Install dependencies
pip install -r requirements.txt

# Or use Poetry
poetry install

# Run LinTune
python -m src.lintune
```

#### Running the Application

```bash
# From the project root
python -m src.lintune

# Or with Poetry
poetry run lintune
```

#### Building Executable

See [BUILD.md](BUILD.md) for instructions on building the standalone executable.

---

## What LinTune Does

LinTune automates the complex process of enrolling a Linux device in Microsoft's enterprise ecosystem:

1. **Detects** your Linux distribution
2. **Validates** system requirements
3. **Installs** GDM display manager (if needed)
4. **Builds** Himmelblau authentication components
5. **Configures** PAM and NSS for EntraID authentication
6. **Enrolls** device in Intune MDM
7. **Enables** policy enforcement and compliance checking

---

## Current Status (v0.1.0 - PoC)

This is a **Proof of Concept** release demonstrating:

- ✅ Microsoft Fluent Design UI
- ✅ Distribution detection
- ✅ System status validation
- ✅ Navigation and layout
- ⏳ Installation workflow (in progress)
- ⏳ Configuration management (in progress)
- ⏳ Log viewer (planned)
- ⏳ AppImage packaging (planned)

---

## Screenshots

*(Coming soon - PoC screenshots)*

---

## Architecture

```
LinTune/
├── src/lintune/
│   ├── core/          # Business logic
│   │   ├── distro.py      # Distribution detection
│   │   └── validator.py   # System validation
│   ├── gui/           # PyQt6 interface
│   │   ├── main_window.py # Main window
│   │   ├── sidebar.py     # Navigation
│   │   └── dashboard.py   # Dashboard view
│   └── resources/     # Styles, icons, templates
└── origin/            # Original setup documentation
```

---

## Development

### Requirements

- Python 3.10+
- PyQt6
- distro
- psutil
- jinja2

### Running Tests

```bash
pytest tests/
```

### Building Documentation

See `docs/IMPLEMENTATION_PLAN.md` for detailed architecture and roadmap.

---

## Contributing

Contributions welcome! Please read our contributing guidelines (coming soon).

---

## Credits

- **Himmelblau**: The underlying EntraID/Intune client for Linux
  - https://github.com/himmelblau-idm/himmelblau
- **Microsoft Fluent Design**: UI/UX inspiration
- **Original Setup Script**: Based on tested CachyOS configuration

---

## License

MIT License - see LICENSE file for details

---

## Support

- **Documentation**: See `docs/` folder
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

## Roadmap

### v0.1.0 (Current - PoC)
- [x] UI framework
- [x] System detection
- [x] Status display

### v0.2.0
- [ ] Full installation workflow
- [ ] Wizard interface
- [ ] Log viewer

### v0.3.0
- [ ] Settings management
- [ ] Configuration import/export
- [ ] AppImage packaging

### v1.0.0
- [ ] Full cross-distro support
- [ ] Comprehensive error handling
- [ ] Production-ready release

---

**Note**: This is alpha software. Use in test environments first.

