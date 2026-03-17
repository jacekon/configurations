#!/usr/bin/env bash
# 01-vim-essentials.sh
# Essential editors + core utils FIRST (for editing future scripts)

set -euo pipefail

echo "==> Installing essential vim, git, curl, etc."

sudo apt update
sudo apt install -y \
    vim \
    curl \
    wget \
    git \
    htop \
    tree \
    unzip \
    xclip

echo "  [OK] Vim + essentials installed"
echo "==> You can now edit scripts with vim!"
