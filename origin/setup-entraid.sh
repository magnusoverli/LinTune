#!/bin/bash
#
# EntraID & Intune Setup for CachyOS/Arch Linux
#

set -o pipefail

HIMMELBLAU_REPO="https://github.com/himmelblau-idm/himmelblau"
BUILD_DIR="/tmp/himmelblau"
LOG_FILE="/var/log/entraid-setup.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
BOLD='\033[1m'
NC='\033[0m'

# Symbols
OK="✓"
FAIL="✗"
PENDING="○"

# ─────────────────────────────────────────────────────────────────────────────

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}Error: Run with sudo${NC}"
        exit 1
    fi
}

status_check() {
    echo ""
    echo -e "${BOLD}Current Status:${NC}"
    echo ""
    
    # Display Manager
    local gdm_enabled=false
    local other_dm=""
    
    if systemctl is-enabled gdm &>/dev/null; then
        gdm_enabled=true
    fi
    
    # Check if other DMs are enabled (use is-enabled, not list-units)
    for dm in sddm lightdm lxdm xdm; do
        if systemctl is-enabled ${dm} &>/dev/null; then
            other_dm="$dm"
            break
        fi
    done
    
    if $gdm_enabled; then
        echo -e "  ${GREEN}${OK}${NC} Display Manager: ${GREEN}GDM enabled${NC} (ready for EntraID)"
    elif [ -n "$other_dm" ]; then
        if pacman -Qi gdm &>/dev/null; then
            echo -e "  ${GREEN}${OK}${NC} Display Manager: ${GREEN}${other_dm^^} enabled${NC} (GDM available, ready for setup)"
        else
            echo -e "  ${YELLOW}!${NC} Display Manager: ${YELLOW}${other_dm^^} enabled${NC} (GDM not installed, use option 0)"
        fi
    elif pacman -Qi gdm &>/dev/null; then
        echo -e "  ${YELLOW}!${NC} Display Manager: ${YELLOW}No DM enabled${NC} (GDM installed but disabled)"
    else
        echo -e "  ${YELLOW}!${NC} Display Manager: ${YELLOW}No DM detected${NC} (GDM required)"
    fi
    
    # Dependencies
    if pacman -Qi rust &>/dev/null && pacman -Qi cargo &>/dev/null; then
        # Check if Himmelblau is actually installed to determine if this is a fresh state
        if [ ! -f "/usr/sbin/himmelblaud" ]; then
            echo -e "  ${CYAN}○${NC} Build dependencies available"
        else
            echo -e "  ${GREEN}${OK}${NC} Dependencies installed"
        fi
    else
        echo -e "  ${GRAY}${PENDING}${NC} Dependencies not installed"
    fi
    
    # Binaries
    if [ -f "/usr/sbin/himmelblaud" ]; then
        echo -e "  ${GREEN}${OK}${NC} Himmelblau installed"
    else
        echo -e "  ${GRAY}${PENDING}${NC} Himmelblau not installed"
    fi
    
    # Services
    if [ -f "/etc/systemd/system/himmelblaud.service" ]; then
        echo -e "  ${GREEN}${OK}${NC} Services configured"
    else
        echo -e "  ${GRAY}${PENDING}${NC} Services not configured"
    fi
    
    # NSS
    if grep -q "himmelblau" /etc/nsswitch.conf 2>/dev/null; then
        echo -e "  ${GREEN}${OK}${NC} NSS configured"
    else
        echo -e "  ${GRAY}${PENDING}${NC} NSS not configured"
    fi
    
    # PAM
    if grep -q "pam_himmelblau" /etc/pam.d/system-auth 2>/dev/null; then
        echo -e "  ${GREEN}${OK}${NC} PAM configured"
    else
        echo -e "  ${GRAY}${PENDING}${NC} PAM not configured"
    fi
    
    # Config
    if [ -f "/etc/himmelblau/himmelblau.conf" ]; then
        local domain=$(grep "^domains" /etc/himmelblau/himmelblau.conf 2>/dev/null | cut -d'=' -f2 | tr -d ' ')
        echo -e "  ${GREEN}${OK}${NC} Config: ${CYAN}${domain}${NC}"
    else
        echo -e "  ${GRAY}${PENDING}${NC} Config not set"
    fi
    
    # Cronie
    if systemctl is-active cronie &>/dev/null; then
        echo -e "  ${GREEN}${OK}${NC} Cronie running"
    else
        echo -e "  ${GRAY}${PENDING}${NC} Cronie not running"
    fi
    
    # Daemon
    if systemctl is-active himmelblaud &>/dev/null; then
        echo -e "  ${GREEN}${OK}${NC} Himmelblaud running"
    else
        echo -e "  ${GRAY}${PENDING}${NC} Himmelblaud not running"
    fi
    
    # Check system state
    local has_backups=false
    local has_himmelblau=false
    
    if [ -f /etc/pam.d/system-auth.backup ] || [ -f /etc/nsswitch.conf.backup ]; then
        has_backups=true
    fi
    
    if [ -f "/usr/sbin/himmelblaud" ] || [ -f "/etc/systemd/system/himmelblaud.service" ]; then
        has_himmelblau=true
    fi
    
    # Show state indicator
    echo ""
    if $has_himmelblau; then
        if $has_backups; then
            echo -e "  ${CYAN}State:${NC} EntraID configured"
        else
            echo -e "  ${YELLOW}State:${NC} Partial/incomplete installation"
        fi
    else
        if $has_backups; then
            echo -e "  ${YELLOW}State:${NC} Leftovers from previous install (backups exist)"
        else
            echo -e "  ${CYAN}State:${NC} Clean system"
        fi
    fi
    
    echo ""
}

