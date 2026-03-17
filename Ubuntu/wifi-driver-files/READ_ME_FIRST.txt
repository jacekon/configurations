===============================================
WiFi Driver Installation for Ubuntu 24.04.4
RTW8852C WiFi Card
===============================================

QUICK START (On your offline Ubuntu machine):
----------------------------------------------

1. Plug in the USB stick
2. Open terminal
3. Navigate to USB: cd /media/YOUR_USERNAME/USB_NAME/wifi-driver-files
4. Run the script: sudo ./install_wifi_driver.sh

The script will show you a menu with installation options.


USAGE OPTIONS:
--------------

Interactive Mode (recommended):
    sudo ./install_wifi_driver.sh
    
    Then select:
    Option 1 - Quick firmware install (try this first!)
    Option 4 - Show diagnostics
    Option 5 - Check if WiFi is working

Auto Mode (runs quick fix automatically):
    sudo ./install_wifi_driver.sh auto


WHAT THE SCRIPT DOES:
---------------------

Option 1 - Quick Fix (RECOMMENDED - Start here!)
    • Copies firmware files to /lib/firmware/rtw89/
    • Reloads the WiFi driver
    • Usually fixes the problem in 10 seconds
    • No reboot needed

Option 2 - Full Firmware Package
    • Installs complete linux-firmware package
    • More comprehensive
    • Requires system reboot

Option 3 - Compile from Source
    • Advanced option if firmware doesn't work
    • Requires kernel headers and build tools
    • Takes a few minutes

Option 4 - Diagnostics
    • Shows system information
    • Hardware detection
    • Driver status
    • Kernel messages

Option 5 - Check WiFi
    • Tests if WiFi interface is detected
    • Shows interface name (wlan0, wlp2s0, etc.)


AFTER SUCCESSFUL INSTALLATION:
-------------------------------

Check WiFi interfaces:
    ip link show
    
Connect to WiFi (graphical):
    nmtui
    
Connect to WiFi (command line):
    nmcli device wifi list
    nmcli device wifi connect "WIFI_NAME" password "PASSWORD"


TROUBLESHOOTING:
----------------

If WiFi still doesn't work after Option 1:
    1. Run diagnostics (Option 4)
    2. Look for error messages in output
    3. Try Option 2 (requires reboot)
    4. Check if you have the correct variant:
       lspci -nn | grep -i network
       (Look for 8852ce vs 8852cd vs 8852cs)

Common issues:
    • Wrong variant (ce vs cd) - check with lspci
    • Secure Boot enabled - may need to disable
    • Missing kernel headers - needed for Option 3


FILE STRUCTURE ON USB:
----------------------
wifi-driver-files/
├── install_wifi_driver.sh          ← Run this script
├── READ_ME_FIRST.txt               ← This file
├── INSTALLATION_INSTRUCTIONS.txt   ← Detailed manual instructions
├── rtw89-firmware/                 ← Firmware binary files
│   ├── rtw8852c_fw.bin
│   ├── rtw8852c_fw-2.bin
│   └── rtw8852c_fw-3.bin
├── kernel-headers/                 ← For compiling driver
└── driver-source/                  ← Driver source code


NEED HELP?
----------
The script provides clear feedback at each step.
If something fails, it will show error messages.

For manual installation, see: INSTALLATION_INSTRUCTIONS.txt

Good luck! 🚀
