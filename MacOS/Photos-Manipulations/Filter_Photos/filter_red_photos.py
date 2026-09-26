#!/usr/bin/env python3
"""
Moves images that contain a significant amount of red into Red_Pictures/.

Uses HSV color space: red wraps around both ends of the hue wheel (0–15 and 240–255).
Saturation and brightness guards prevent dark browns or near-grays from matching.

Threshold: 5% of pixels must be red (min_red_ratio=0.05). Lower to catch faint red
accents; raise to require dominant red subjects.

Run from the folder containing the JPEGs.
Requirements: pip install Pillow numpy
"""

import os
import shutil
import concurrent.futures
import numpy as np
from PIL import Image

SOURCE_DIR = "."
DEST_DIR = os.path.join(SOURCE_DIR, "Red_Pictures")

os.makedirs(DEST_DIR, exist_ok=True)

def contains_red(file_path, min_red_ratio=0.05):
    try:
        with Image.open(file_path) as img:
            # Downsample to 200x200 — enough for color ratios, much faster than full res.
            hsv_data = np.array(img.resize((200, 200)).convert('HSV'))

            h = hsv_data[:, :, 0]  # Hue    0–255 (PIL maps 0°–360° → 0–255)
            s = hsv_data[:, :, 1]  # Sat    0–255
            v = hsv_data[:, :, 2]  # Value  0–255

            # Red sits at both extremes of the hue wheel.
            is_red_hue = (h < 15) | (h > 240)
            # Require visible color and brightness to exclude muddy browns and grays.
            is_colorful = s > 70
            is_bright   = v > 70

            red_ratio = np.mean(is_red_hue & is_colorful & is_bright)
            return red_ratio >= min_red_ratio, red_ratio

    except Exception as e:
        print(f"[ERROR] Could not process {file_path}: {e}")
        return False, 0.0

def process_image(filename):
    file_path = os.path.join(SOURCE_DIR, filename)
    is_match, red_ratio = contains_red(file_path)
    if is_match:
        print(f"[MATCH] {filename} ({red_ratio*100:.1f}% red)")
        shutil.move(file_path, os.path.join(DEST_DIR, filename))
    else:
        print(f"[SKIP]  {filename} ({red_ratio*100:.1f}% red)")

files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.jpg', '.jpeg'))]
print(f"Found {len(files)} JPEGs. Scanning for red content...")

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(process_image, files)

print("Done.")