show_menu() {
    echo -e "${BOLD}Actions:${NC}"
    echo ""
    echo -e "  ${CYAN}0${NC}  Install & switch to GDM"
    echo -e "  ${CYAN}1${NC}  Install dependencies"
    echo -e "  ${CYAN}2${NC}  Build & install Himmelblau"
    echo -e "  ${CYAN}3${NC}  Configure system"
    echo -e "  ${CYAN}4${NC}  Set EntraID domain"
    echo -e "  ${CYAN}5${NC}  Setup cronie"
    echo -e "  ${CYAN}6${NC}  Start services"
    echo -e "  ${CYAN}a${NC}  Run ALL steps"
    echo -e "  ${CYAN}r${NC}  ${RED}Reset/Uninstall${NC}"
    echo -e "  ${CYAN}i${NC}  Login instructions"
    echo -e "  ${CYAN}q${NC}  Quit"
    echo ""
}

do_install_gdm() {
    echo -e "\n${BOLD}Installing and configuring GDM...${NC}\n"
    
    # Check current display manager
    local current_dm=$(systemctl list-units --type=service --state=running | grep -oE '(sddm|lightdm|lxdm|xdm)\.service' | head -1 | sed 's/\.service//')
    
    if [ -n "$current_dm" ]; then
        echo -e "  ${YELLOW}!${NC} Current display manager: ${current_dm}"
        echo -e "  ${CYAN}ℹ${NC} Will disable ${current_dm} and switch to GDM"
        echo ""
        echo -n "  Continue? [Y/n]: "
        read confirm
        if [[ "$confirm" =~ ^[Nn] ]]; then
            echo -e "  ${YELLOW}Cancelled${NC}\n"
            return
        fi
        
        # Save previous display manager for reset (create dir first)
        mkdir -p /etc/himmelblau
        echo "$current_dm" > /etc/himmelblau/.previous_dm
        echo -e "  ${CYAN}ℹ${NC} Saved previous DM: ${current_dm}"
    fi
    
    # Install GDM (without full GNOME)
    echo -e "\n  Installing GDM package..."
    pacman -S --noconfirm --needed gdm
    
    # Disable old display manager if present
    if [ -n "$current_dm" ]; then
        echo -e "  ${CYAN}ℹ${NC} Disabling ${current_dm}..."
        systemctl disable ${current_dm}.service 2>/dev/null
    fi
    
    # Enable GDM
    echo -e "  ${CYAN}ℹ${NC} Enabling GDM..."
    systemctl enable gdm.service
    
    echo -e "\n  ${GREEN}${OK}${NC} GDM installed and enabled"
    echo -e "  ${YELLOW}!${NC} Reboot required for GDM to take effect"
    echo ""
}

do_install_deps() {
    echo -e "\n${BOLD}Installing dependencies...${NC}\n"
    pacman -Sy --noconfirm
    pacman -S --noconfirm --needed rust cargo pkg-config openssl sqlite dbus tpm2-tss git base-devel
    echo -e "\n${GREEN}${OK} Done${NC}\n"
}

