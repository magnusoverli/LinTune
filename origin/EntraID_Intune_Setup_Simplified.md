# EntraID & Intune Setup for CachyOS/Arch Linux

**Simplified setup guide - confirmed working steps only**

---

## Prerequisites

- CachyOS/Arch Linux with GDM display manager
- Corporate EntraID tenant with Intune license
- Network access to Microsoft cloud services
- Sudo access

---

## Step 1: Install Build Dependencies

```bash
sudo pacman -Sy --noconfirm rust cargo pkg-config openssl sqlite dbus tpm2-tss git base-devel
```

**Packages:**
- `rust`, `cargo`: Rust toolchain for building Himmelblau
- `pkg-config`: Build configuration
- `openssl`: Cryptography
- `sqlite`: Database support
- `dbus`: IPC
- `tpm2-tss`: TPM 2.0 support
- `git`: Clone source repository
- `base-devel`: Build essentials

**Automation:** Fully automatable

---

## Step 2: Clone and Build Himmelblau

```bash
cd /tmp
git clone https://github.com/himmelblau-idm/himmelblau
cd himmelblau
HIMMELBLAU_ALLOW_MISSING_SELINUX=1 cargo build --release
```

**Note:** `HIMMELBLAU_ALLOW_MISSING_SELINUX=1` is required because Arch uses AppArmor, not SELinux.

**Build time:** ~2 minutes on modern hardware

**Built binaries:**
- `himmelblaud` - Main authentication daemon
- `himmelblaud_tasks` - Background task processor
- `aad-tool` - CLI management tool
- `broker` - Identity broker for MFA
- `linux-entra-sso` - SSO integration
- `libpam_himmelblau.so` - PAM module
- `libnss_himmelblau.so` - NSS module

**Automation:** Fully automatable

---

## Step 3: Install Binaries

```bash
sudo install -m 755 /tmp/himmelblau/target/release/himmelblaud /usr/sbin/himmelblaud
sudo install -m 755 /tmp/himmelblau/target/release/himmelblaud_tasks /usr/sbin/himmelblaud_tasks
sudo install -m 755 /tmp/himmelblau/target/release/aad-tool /usr/bin/aad-tool
sudo install -m 755 /tmp/himmelblau/target/release/broker /usr/sbin/broker
sudo install -m 755 /tmp/himmelblau/target/release/linux-entra-sso /usr/bin/linux-entra-sso
sudo install -m 755 /tmp/himmelblau/target/release/libpam_himmelblau.so /usr/lib/security/pam_himmelblau.so
sudo install -m 755 /tmp/himmelblau/target/release/libnss_himmelblau.so /usr/lib/libnss_himmelblau.so.2
```

**Automation:** Fully automatable

---

## Step 4: Install Systemd Services

Generate service files using the included script (auto-detects systemd version):

```bash
python3 /tmp/himmelblau/scripts/gen_servicefiles.py --out-dir /tmp/himmelblau-services
```

Modify for Arch (comment out HSM PIN lines):

```bash
sed -i 's/^LoadCredentialEncrypted=/#LoadCredentialEncrypted=/' /tmp/himmelblau-services/himmelblaud.service
sed -i 's/^Environment=HIMMELBLAU_HSM_PIN_PATH=/#Environment=HIMMELBLAU_HSM_PIN_PATH=/' /tmp/himmelblau-services/himmelblaud.service
```

Install services:

```bash
sudo mkdir -p /etc/himmelblau
sudo cp /tmp/himmelblau-services/himmelblaud.service /etc/systemd/system/himmelblaud.service
sudo cp /tmp/himmelblau-services/himmelblaud-tasks.service /etc/systemd/system/himmelblaud-tasks.service
sudo install -m 644 /tmp/himmelblau/platform/debian/com.microsoft.identity.broker1.service /usr/share/dbus-1/services/com.microsoft.identity.broker1.service
sudo systemctl daemon-reload
```

**Note:** The HSM PIN credentials must be disabled for basic Arch setup.

**Automation:** Fully automatable

---

## Step 5: Create Required Directories

```bash
sudo mkdir -p /var/cache/nss-himmelblau /var/cache/himmelblau-policies /etc/krb5.conf.d
```

These directories are used for:
- `nss-himmelblau`: NSS caching
- `himmelblau-policies`: Intune policy storage
- `krb5.conf.d`: Kerberos configuration

**Automation:** Fully automatable

---

## Step 6: Configure NSS (Name Service Switch)

Backup and modify nsswitch.conf to add himmelblau:

