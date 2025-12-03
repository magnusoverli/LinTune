# LinTune Uninstall Guide

## Overview

LinTune provides two levels of removal:

1. **Rollback** - Removes configuration and services (keeps binaries)
2. **Full Uninstall** - Complete removal of everything

## Rollback (Partial Removal)

### What it removes:
- ✓ Stops and disables Himmelblau services
- ✓ Removes systemd service files
- ✓ Removes D-Bus service file
- ✓ Restores NSS/PAM configuration backups
- ✓ Removes Himmelblau configuration directory

### What it keeps:
- Binary files in /usr/bin, /usr/sbin, /usr/lib
- Build dependencies (rust, cargo, etc.)
- Build source files
- GDM (if installed)

### How to use:
```python
from lintune.core.configurator import SystemConfigurator
configurator = SystemConfigurator()
configurator.rollback()
```

## Full Uninstall (Complete Removal)

### What it removes:
- ✓ Everything from Rollback, plus:
- ✓ All Himmelblau binaries:
  - /usr/sbin/himmelblaud
  - /usr/sbin/himmelblaud_tasks
  - /usr/bin/aad-tool
  - /usr/sbin/broker
  - /usr/bin/linux-entra-sso
  - /usr/lib/security/pam_himmelblau.so
  - /usr/lib/libnss_himmelblau.so.2
- ✓ Cache directories:
  - /var/cache/nss-himmelblau
  - /var/cache/himmelblau-policies
- ✓ Build directories:
  - /tmp/himmelblau
  - /tmp/himmelblau-services

### Optional removal:
- Build dependencies (--remove-deps flag)
- GDM display manager (--remove-gdm flag, **DANGEROUS**)

### How to use:

#### Via GUI:
1. Open LinTune
2. Go to Settings
3. Click "Full Uninstall" button
4. Confirm the action
5. Reboot system

#### Via Code:
```python
from lintune.core.installer import Installer

installer = Installer()
installer.full_uninstall(
    remove_gdm=False,         # Set to True to remove GDM (dangerous!)
    remove_build_deps=False   # Set to True to remove rust, cargo, etc.
)
```

## What is NOT removed

Even with full uninstall, these are preserved:
- System logs in /var/log
- User home directory data
- Package manager cache
- System backups (*.backup files)

## Post-Uninstall Steps

1. **Reboot** - Required to fully remove all components
2. **Check logs** - Review /var/log for any issues
3. **Manual cleanup** (if needed):
   ```bash
   # Remove any remaining backup files
   sudo rm -f /etc/nsswitch.conf.backup
   sudo rm -f /etc/pam.d/system-auth.backup
   
   # Remove logs (optional)
   sudo rm -rf /var/log/himmelblau*
   ```

## Troubleshooting

### Services won't stop
```bash
sudo systemctl kill himmelblaud
sudo systemctl kill himmelblaud-tasks
```

### Files still exist after uninstall
Check if files are in use:
```bash
lsof | grep himmelblau
```

Kill processes:
```bash
pkill -9 himmelblaud
```

### Can't restore backups
Manually restore:
```bash
sudo cp /etc/nsswitch.conf.backup /etc/nsswitch.conf
sudo cp /etc/pam.d/system-auth.backup /etc/pam.d/system-auth
```

## Emergency Recovery

If system becomes unbootable after uninstall:

1. Boot into rescue mode
2. Restore PAM configuration:
   ```bash
   sudo cp /etc/pam.d/system-auth.backup /etc/pam.d/system-auth
   ```
3. Reboot

