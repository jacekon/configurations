#!/usr/bin/env bash
# Downloads realesrgan-ncnn-vulkan macOS binary and installs it into bin/ next to this script.
# Run once before using upscale_photo.py.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VERSION="v0.2.5.0"
ZIP_NAME="realesrgan-ncnn-vulkan-20220424-macos.zip"
URL="https://github.com/xinntao/Real-ESRGAN/releases/download/${VERSION}/${ZIP_NAME}"
INSTALL_DIR="$SCRIPT_DIR/bin"
BINARY="realesrgan-ncnn-vulkan"

echo "Downloading Real-ESRGAN ncnn-vulkan ${VERSION}..."
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

curl -fsSL "$URL" -o "$TMP_DIR/$ZIP_NAME"
unzip -q "$TMP_DIR/$ZIP_NAME" -d "$TMP_DIR/extracted"

mkdir -p "$INSTALL_DIR"

# Find and copy the binary
BINARY_PATH=$(find "$TMP_DIR/extracted" -name "$BINARY" -type f | head -1)
if [ -z "$BINARY_PATH" ]; then
    echo "Error: could not find '$BINARY' in the downloaded zip." >&2
    exit 1
fi
cp "$BINARY_PATH" "$INSTALL_DIR/$BINARY"
chmod +x "$INSTALL_DIR/$BINARY"

# Copy model files next to the binary (required at runtime)
MODELS_SRC=$(find "$TMP_DIR/extracted" -type d -name "models" | head -1)
if [ -z "$MODELS_SRC" ]; then
    echo "Error: could not find 'models/' folder in the downloaded zip." >&2
    exit 1
fi
cp -r "$MODELS_SRC" "$INSTALL_DIR/models"

echo "Installed: $INSTALL_DIR/$BINARY"
echo "Models:    $INSTALL_DIR/models/"
echo "Ready — no PATH changes needed."
