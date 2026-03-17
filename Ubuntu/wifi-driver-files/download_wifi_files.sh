#!/bin/bash
# Script to download WiFi driver files for Ubuntu 24.04.4 LTS (kernel 6.8.0-58-generic)
# For RTW8852C WiFi card

set -e  # Exit on error

BASE_DIR="$HOME/wifi-driver-files"
cd "$BASE_DIR"

echo "=========================================="
echo "Downloading WiFi Driver Files"
echo "=========================================="

# 1. Download RTW89 firmware files (CRITICAL)
echo ""
echo "[1/4] Downloading RTW89 firmware files..."
cd rtw89-firmware

curl -L -o rtw8852c_fw.bin \
  "https://gitlab.com/kernel-firmware/linux-firmware/-/raw/main/rtw89/rtw8852c_fw.bin"
echo "✓ Downloaded rtw8852c_fw.bin"

curl -L -o rtw8852c_fw-2.bin \
  "https://gitlab.com/kernel-firmware/linux-firmware/-/raw/main/rtw89/rtw8852c_fw-2.bin"
echo "✓ Downloaded rtw8852c_fw-2.bin"

curl -L -o rtw8852c_fw-3.bin \
  "https://gitlab.com/kernel-firmware/linux-firmware/-/raw/main/rtw89/rtw8852c_fw-3.bin"
echo "✓ Downloaded rtw8852c_fw-3.bin"

# 2. Download linux-firmware package
echo ""
echo "[2/4] Downloading linux-firmware package..."
cd "$BASE_DIR"

# Get the latest linux-firmware for noble (24.04)
curl -L -o linux-firmware_24.04_all.deb \
  "http://archive.ubuntu.com/ubuntu/pool/main/l/linux-firmware/linux-firmware_20240909-0ubuntu0.24.04.1_all.deb"
echo "✓ Downloaded linux-firmware package"

# 3. Download kernel headers and dependencies
echo ""
echo "[3/4] Downloading kernel headers and dependencies..."
cd kernel-headers

# Kernel headers for 6.8.0-58-generic
curl -L -o linux-headers-6.8.0-58-generic_amd64.deb \
  "http://archive.ubuntu.com/ubuntu/pool/main/l/linux/linux-headers-6.8.0-58-generic_6.8.0-58.58_amd64.deb" || \
  echo "⚠ Failed to download linux-headers-6.8.0-58-generic, trying alternative source..." && \
  curl -L -o linux-headers-6.8.0-58-generic_amd64.deb \
  "http://security.ubuntu.com/ubuntu/pool/main/l/linux/linux-headers-6.8.0-58-generic_6.8.0-58.58_amd64.deb"
echo "✓ Downloaded linux-headers-6.8.0-58-generic"

# Common headers
curl -L -o linux-headers-6.8.0-58_all.deb \
  "http://archive.ubuntu.com/ubuntu/pool/main/l/linux/linux-headers-6.8.0-58_6.8.0-58.58_all.deb" || \
  curl -L -o linux-headers-6.8.0-58_all.deb \
  "http://security.ubuntu.com/ubuntu/pool/main/l/linux/linux-headers-6.8.0-58_6.8.0-58.58_all.deb"
echo "✓ Downloaded linux-headers-6.8.0-58 (common)"

# Build essentials (libc6-dev, gcc, make) - if you need to compile drivers
echo "Downloading build dependencies (gcc, make, libc6-dev)..."
curl -L -o gcc-13_amd64.deb \
  "http://archive.ubuntu.com/ubuntu/pool/main/g/gcc-13/gcc-13_13.2.0-23ubuntu4_amd64.deb" 2>/dev/null || \
  echo "⚠ gcc download skipped (available via apt on target machine)"

curl -L -o make_amd64.deb \
  "http://archive.ubuntu.com/ubuntu/pool/main/m/make-dfsg/make_4.3-4.1build1_amd64.deb" 2>/dev/null || \
  echo "⚠ make download skipped"

curl -L -o libc6-dev_amd64.deb \
  "http://archive.ubuntu.com/ubuntu/pool/main/g/glibc/libc6-dev_2.39-0ubuntu8_amd64.deb" 2>/dev/null || \
  echo "⚠ libc6-dev download skipped"