do_build_install() {
    echo -e "\n${BOLD}Building Himmelblau (takes ~2 min)...${NC}\n"
    
    rm -rf ${BUILD_DIR}
    git clone ${HIMMELBLAU_REPO} ${BUILD_DIR}
    cd ${BUILD_DIR}
    
    HIMMELBLAU_ALLOW_MISSING_SELINUX=1 cargo build --release
    
    echo -e "\n${BOLD}Installing binaries...${NC}\n"
    install -m 755 target/release/himmelblaud /usr/sbin/
    install -m 755 target/release/himmelblaud_tasks /usr/sbin/
    install -m 755 target/release/aad-tool /usr/bin/
    install -m 755 target/release/broker /usr/sbin/
    install -m 755 target/release/linux-entra-sso /usr/bin/
    install -m 755 target/release/libpam_himmelblau.so /usr/lib/security/pam_himmelblau.so
    install -m 755 target/release/libnss_himmelblau.so /usr/lib/libnss_himmelblau.so.2
    
    echo -e "\n${GREEN}${OK} Done${NC}\n"
}

do_configure() {
    echo -e "\n${BOLD}Configuring system...${NC}\n"
    
    # Services
    python3 ${BUILD_DIR}/scripts/gen_servicefiles.py --out-dir /tmp/himmelblau-services
    sed -i 's/^LoadCredentialEncrypted=/#LoadCredentialEncrypted=/' /tmp/himmelblau-services/himmelblaud.service
    sed -i 's/^Environment=HIMMELBLAU_HSM_PIN_PATH=/#Environment=HIMMELBLAU_HSM_PIN_PATH=/' /tmp/himmelblau-services/himmelblaud.service
    
    mkdir -p /etc/himmelblau
    cp /tmp/himmelblau-services/himmelblaud.service /etc/systemd/system/
    cp /tmp/himmelblau-services/himmelblaud-tasks.service /etc/systemd/system/
    install -m 644 ${BUILD_DIR}/platform/debian/com.microsoft.identity.broker1.service /usr/share/dbus-1/services/
    mkdir -p /var/cache/nss-himmelblau /var/cache/himmelblau-policies /etc/krb5.conf.d
    systemctl daemon-reload
    echo -e "  ${GREEN}${OK}${NC} Services configured"
    
    # NSS
    if ! grep -q "himmelblau" /etc/nsswitch.conf; then
        cp /etc/nsswitch.conf /etc/nsswitch.conf.backup
        sed -i 's/^passwd:.*/passwd: files systemd himmelblau/' /etc/nsswitch.conf
        sed -i 's/^group:.*/group: files [SUCCESS=merge] systemd himmelblau/' /etc/nsswitch.conf
        echo -e "  ${GREEN}${OK}${NC} NSS configured"
    fi
    
    # PAM
    if ! grep -q "pam_himmelblau" /etc/pam.d/system-auth; then
        cp /etc/pam.d/system-auth /etc/pam.d/system-auth.backup
        cat > /etc/pam.d/system-auth << 'PAMEOF'
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
PAMEOF
        echo -e "  ${GREEN}${OK}${NC} PAM configured"
    fi
    
    echo -e "\n${GREEN}${OK} Done${NC}\n"
}

do_set_domain() {
    echo -e "\n${BOLD}EntraID Domain Configuration${NC}\n"
    
    echo -n "  Enter domain (e.g. company.com): "
    read domain
    
    if [ -z "$domain" ]; then
        echo -e "  ${YELLOW}Cancelled${NC}\n"
        return
    fi
    
    echo -n "  Grant sudo to EntraID users? [Y/n]: "
    read sudo_choice
    
    local local_groups="users"
    [[ ! "$sudo_choice" =~ ^[Nn] ]] && local_groups="users,wheel"
    
    mkdir -p /etc/himmelblau
    cat > /etc/himmelblau/himmelblau.conf << CONFEOF
[global]
domains = ${domain}
local_groups = ${local_groups}
home_attr = CN
home_alias = CN
use_etc_skel = true
enable_hello = false
debug = true
apply_policy = true
CONFEOF
    
    echo -e "\n  ${GREEN}${OK}${NC} Saved: ${CYAN}${domain}${NC}\n"
}

do_setup_cronie() {
    echo -e "\n${BOLD}Setting up cronie...${NC}\n"
    pacman -S --noconfirm --needed cronie
    systemctl enable --now cronie.service
    echo -e "\n${GREEN}${OK} Done${NC}\n"
}

do_start_services() {
    echo -e "\n${BOLD}Starting services...${NC}\n"
    systemctl enable himmelblaud himmelblaud-tasks
    systemctl restart himmelblaud
    sleep 2
    
    if systemctl is-active --quiet himmelblaud; then
        echo -e "  ${GREEN}${OK}${NC} himmelblaud running"
    else
        echo -e "  ${RED}${FAIL}${NC} himmelblaud failed"
        echo -e "  ${RED}!${NC} Check logs: journalctl -u himmelblaud -n 50"
        return
    fi
    
    if aad-tool status 2>/dev/null | grep -q "working"; then
        echo -e "  ${GREEN}${OK}${NC} aad-tool: working"
    fi
    
    echo ""
    echo -e "${CYAN}Ready for EntraID login!${NC}"
    echo ""
}