```bash
sudo cp /etc/nsswitch.conf /etc/nsswitch.conf.backup
sudo sed -i 's/^passwd:.*/passwd: files systemd himmelblau/' /etc/nsswitch.conf
sudo sed -i 's/^group:.*/group: files [SUCCESS=merge] systemd himmelblau/' /etc/nsswitch.conf
```

**Verify:**
```bash
grep -E "^(passwd|group):" /etc/nsswitch.conf
# Should show:
# passwd: files systemd himmelblau
# group: files [SUCCESS=merge] systemd himmelblau
```

This allows the system to resolve EntraID users and groups.

**Automation:** Fully automatable (backup recommended)

---

## Step 7: Configure PAM (Authentication)

**CRITICAL:** Backup first - incorrect PAM config can lock you out!

```bash
sudo cp /etc/pam.d/system-auth /etc/pam.d/system-auth.backup
```

Create new system-auth with himmelblau (save as `/tmp/system-auth` then copy):

```
#%PAM-1.0

auth       required                    pam_faillock.so      preauth
-auth      [success=3 default=ignore]  pam_systemd_home.so
auth       [success=2 default=ignore]  pam_himmelblau.so    ignore_unknown_user try_first_pass
auth       [success=1 default=bad]     pam_unix.so          try_first_pass nullok
auth       [default=die]               pam_faillock.so      authfail
auth       optional                    pam_permit.so
auth       required                    pam_env.so
auth       required                    pam_faillock.so      authsucc

-account   [success=2 default=ignore]  pam_systemd_home.so
account    [success=1 default=ignore]  pam_himmelblau.so    ignore_unknown_user
account    required                    pam_unix.so
account    optional                    pam_permit.so
account    required                    pam_time.so

-password  [success=2 default=ignore]  pam_systemd_home.so
password   [success=1 default=ignore]  pam_himmelblau.so    ignore_unknown_user
password   required                    pam_unix.so          try_first_pass nullok shadow
password   optional                    pam_permit.so

-session   optional                    pam_systemd_home.so
session    optional                    pam_himmelblau.so
session    required                    pam_limits.so
session    required                    pam_unix.so
session    optional                    pam_permit.so
```

Install the config:
```bash
sudo cp /tmp/system-auth /etc/pam.d/system-auth
```

**Key points:**
- Use `try_first_pass` (not `use_first_pass`) - allows password prompting
- `ignore_unknown_user` - falls back to local auth for non-EntraID users
- `[success=N]` values adjusted for proper stack flow

**Automation:** Automatable but RISKY - backup essential, test sudo after

---

## Step 8: Create Himmelblau Configuration

Create `/etc/himmelblau/himmelblau.conf`:

```ini
[global]
# CRITICAL: Use "domains" (plural) not "domain"
domains = YOUR_DOMAIN_HERE

# Local groups that EntraID users should be added to
local_groups = users,wheel

# Home directory attributes
home_attr = CN
home_alias = CN

# Use /etc/skel for new home directories
use_etc_skel = true

# Disable Hello PIN for initial setup (use MFA instead)
enable_hello = false

# Enable debug logging (helpful for troubleshooting)
debug = true

# CRITICAL: Enable MDM Intune compliance enforcement
apply_policy = true
```

**Replace `YOUR_DOMAIN_HERE`** with your EntraID domain (e.g., `tv2.no` or `company.onmicrosoft.com`)

**Key settings:**
- `domains` (PLURAL!) - Your EntraID tenant domain
- `local_groups = users,wheel` - Gives EntraID users sudo access
- `apply_policy = true` - Required for Intune enrollment

**Automation:** Requires user input (domain name)

---

## Step 9: Install Cronie

Cronie is required for Intune policy scheduling:

```bash
sudo pacman -S --noconfirm cronie
sudo systemctl enable --now cronie.service
```

Without cronie, Intune enrollment will fail with "Failed to create cron file" errors.

**Automation:** Fully automatable

---

## Step 10: Start Himmelblau Services

```bash
sudo systemctl enable himmelblaud himmelblaud-tasks
sudo systemctl start himmelblaud
```

Note: `himmelblaud-tasks` starts automatically via `Upholds=` in the service file.

**Verify:**
```bash
systemctl status himmelblaud.service
systemctl status himmelblaud-tasks.service
aad-tool status  # Should output: working!
```

**Automation:** Fully automatable

---

## Step 11: First Login via GDM (User Interaction Required)

This step triggers device registration and Intune enrollment.

### Login Process:

