#!/usr/bin/env bash
# 01-vim-essentials.sh
# Essential editors + core utils FIRST (for editing future scripts)

set -euo pipefail

echo "==> Installing apps: brave, etc."

sudo snap install brave
sudo apt install docker.io
sudo usermod -aG docker $USER
echo "  [OK] apps installed"