do_all() {
    # Check if GDM is enabled first
    if ! systemctl is-enabled gdm &>/dev/null; then
        echo -e "\n${YELLOW}!${NC} GDM is not enabled. It's required for EntraID authentication.\n"
        echo -n "  Install and enable GDM now? [Y/n]: "
        read confirm
        if [[ ! "$confirm" =~ ^[Nn] ]]; then
            do_install_gdm
            echo -e "${YELLOW}!${NC} Please reboot and run this script again to continue setup.\n"
            read -p "  Press Enter..."
            return
        fi
    fi
    
    do_install_deps
    do_build_install
    do_configure
    do_set_domain
    do_setup_cronie
    do_start_services
    
    echo ""
    echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}  Setup Complete!${NC}"
    echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}${BOLD}Next Steps:${NC}"
    echo ""
    echo -e "  ${BOLD}1.${NC} Log out of your current session"
    echo -e "  ${BOLD}2.${NC} At the GDM login screen:"
    echo -e "     • Click ${CYAN}'Not listed?'${NC}"
    echo -e "     • Enter your full email: ${CYAN}username@tv2.no${NC}"
    echo -e "     • Enter your ${CYAN}EntraID password${NC}"
    echo -e "     • Wait for ${CYAN}MFA notification${NC} (10-30 seconds)"
    echo -e "     • Approve on your phone"
    echo ""
    echo -e "  ${YELLOW}Note:${NC} First attempt may fail - just try again if needed"
    echo ""
    echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════${NC}"
    echo ""
}