1. **Log out** from your current session
2. At **GDM login screen**, click "Not listed?" (or equivalent) to enter a username
3. Enter your **full EntraID email**: `username@your-domain.com`
4. Enter your **corporate password**
5. A **2-digit MFA code** appears on screen
6. Open **Microsoft Authenticator** on your phone
7. **Wait 10-30 seconds** for notification (it's delayed - be patient!)
8. Enter the code from screen into Authenticator
9. **Approve** the authentication
10. Login completes and home directory is created

### IMPORTANT: First Attempt May Fail

**Known issue:** The first login attempt may skip the password prompt and go directly to MFA, which will fail because no password was provided. The MFA notification will not trigger in this case.

**Solution:** If this happens:
1. **Cancel** the login attempt
2. Click "Not listed?" again
3. Re-enter your email address
4. This time you should be prompted for your **password** first
5. After entering password, the MFA code will display
6. The Authenticator push notification should arrive within 10-30 seconds
7. Complete the MFA and login will succeed

### What Happens on First Login:

- Device registers with EntraID
- Intune MDM enrollment initiated (if `apply_policy = true`)
- Home directory created from `/etc/skel`
- User added to configured local groups (users, wheel)
- EntraID group memberships synced

### Timing Notes:

- Password prompt: Should appear immediately (if not, cancel and retry)
- MFA code display: Immediate after password entry
- Authenticator notification: 10-30 seconds (be patient!)
- Total successful login time: ~30 seconds

**Automation:** NOT automatable - requires user interaction (MFA approval)

---

## Step 12: Verify Enrollment

After successful login, verify everything is working:

### Check Services:
```bash
systemctl status himmelblaud.service
systemctl status himmelblaud-tasks.service
systemctl status cronie.service
aad-tool status  # Should output: working!
```

**Expected:** All services should be `active (running)` and aad-tool should output `working!`

### Check User Identity:
```bash
whoami                    # Should show: username (e.g., magnus.overli)
id                        # Should show 100+ groups from EntraID
groups                    # Should include: users, wheel, and many EntraID groups
```

**Expected:** Your username without the domain suffix, and numerous EntraID group memberships (typically 50-150+ groups depending on your organization).

### Check Logs for Enrollment:
```bash
# Look for domain join (replace "20 minutes ago" with appropriate time)
journalctl -u himmelblaud --since "20 minutes ago" | grep -i "joined domain"

# Check compliance state
journalctl -u himmelblaud-tasks --since "20 minutes ago" | grep -i "compliance_state"
```

**Expected output examples:**
- Domain join: `INFO │ │ ┝━ ｉ [info]: Joined domain your-domain.com with device id <uuid>`
- Compliance: `new_compliance_state: "Compliant"`

### Verify Home Directory:
```bash
echo $HOME
ls -la $HOME
```

**Expected:** Home directory should be `/home/username` and contain files copied from `/etc/skel`.

### Test Sudo Access:
```bash
sudo whoami  # Enter your EntraID password when prompted
```

**Expected:** After entering your password, should output `root`. You're in the wheel group so sudo access is properly configured.

### Success Indicators:

- All services running (`active (running)`)
- `aad-tool status` outputs `working!`
- `id` command shows 100+ groups from EntraID
- Logs show domain joined successfully
- Logs show `compliance_state: Compliant`
- Home directory exists and populated
- User is member of `users` and `wheel` groups
- Sudo access works with EntraID password

**Automation:** Verification commands are automatable

---

**Step 12 Complete!** Your device is now successfully:
- Authenticated with EntraID
- Enrolled in Intune MDM
- Compliant with policies
- Ready for use

---

## Troubleshooting

### Issue: MFA code shows but no Authenticator notification
- **Wait 30 seconds** - notification is delayed
- Check phone is online
- Manually open Authenticator and look for pending requests

### Issue: Authentication fails - "user unknown"
- Verify domain in `/etc/himmelblau/himmelblau.conf` matches your EntraID tenant
- Use FULL email: `username@exact-domain.com`
- Check: Is it your custom domain or onmicrosoft.com domain?

### Issue: Config key "domain" not recognized
- Change `domain =` to `domains =` (plural!) in config file

### Issue: "Failed to create cron file"
- Install and enable cronie: `sudo pacman -S cronie && sudo systemctl enable --now cronie`

### Issue: Intune not enrolling
- Ensure `apply_policy = true` in `/etc/himmelblau/himmelblau.conf`
- Restart services and login again

### Restore from PAM lockout:
- Boot to recovery or live USB
- Restore backup: `cp /etc/pam.d/system-auth.backup /etc/pam.d/system-auth`

---
