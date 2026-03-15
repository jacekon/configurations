#!/usr/bin/env bash
# wifi-fix-rtw89-8852ce.sh
# Fixes Realtek RTL8852CE (rtw89) WiFi on Pop!_OS / Ubuntu-based distros.
# Problem: Card fails to exit firmware power-save mode ("busy swsi" / LPS errors).
# Solution: Disable power-save and PCI power management at the driver level.

set -euo pipefail

echo "==> Applying Realtek RTL8852CE WiFi fix..."

# --- 1. Kernel module options ---
# disable_ps_mode: prevents firmware from entering low-power state (fixes busy swsi)
# disable_aspm_l1 / disable_aspm_l1ss: disables PCI power management that makes card unresponsive
# disable_clkreq: disables PCI clock gating, another source of instability
sudo tee /etc/modprobe.d/rtw89.conf > /dev/null << 'EOF'
options rtw89_core disable_ps_mode=Y
options rtw89_pci disable_aspm_l1=Y disable_aspm_l1ss=Y disable_clkreq=Y
EOF
echo "  [OK] /etc/modprobe.d/rtw89.conf written"

# --- 2. NetworkManager power save ---
# wifi.powersave = 2 means disabled (3 = enabled, 1 = default)
sudo mkdir -p /etc/NetworkManager/conf.d
sudo tee /etc/NetworkManager/conf.d/wifi-powersave-off.conf > /dev/null << 'EOF'
[connection]
wifi.powersave = 2
EOF
echo "  [OK] /etc/NetworkManager/conf.d/wifi-powersave-off.conf written"

# --- 3. Rebuild initramfs so settings persist across reboots ---
echo "==> Rebuilding initramfs (this may take a moment)..."
sudo update-initramfs -u
echo "  [OK] initramfs updated"

# --- 4. Reload driver to apply immediately without rebooting ---
echo "==> Reloading rtw89_8852ce driver..."
sudo modprobe -rv rtw89_8852ce 2>/dev/null || true
sudo modprobe -v rtw89_8852ce
echo "  [OK] Driver reloaded"

# --- 5. Restart NetworkManager ---
sudo systemctl restart NetworkManager
echo "  [OK] NetworkManager restarted"

echo ""
echo "==> Done! Verify with: sudo dmesg | grep -i rtw89"
echo "    You should see no 'busy swsi' or 'failed to leave lps' errors."
