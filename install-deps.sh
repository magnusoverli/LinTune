#!/bin/bash
# Install dependencies for LinTune
# Run with: sudo ./install-deps.sh

set -e

echo "Installing LinTune dependencies..."

# Detect distro
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO_ID=$ID
else
    echo "Error: Could not detect distribution"
    exit 1
fi

echo "Detected distribution: $DISTRO_ID"

# Install based on distro
case "$DISTRO_ID" in
    arch|cachyos)
        echo "Installing with pacman..."
        pacman -S --noconfirm --needed \
            python \
            python-pyqt6 \
            python-jinja \
            python-distro \
            python-psutil
        ;;
    ubuntu|debian)
        echo "Installing with apt..."
        apt update
        apt install -y \
            python3 \
            python3-pyqt6 \
            python3-jinja2 \
            python3-distro \
            python3-psutil
        ;;
    *)
        echo "Unsupported distribution: $DISTRO_ID"
        echo "Please install manually:"
        echo "  - Python 3.10+"
        echo "  - PyQt6"
        echo "  - jinja2"
        echo "  - distro"
        echo "  - psutil"
        exit 1
        ;;
esac

echo ""
echo "✓ Dependencies installed successfully!"
echo ""
echo "Run LinTune with:"
echo "  python -m src.lintune"
echo ""

