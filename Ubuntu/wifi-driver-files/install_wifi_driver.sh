#!/bin/bash
# WiFi Driver Installation Script for Ubuntu 24.04.4 LTS
# RTW8852C WiFi Card - Kernel 6.8.0-58-generic
# Run this script from the USB stick on your offline Ubuntu machine

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located (USB path)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}=========================================="
echo "WiFi Driver Installation Script"
echo "RTW8852C for Ubuntu 24.04.4"
echo -e "==========================================${NC}"
echo ""
echo "Script location: $SCRIPT_DIR"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}This script must be run as root (use sudo)${NC}"
    echo "Usage: sudo $0 [option]"
    exit 1
fi

# Function to check if WiFi is working
check_wifi() {
    echo -e "\n${BLUE}Checking WiFi status...${NC}"
    if ip link show | grep -q "wl"; then
        echo -e "${GREEN}✓ WiFi interface found!${NC}"
        ip link show | grep "wl"
        echo ""
        echo "To connect to WiFi, use: nmtui or nmcli"
        return 0
    else
        echo -e "${YELLOW}⚠ No WiFi interface detected yet${NC}"
        return 1
    fi
}

# Function to install firmware files (Method 1 - Quick)
install_firmware_files() {
    echo -e "\n${BLUE}[Method 1] Installing firmware files...${NC}"
    
    if [ ! -d "$SCRIPT_DIR/rtw89-firmware" ]; then
        echo -e "${RED}Error: rtw89-firmware directory not found!${NC}"
        return 1
    fi
    
    # Create firmware directory if it doesn't exist
    mkdir -p /lib/firmware/rtw89
    
    # Copy firmware files
    echo "Copying firmware files to /lib/firmware/rtw89/..."
    cp -v "$SCRIPT_DIR/rtw89-firmware/"*.bin /lib/firmware/rtw89/
    
    # Set permissions
    chmod 644 /lib/firmware/rtw89/rtw8852c*
    
    echo -e "${GREEN}✓ Firmware files installed${NC}"
    
    # Reload driver
    echo "Reloading driver..."
    modprobe -r rtw89_8852ce 2>/dev/null || true
    modprobe -r rtw89_8852cd 2>/dev/null || true
    sleep 1
    
    if modprobe rtw89_8852ce 2>/dev/null; then
        echo -e "${GREEN}✓ Driver loaded successfully (8852ce)${NC}"
    elif modprobe rtw89_8852cd 2>/dev/null; then
        echo -e "${GREEN}✓ Driver loaded successfully (8852cd)${NC}"
    else
        echo -e "${YELLOW}⚠ Driver load failed, checking dmesg...${NC}"
        dmesg | tail -20 | grep -i rtw89
    fi
    
    return 0
}

# Function to install linux-firmware package (Method 2)
install_firmware_package() {
    echo -e "\n${BLUE}[Method 2] Installing linux-firmware package...${NC}"
    
    FIRMWARE_DEB="$SCRIPT_DIR/linux-firmware_24.04_all.deb"
    
    if [ ! -f "$FIRMWARE_DEB" ]; then
        echo -e "${RED}Error: linux-firmware package not found!${NC}"
        return 1
    fi
    
    echo "Installing $FIRMWARE_DEB..."
    dpkg -i "$FIRMWARE_DEB" || apt-get install -f -y
    
    echo -e "${GREEN}✓ linux-firmware package installed${NC}"
    
    echo "Updating initramfs..."
    update-initramfs -u
    
    echo -e "${YELLOW}System reboot recommended. Reboot now? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        reboot
    fi
    
    return 0
}

