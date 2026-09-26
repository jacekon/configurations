#!/usr/bin/env zsh
# Maps Home, End, Shift+Up, Shift+Down in the active macOS Terminal profile.

PROFILE=$(defaults read com.apple.Terminal "Default Window Settings" 2>/dev/null)
[ -z "$PROFILE" ] && PROFILE=Basic
PLB=/usr/libexec/PlistBuddy
ESC=$(printf '\033')
KEYMAPS=/System/Applications/Utilities/Terminal.app/Contents/Resources/keyMappings.plist
TPL=$(mktemp -t com.apple.Terminal) || return 1

defaults export com.apple.Terminal "$TPL" || return 1
# Each Add fails harmlessly when the level already exists.  The profile
# dict is missing entirely until some profile setting is changed, so it
# gets created with the identity keys Terminal itself writes.
$PLB -c "Add :'Window Settings' dict" "$TPL" 2>/dev/null
$PLB -c "Add :'Window Settings':'$PROFILE' dict" "$TPL" 2>/dev/null \
    && $PLB -c "Add :'Window Settings':'$PROFILE':name string $PROFILE" "$TPL" 2>/dev/null \
    && $PLB -c "Add :'Window Settings':'$PROFILE':type string Window Settings" "$TPL" 2>/dev/null
$PLB -c "Add :'Window Settings':'$PROFILE':keyMapBoundKeys dict" "$TPL" 2>/dev/null
# Merge reports every collision on stdout, which is noise here: a rerun
# collides on all of them.
[ -f "$KEYMAPS" ] && \
    $PLB -c "Merge $KEYMAPS :'Window Settings':'$PROFILE':keyMapBoundKeys" "$TPL" >/dev/null
# Add-then-Set so an existing mapping is corrected rather than skipped.
$PLB -c "Add :'Window Settings':'$PROFILE':keyMapBoundKeys:F729 string ${ESC}OH" "$TPL" 2>/dev/null \
    || $PLB -c "Set :'Window Settings':'$PROFILE':keyMapBoundKeys:F729 ${ESC}OH" "$TPL"
$PLB -c "Add :'Window Settings':'$PROFILE':keyMapBoundKeys:F72B string ${ESC}OF" "$TPL" 2>/dev/null \
    || $PLB -c "Set :'Window Settings':'$PROFILE':keyMapBoundKeys:F72B ${ESC}OF" "$TPL"
$PLB -c "Add :'Window Settings':'$PROFILE':keyMapBoundKeys:\$F700 string ${ESC}[1;2A" "$TPL" 2>/dev/null \
    || $PLB -c "Set :'Window Settings':'$PROFILE':keyMapBoundKeys:\$F700 ${ESC}[1;2A" "$TPL"
$PLB -c "Add :'Window Settings':'$PROFILE':keyMapBoundKeys:\$F701 string ${ESC}[1;2B" "$TPL" 2>/dev/null \
    || $PLB -c "Set :'Window Settings':'$PROFILE':keyMapBoundKeys:\$F701 ${ESC}[1;2B" "$TPL"

$PLB -c "Delete :'Window Settings':'$PROFILE':keyMapBoundBySelector" "$TPL" 2>/dev/null
# Close window when shell exits (2 = close, 1 = close if clean, 0 = don't close)
$PLB -c "Add :'Window Settings':'$PROFILE':shellExitAction integer 2" "$TPL" 2>/dev/null \
    || $PLB -c "Set :'Window Settings':'$PROFILE':shellExitAction 2" "$TPL"
# Option key sends ESC prefix (Meta) so alt-* shortcuts reach terminal apps like mc
$PLB -c "Add :'Window Settings':'$PROFILE':useOptionAsMetaKey bool true" "$TPL" 2>/dev/null \
    || $PLB -c "Set :'Window Settings':'$PROFILE':useOptionAsMetaKey true" "$TPL"
defaults import com.apple.Terminal "$TPL" && \
    echo "Mapped Home, End, Shift+Up and Shift+Down in Terminal profile \"$PROFILE\""
rm -f "$TPL"
