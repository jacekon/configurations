#!/usr/bin/env bash
# wifi-connect-interactive.sh
# Interactive WiFi connector for Pop!_OS.
# Lists available networks with numbers, pick one, enter password.

set -euo pipefail

echo "==> Scanning for WiFi networks..."

# Get list of available networks (SSID + signal strength)
mapfile -t networks < <(nmcli -t -f SSID,SIGNAL device wifi list --rescan yes | grep -v '^IN-USE' | tail -n +2)

if [ ${#networks[@]} -eq 0 ]; then
    echo "No networks found. Check WiFi adapter."
    exit 1
fi

echo ""
echo "Available networks:"
for i in "${!networks[@]}"; do
    printf "  %d. %s\n" $((i+1)) "${networks[i]}"
done
echo ""

# Let user pick by number
read -p "Enter network number (1-${#networks[@]}): " num
num=$((num - 1))

if [ "$num" -lt 0 ] || [ "$num" -ge ${#networks[@]} ]; then
    echo "Invalid selection."
    exit 1
fi

# Extract SSID
SSID=$(echo "${networks[num]}" | cut -d: -f1)
CONNECTION_NAME="${SSID//[^a-zA-Z0-9]/_}"

echo "Selected: $SSID"
read -s -p "Enter password for $SSID: " PASSWORD
echo

echo "==> Connecting to $SSID..."

# Connect and save
nmcli device wifi connect "$SSID" password "$PASSWORD" \
    name "$CONNECTION_NAME" \
    autoconnect yes

echo "  [OK] Connected to $SSID"
echo "  [OK] Saved as: $CONNECTION_NAME (auto-connects on boot)"

echo ""
echo "==> Status:"
nmcli connection show --active