# Function to install kernel headers and compile driver (Method 3)
compile_driver() {
    echo -e "\n${BLUE}[Method 3] Compiling driver from source...${NC}"
    
    # Install kernel headers
    echo "Installing kernel headers..."
    if [ -f "$SCRIPT_DIR/kernel-headers/linux-headers-6.8.0-58_all.deb" ]; then
        dpkg -i "$SCRIPT_DIR/kernel-headers/linux-headers-6.8.0-58_all.deb" || true
    fi
    
    if [ -f "$SCRIPT_DIR/kernel-headers/linux-headers-6.8.0-58-generic_amd64.deb" ]; then
        dpkg -i "$SCRIPT_DIR/kernel-headers/linux-headers-6.8.0-58-generic_amd64.deb" || true
    fi
    
    # Install build dependencies if available
    for deb in "$SCRIPT_DIR/kernel-headers/"*.deb; do
        [ -f "$deb" ] && dpkg -i "$deb" 2>/dev/null || true
    done
    
    # Check if build-essential is installed, if not try to install from debs
    if ! command -v make &> /dev/null || ! command -v gcc &> /dev/null; then
        echo -e "${YELLOW}⚠ build-essential not found. Install it when you have internet.${NC}"
        echo "You can try: apt install build-essential dkms"
        return 1
    fi
    
    # Extract and compile driver
    DRIVER_ZIP="$SCRIPT_DIR/driver-source/rtw89-lwfinger-master.zip"
    
    if [ ! -f "$DRIVER_ZIP" ]; then
        echo -e "${RED}Error: Driver source not found!${NC}"
        return 1
    fi
    
    WORK_DIR=$(mktemp -d)
    cd "$WORK_DIR"
    
    echo "Extracting driver source..."
    unzip -q "$DRIVER_ZIP"
    cd rtw89-master
    
    echo "Compiling driver..."
    make
    
    echo "Installing driver..."
    make install
    
    echo "Loading driver..."
    modprobe rtw89_8852ce || modprobe rtw89_8852cd
    
    cd /
    rm -rf "$WORK_DIR"
    
    echo -e "${GREEN}✓ Driver compiled and installed${NC}"
    
    return 0
}

# Function to show diagnostics
show_diagnostics() {
    echo -e "\n${BLUE}=== System Diagnostics ===${NC}"
    
    echo -e "\n${YELLOW}Kernel version:${NC}"
    uname -r
    
    echo -e "\n${YELLOW}Network interfaces:${NC}"
    ip link show
    
    echo -e "\n${YELLOW}PCI WiFi devices:${NC}"
    lspci | grep -i network || echo "No network devices found"
    
    echo -e "\n${YELLOW}USB WiFi devices:${NC}"
    lsusb | grep -i wireless || echo "No USB wireless devices found"
    
    echo -e "\n${YELLOW}RTW89 modules:${NC}"
    lsmod | grep rtw89 || echo "No rtw89 modules loaded"
    
    echo -e "\n${YELLOW}Module info (if available):${NC}"
    modinfo rtw89_8852ce 2>/dev/null || modinfo rtw89_8852cd 2>/dev/null || echo "Module not found"
    
    echo -e "\n${YELLOW}Recent kernel messages (dmesg):${NC}"
    dmesg | grep -i rtw89 | tail -20 || echo "No rtw89 messages found"
    
    echo -e "\n${YELLOW}Firmware directory:${NC}"
    ls -lh /lib/firmware/rtw89/ 2>/dev/null || echo "Directory not found"
}

# Main menu
show_menu() {
    echo ""
    echo -e "${GREEN}Installation Options:${NC}"
    echo "1) Quick fix - Install firmware files only (recommended first)"
    echo "2) Install full linux-firmware package (requires reboot)"
    echo "3) Compile driver from source (advanced)"
    echo "4) Show diagnostics"
    echo "5) Check if WiFi is working"
    echo "6) Exit"
    echo ""
}

# Main logic
if [ "$1" == "auto" ] || [ "$1" == "1" ]; then
    # Auto mode - try quick fix
    install_firmware_files
    check_wifi
    exit 0
fi

# Interactive mode
while true; do
    show_menu
    read -p "Select option [1-6]: " choice
    
    case $choice in
        1)
            install_firmware_files
            check_wifi
            ;;
        2)
            install_firmware_package
            ;;
        3)
            compile_driver
            check_wifi
            ;;
        4)
            show_diagnostics
            ;;
        5)
            check_wifi
            ;;
        6)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done
