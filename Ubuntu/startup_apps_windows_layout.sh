#!/bin/bash

# first start apps in the background:
docker start searxng

#now start gui apps:
SCREEN_W=3440
SCREEN_H=1440
LEFT_W=1400
MID_W=1400
RIGHT_W=640
MID_X=$LEFT_W
RIGHT_X=$((SCREEN_W - RIGHT_W))

# Returns: is_csd(0|1)  left right top bottom
# CSD windows (_GTK_FRAME_EXTENTS) need size adjustment too;
# WM-framed windows (_NET_FRAME_EXTENTS) only need position adjustment.
get_extents() {
    local wid="$1"
    local out is_csd=0
    out=$(xprop -id "$wid" _GTK_FRAME_EXTENTS 2>/dev/null | grep -oP '\d+' | paste -sd ' ')
    if [ -n "$out" ]; then
        is_csd=1
    else
        out=$(xprop -id "$wid" _NET_FRAME_EXTENTS 2>/dev/null | grep -oP '\d+' | paste -sd ' ')
    fi
    echo "$is_csd ${out:-0 0 0 0}"
}

# move_window SEARCH tx ty tw th [use_class=0|1]
# tx/ty/tw/th are the TARGET VISIBLE content rectangle — shadows/frames are compensated.
# move_window SEARCH tx ty tw th [use_class=0|1]
# move_window SEARCH tx ty tw th [use_class=0|1]
move_window() {
    local search="$1" tx=$2 ty=$3 tw=$4 th=$5 use_class="${6:-0}"
    local wid=""

    for _ in $(seq 1 20); do
        if [ "$use_class" = "1" ]; then
            wid=$(wmctrl -lx 2>/dev/null | grep -i "$search" | awk '{print $1}' | tail -1)
        else
            wid=$(wmctrl -l  2>/dev/null | grep -i "$search" | awk '{print $1}' | tail -1)
        fi
        [ -n "$wid" ] && break
        sleep 1
    done

    [ -z "$wid" ] && { echo "⚠  Not found: '$search'" >&2; return 1; }

    # === THE FIX ===
    # Strip the hardcoded minimum size constraint from the window.
    # This allows it to actually shrink to your requested $tw (700px) 
    # so the Window Manager won't forcefully shove it back to the left.
    xprop -id "$wid" -remove WM_NORMAL_HINTS 2>/dev/null
    # ===============

    wmctrl -i -r "$wid" -b remove,maximized_vert,maximized_horz
    sleep 0.3

    read is_csd fl fr ft fb <<< "$(get_extents "$wid")"
    fl=${fl:-0}; fr=${fr:-0}; ft=${ft:-0}; fb=${fb:-0}

    local x=$((tx - fl))
    local y=$((ty - ft))
    local w h

    if [ "$is_csd" = "1" ]; then
        w=$((tw + fl + fr))
        h=$((th + ft + fb))
    else
        w=$tw
        h=$th
    fi

    # Now that the size limit is removed, this single command will place it perfectly
    wmctrl -i -r "$wid" -e "1,$x,$y,$w,$h"
    echo "✔  '$search' [CSD=$is_csd extents=$fl,$fr,$ft,$fb] → visible ($tx,$ty) ${tw}×${th}"
}

# ── 1. Brave ──────────────────────────────────────────────────────────────
brave 2>/dev/null &
sleep 4
move_window "Brave" 0 0 $LEFT_W $SCREEN_H

# ── 2. htop — top-middle ──────────────────────────────────────────────────
gnome-terminal --class="HtopTerm" --title="Htop" -- bash -c "htop; exec bash" &
sleep 2
move_window "HtopTerm" $MID_X 0 $MID_W $((SCREEN_H / 2)) 1

# ── 3. Terminal — bottom-middle ───────────────────────────────────────────
gnome-terminal --class="BottomTerm" --title="Terminal" -- bash -c "journalctl -f -u ollama -u openclaw CONTAINER_NAME=searxng" &
sleep 2
move_window "BottomTerm" $MID_X $((SCREEN_H / 2)) $MID_W $((SCREEN_H / 2)) 1

# ── 4. NVIDIA Settings ────────────────────────────────────────────────────
nvidia-settings --page="Thermal Settings" 2>/dev/null &
sleep 7
move_window "NVIDIA" $RIGHT_X 0 $RIGHT_W $((SCREEN_H / 3))

# ── 5. System Monitor ─────────────────────────────────────────────────────
gnome-system-monitor 2>/dev/null &
sleep 3
move_window "System Monitor" $RIGHT_X $((SCREEN_H / 3)) $RIGHT_W $((SCREEN_H * 2 / 3))

