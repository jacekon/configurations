#!/usr/bin/env bash
# Configures git, enables natural scrolling, etc.

set -euo pipefail

#Git variables:
read -p "Enter your Git username: " GIT_USER
read -s -p "Enter your Git email: " GIT_EMAIL
echo
read -s -p "Enter your GitHub PAT (token): " GIT_TOKEN
echo

# Set user info
git config --global user.name "$GIT_USER"
git config --global user.email "$GIT_EMAIL"

# Set credential helper (stores permanently after first push)
git config --global credential.helper store

echo "Git configured!"
echo "Now do a 'git push' once - enter username ($GIT_USER) and token when prompted."
echo "Future pushes will be automatic."
echo "Verify: git config --list | grep user"

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
