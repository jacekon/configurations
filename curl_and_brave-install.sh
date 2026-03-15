#!/usr/bin/env bash
# brave-install.sh
# Installs Brave Browser from official repo on Pop!_OS / Ubuntu.
# Commands sourced from https://brave.com/linux/#installation

set -euo pipefail

echo "==> Installing Brave Browser..."

# --- 1. Install curl if missing ---
if ! command -v curl >/dev/null 2>&1; then
    sudo apt update
    sudo apt install -y curl
    echo "  [OK] curl installed"
fi

# --- 2. Download and install GPG key ---
KEYRING_URL="https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg"
sudo curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg "$KEYRING_URL"
echo "  [OK] GPG keyring installed"

# --- 3. Add Brave repo ---
REPO_URL="https://brave-browser-apt-release.s3.brave.com/brave-browser.sources"
sudo curl -fsSLo /etc/apt/sources.list.d/brave-browser-release.sources "$REPO_URL"
echo "  [OK] Brave repo added"

# --- 4. Update package lists and install ---
sudo apt update
sudo apt install -y brave-browser
echo "  [OK] Brave Browser installed"

echo ""
echo "==> Done! You can now run: brave-browser"
echo "==> Files created:"
echo "    /usr/share/keyrings/brave-browser-archive-keyring.gpg"
echo "    /etc/apt/sources.list.d/brave-browser-release.sources"
