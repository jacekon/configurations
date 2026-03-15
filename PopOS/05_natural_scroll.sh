#!/usr/bin/env bash
# natural-scrolling.sh
# Enables natural scrolling on Pop!_OS COSMIC (touchpad + mouse).
# Uses gsettings (COSMIC Settings backend) - persists across reboots.
# Equivalent to COSMIC Settings > Input Devices > Touchpad > Natural Scrolling

set -euo pipefail

echo "==> Enabling natural scrolling..."

# --- Touchpad natural scrolling ---
gsettings set org.gnome.desktop.peripherals.touchpad natural-scroll true
echo "  [OK] Touchpad natural scrolling enabled"

# --- Mouse wheel natural scrolling (separate setting) ---
gsettings set org.gnome.desktop.peripherals.mouse natural-scroll true
echo "  [OK] Mouse natural scrolling enabled"

# --- Verify ---
echo ""
echo "==> Verification:"
gsettings get org.gnome.desktop.peripherals.touchpad natural-scroll
gsettings get org.gnome.desktop.peripherals.mouse natural-scroll

echo ""
echo "==> Done! Scroll direction should now be natural (Mac-like)."
echo "    Log out/in or restart COSMIC Settings daemon if no immediate effect:"
echo "    killall cosmic-settings-daemon  # or reboot"
