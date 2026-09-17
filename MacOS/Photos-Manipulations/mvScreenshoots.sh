#!/bin/bash

SOURCE="${1:-.}"
DEST="$SOURCE/Screenshots"

mkdir -p "$DEST"

find "$SOURCE" -maxdepth 1 -type f \( \
    -iname "*.jpg" -o \
    -iname "*.jpeg" -o \
    -iname "*.png" -o \
    -iname "*.heic" \
\) -print0 | while IFS= read -r -d '' file; do

    width=$(sips -g pixelWidth "$file" 2>/dev/null | awk '/pixelWidth:/ {print $2}')
    height=$(sips -g pixelHeight "$file" 2>/dev/null | awk '/pixelHeight:/ {print $2}')

    # Common iPhone/iPad screenshot dimensions
    case "${width}x${height}" in
        1080x2340|2340x1080|1290x2796|2796x1290|1284x2778|2778x1284|\
        1242x2688|2688x1242|1125x2436|2436x1125|\
        828x1792|1792x828|750x1334|1334x750|\
        1080x1920|1920x1080|\
        2048x2732|2732x2048)
            echo "Screenshot: $file (${width}x${height})"
            mv "$file" "$DEST/"
            ;;
    esac
done
