#!/usr/bin/env bash
# 01-vim-essentials.sh
# Essential editors + core utils FIRST (for editing future scripts)

set -euo pipefail

echo "==> Installing apps: brave, etc."

sudo snap install brave
sudo apt install docker.io
sudo usermod -aG docker $USER

echo "==> Installing OrcaSlicer"
git clone https://github.com/OrcaSlicer/OrcaSlicer && cd OrcaSlicer && ./scripts/DockerBuild.sh && ./scripts/DockerRun.sh
echo "  [OK] apps installed"
