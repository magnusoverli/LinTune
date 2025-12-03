# Building LinTune

## Automated Builds (GitHub Actions)

Every push to the `main` branch automatically builds a standalone executable that can be downloaded and run on any Linux system.

### Downloading Pre-built Binaries

1. Go to the [Actions tab](https://github.com/magnusoverli/LinTune/actions)
2. Click on the latest successful workflow run
3. Download the `LinTune-linux-x64` artifact
4. Extract and run:
   ```bash
   tar -xzf LinTune-linux-x64.tar.gz
   chmod +x LinTune
   ./LinTune
   ```

### Creating a Release

To create a release with downloadable binaries:

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
gh release create v0.1.0 --title "v0.1.0" --notes "Release notes here"
```

The GitHub Action will automatically attach the binary to the release.

## Manual Build

### Prerequisites

```bash
sudo apt-get install -y python3 python3-pip python3-venv
```

### Build Steps

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Build the executable:**
   ```bash
   pyinstaller LinTune.spec
   ```

3. **Run the executable:**
   ```bash
   ./dist/LinTune
   ```

### Distribution

The built executable is located in `dist/LinTune` and can be:
- Copied to any Linux system with similar architecture (x86_64)
- Double-clicked to run (if file manager supports it)
- Run from terminal: `./LinTune`
- Installed to `/usr/local/bin` for system-wide access

### Notes

- The executable includes all Python dependencies
- Users don't need Python installed
- The app requires standard Linux GUI libraries (X11/Wayland)
- Size: ~100-150MB (includes PyQt6 and all dependencies)