do_reset() {
    echo -e "\n${BOLD}${YELLOW}════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${YELLOW}  Reset EntraID Setup${NC}"
    echo -e "${BOLD}${YELLOW}════════════════════════════════════════════${NC}"
    echo ""
    echo "This will remove all EntraID/Himmelblau configuration"
    echo "and restore your system to the state before setup."
    echo ""
    echo -n "Continue? [y/N]: "
    read confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Cancelled${NC}\n"
        return
    fi
    
    echo ""
    echo -n "Remove build dependencies (rust, cargo, etc.)? [y/N]: "
    read remove_deps
    
    echo ""
    echo -e "${BOLD}Stopping services...${NC}"
    systemctl stop himmelblaud himmelblaud-tasks 2>/dev/null || true
    systemctl disable himmelblaud himmelblaud-tasks 2>/dev/null || true
    echo -e "  ${GREEN}${OK}${NC} Services stopped"
    
    echo ""
    echo -e "${BOLD}Removing binaries...${NC}"
    rm -f /usr/sbin/himmelblaud
    rm -f /usr/sbin/himmelblaud_tasks
    rm -f /usr/bin/aad-tool
    rm -f /usr/sbin/broker
    rm -f /usr/bin/linux-entra-sso
    rm -f /usr/lib/security/pam_himmelblau.so
    rm -f /usr/lib/security/libpam_himmelblau.so
    rm -f /usr/lib/libnss_himmelblau.so.2
    echo -e "  ${GREEN}${OK}${NC} Binaries removed"
    
    echo ""
    echo -e "${BOLD}Removing systemd services...${NC}"
    rm -f /etc/systemd/system/himmelblaud.service
    rm -f /etc/systemd/system/himmelblaud-tasks.service
    rm -f /usr/share/dbus-1/services/com.microsoft.identity.broker1.service
    systemctl daemon-reload
    echo -e "  ${GREEN}${OK}${NC} Services removed"
    
    echo ""
    echo -e "${BOLD}Restoring PAM configuration...${NC}"
    if [ -f /etc/pam.d/system-auth.backup ]; then
        cp /etc/pam.d/system-auth.backup /etc/pam.d/system-auth
        echo -e "  ${GREEN}${OK}${NC} PAM restored from backup"
    else
        echo -e "  ${YELLOW}!${NC} No PAM backup found"
    fi
    
    echo ""
    echo -e "${BOLD}Restoring NSS configuration...${NC}"
    if [ -f /etc/nsswitch.conf.backup ]; then
        cp /etc/nsswitch.conf.backup /etc/nsswitch.conf
        echo -e "  ${GREEN}${OK}${NC} NSS restored from backup"
    else
        echo -e "  ${YELLOW}!${NC} No NSS backup found"
    fi
    
    echo ""
    echo -e "${BOLD}Restoring display manager...${NC}"
    local previous_dm=""
    if [ -f /etc/himmelblau/.previous_dm ]; then
        previous_dm=$(cat /etc/himmelblau/.previous_dm)
    elif [ -f /tmp/.himmelblau_previous_dm ]; then
        previous_dm=$(cat /tmp/.himmelblau_previous_dm)
    fi
    
    if [ -n "$previous_dm" ]; then
        echo -e "  ${CYAN}ℹ${NC} Found previous display manager: ${previous_dm}"
        echo -n "  Restore ${previous_dm}? [Y/n]: "
        read restore_dm
        if [[ ! "$restore_dm" =~ ^[Nn]$ ]]; then
            systemctl disable gdm.service 2>/dev/null || true
            systemctl enable ${previous_dm}.service 2>/dev/null
            echo -e "  ${GREEN}${OK}${NC} Display manager restored to ${previous_dm}"
            echo -e "  ${YELLOW}!${NC} Reboot required for display manager change"
        fi
        rm -f /etc/himmelblau/.previous_dm /tmp/.himmelblau_previous_dm
    else
        echo -e "  ${YELLOW}!${NC} No previous display manager recorded"
        echo -e "  ${CYAN}ℹ${NC} GDM will remain as display manager"
    fi
    
    echo ""
    echo -e "${BOLD}Removing configuration and cache...${NC}"
    rm -rf /etc/himmelblau
    rm -rf /var/cache/nss-himmelblau
    rm -rf /var/cache/himmelblau-policies
    echo -e "  ${GREEN}${OK}${NC} Configuration removed"
    
    echo ""
    echo -e "${BOLD}Removing build directory...${NC}"
    rm -rf /tmp/himmelblau
    rm -rf /tmp/himmelblau-services
    echo -e "  ${GREEN}${OK}${NC} Build files removed"
    
    echo ""
    echo -e "${BOLD}Cleaning up backup files...${NC}"
    rm -f /etc/pam.d/system-auth.backup
    rm -f /etc/nsswitch.conf.backup
    echo -e "  ${GREEN}${OK}${NC} Backup files removed"
    
    if [[ "$remove_deps" =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${BOLD}Removing build dependencies...${NC}"
        echo -e "  ${CYAN}ℹ${NC} This may take a moment..."
        pacman -R --noconfirm rust cargo pkg-config tpm2-tss 2>/dev/null || true
        echo -e "  ${GREEN}${OK}${NC} Build dependencies removed"
        echo -e "  ${YELLOW}!${NC} Kept: openssl, sqlite, dbus, git, base-devel (commonly used)"
    fi
    
    echo ""
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}  Reset Complete!${NC}"
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════${NC}"
    echo ""
    echo "System restored to pre-setup state."
    echo ""
    if [[ ! "$remove_deps" =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}Note:${NC} Build dependencies (rust, cargo) were kept."
        echo -e "      Remove manually if needed: ${CYAN}sudo pacman -R rust cargo${NC}"
    fi
    if [ -n "$previous_dm" ] && [[ ! "$restore_dm" =~ ^[Nn]$ ]]; then
        echo -e "${CYAN}Note:${NC} Reboot to switch back to ${previous_dm}"
    fi
    echo ""
}

show_instructions() {
    echo -e "\n${BOLD}Login Instructions:${NC}\n"
    echo "  1. Log out of your current session"
    echo "  2. At login screen, click 'Not listed?'"
    echo "  3. Enter your full email (user@domain.com)"
    echo "  4. Enter your password"
    echo "  5. Enter the MFA code shown into Authenticator"
    echo ""
    echo -e "  ${YELLOW}Note: First attempt may skip password - just retry${NC}"
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────

main() {
    check_root
    
    while true; do
        clear
        echo ""
        echo -e "${CYAN}${BOLD}  EntraID & Intune Setup${NC}"
        echo -e "  ${GRAY}CachyOS/Arch Linux${NC}"
        
        status_check
        show_menu
        
        echo -n "  Select: "
        read -n1 choice
        echo ""
        
        case "$choice" in
            0) do_install_gdm; read -p "  Press Enter..." ;;
            1) do_install_deps; read -p "  Press Enter..." ;;
            2) do_build_install; read -p "  Press Enter..." ;;
            3) do_configure; read -p "  Press Enter..." ;;
            4) do_set_domain; read -p "  Press Enter..." ;;
            5) do_setup_cronie; read -p "  Press Enter..." ;;
            6) do_start_services; read -p "  Press Enter..." ;;
            a|A) do_all; read -p "  Press Enter..." ;;
            r|R) do_reset; read -p "  Press Enter..." ;;
            i|I) show_instructions; read -p "  Press Enter..." ;;
            q|Q) clear; exit 0 ;;
        esac
    done
}

main
