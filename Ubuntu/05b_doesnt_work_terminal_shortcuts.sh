#!/bin/bash

UUID="b1dcc9dd-5262-4d8d-a863-c897e6d979b9"
PROFILE_PATH="org.gnome.Terminal.Legacy.Keybindings:/org/gnome/terminal/legacy/keybindings/:$UUID/"

echo "Applying to profile $UUID..."

gsettings set "$PROFILE_PATH" close-tab '<Control>w'
gsettings set "$PROFILE_PATH" close-window '<Control>q'
gsettings set "$PROFILE_PATH" copy '<Control>c'
gsettings set "$PROFILE_PATH" find '<Control>F'
gsettings set "$PROFILE_PATH" find-clear '<Control>J'
gsettings set "$PROFILE_PATH" find-next '<Control>G'
gsettings set "$PROFILE_PATH" find-previous '<Control>H'
gsettings set "$PROFILE_PATH" move-tab-left '<Control>Page_Up'
gsettings set "$PROFILE_PATH" move-tab-right '<Control>Page_Down'
gsettings set "$PROFILE_PATH" new-tab '<Control>t'
gsettings set "$PROFILE_PATH" new-window '<Control>n'
gsettings set "$PROFILE_PATH" paste '<Control>v'

echo "Done. Close ALL terminals, run 'killall gnome-terminal', reopen."
echo "Verify: gsettings get $PROFILE_PATH copy"

