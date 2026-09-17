#!/usr/bin/env python3
"""
Moves gray/concrete wall photos into Concrete_Walls/.

Detects images dominated by neutral gray (concrete, plaster, bare walls).
Useful for cleaning up renovation or real-estate photo dumps.

Algorithm: resize to 200×200, convert to HSV, count pixels with low saturation
and mid-range brightness. If ≥65% of pixels qualify as gray, it's a wall photo.

Thresholds:
  gray_ratio_threshold=0.65  — at least 65% of the image must be gray
  max_saturation=35          — pixel must be nearly colorless (0–255 scale)
  min_brightness=40          — exclude very dark/shadowed areas
  max_brightness=220         — exclude blown-out white pixels (those aren't concrete)

Run from the folder containing the JPEGs.
Requirements: pip install Pillow numpy
"""

import os
import shutil
import concurrent.futures
import numpy as np
from PIL import Image

SOURCE_DIR = "."
DEST_DIR = os.path.join(SOURCE_DIR, "Concrete_Walls")

os.makedirs(DEST_DIR, exist_ok=True)

def is_gray_concrete(file_path, gray_ratio_threshold=0.65, max_saturation=35,
                     min_brightness=40, max_brightness=220):
    try:
        with Image.open(file_path) as img:
            hsv_data = np.array(img.resize((200, 200)).convert('HSV'))

            s = hsv_data[:, :, 1]  # Saturation
            v = hsv_data[:, :, 2]  # Value / brightness

            # Low saturation = no color. Brightness range excludes pitch-black shadows
            # and blown-out whites that would otherwise skew the ratio.
            gray_mask = (s < max_saturation) & (v > min_brightness) & (v < max_brightness)
            gray_ratio = np.mean(gray_mask)

            return gray_ratio >= gray_ratio_threshold, gray_ratio

    except Exception as e:
        print(f"[ERROR] Could not process {file_path}: {e}")
        return False, 0.0

def process_image(filename):
    file_path = os.path.join(SOURCE_DIR, filename)
    is_concrete, ratio = is_gray_concrete(file_path)
    if is_concrete:
        print(f"[MATCH] {filename} ({ratio*100:.1f}% gray)")
        shutil.move(file_path, os.path.join(DEST_DIR, filename))
    else:
        print(f"[SKIP]  {filename} ({ratio*100:.1f}% gray)")

files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.jpg', '.jpeg'))]
print(f"Found {len(files)} JPEGs. Scanning for gray/concrete walls...")

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(process_image, files)

print("Filtering complete.")