# 4. Download driver source code (backup option)
echo ""
echo "[4/4] Downloading driver source code..."
cd "$BASE_DIR/driver-source"

curl -L -o rtw89-lwfinger-master.zip \
  "https://github.com/lwfinger/rtw89/archive/refs/heads/master.zip"
echo "✓ Downloaded rtw89 driver source (lwfinger)"

curl -L -o rtw89-morrownr-master.zip \
  "https://github.com/morrownr/rtw89/archive/refs/heads/main.zip"
echo "✓ Downloaded rtw89 driver source (morrownr)"

# Create README with installation instructions
echo ""
echo "Creating installation instructions..."
cd "$BASE_DIR"

cat > INSTALLATION_INSTRUCTIONS.txt << 'EOF'
============================================================
WiFi Driver Installation Instructions for Ubuntu 24.04.4
RTW8852C WiFi Card - Kernel 6.8.0-58-generic
============================================================

STEP 1: Install Firmware Files (CRITICAL - Try this first)
-----------------------------------------------------------
cd /path/to/usb/rtw89-firmware
sudo cp *.bin /lib/firmware/rtw89/
sudo chmod 644 /lib/firmware/rtw89/rtw8852c*
sudo modprobe -r rtw89_8852ce  # Unload if loaded
sudo modprobe rtw89_8852ce      # Reload driver
dmesg | grep rtw89              # Check for errors

STEP 2: Install linux-firmware Package (if Step 1 fails)
---------------------------------------------------------
cd /path/to/usb
sudo dpkg -i linux-firmware_24.04_all.deb
sudo update-initramfs -u
sudo reboot

STEP 3: Check WiFi Status
--------------------------
ip link show                    # Look for wlan0 or wlp* interface
sudo dmesg | grep -i rtw89      # Check driver messages
lspci -k | grep -A 3 Network    # Verify driver loaded

STEP 4: If Still Not Working - Compile Driver from Source
----------------------------------------------------------
# Install kernel headers first
cd /path/to/usb/kernel-headers
sudo dpkg -i linux-headers-6.8.0-58_all.deb
sudo dpkg -i linux-headers-6.8.0-58-generic_amd64.deb

# Install build tools (if not already installed)
sudo apt install build-essential dkms

# Extract and compile driver
cd /path/to/usb/driver-source
unzip rtw89-lwfinger-master.zip
cd rtw89-master
make
sudo make install
sudo modprobe rtw89_8852ce

STEP 5: Troubleshooting
-----------------------
# Check if firmware is loaded
sudo dmesg | tail -50

# Check module info
modinfo rtw89_8852ce

# Force module parameters (if ce vs cd mismatch)
sudo modprobe rtw89_8852ce debug=1

# Check hardware
lspci -nn | grep -i network
lsusb  # If it's a USB WiFi adapter

# Blacklist conflicting drivers
echo "blacklist rtw88_8852ce" | sudo tee /etc/modprobe.d/blacklist-wifi.conf

NOTES:
------
- The rtw89 driver is built into kernel 6.8, so firmware files are usually enough
- Your error mentioned "rtw89_8852cd" vs "8852ce" - this is a variant issue
- Ensure you're using the correct variant (ce vs cd) for your exact hardware
- Run 'lspci -nn' to find exact PCI ID of your WiFi card

Good luck!
EOF

echo "✓ Installation instructions created"

# Summary
echo ""
echo "=========================================="
echo "Download Complete!"
echo "=========================================="
echo ""
echo "Files downloaded to: $BASE_DIR"
echo ""
echo "Directory structure:"
tree -L 2 "$BASE_DIR" 2>/dev/null || find "$BASE_DIR" -maxdepth 2 -type f
echo ""
echo "=========================================="
echo "NEXT STEPS:"
echo "=========================================="
echo "1. Copy the entire '$BASE_DIR' folder to your USB stick"
echo "2. On the Ubuntu machine (offline), follow the instructions in:"
echo "   INSTALLATION_INSTRUCTIONS.txt"
echo "3. Start with STEP 1 (firmware files) - this usually solves the issue"
echo ""
echo "Total size:"
du -sh "$BASE_DIR"
echo ""
