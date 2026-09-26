#!/usr/bin/env python3
"""
Moves renovation-phase photos into Renovation_Floors/.

Detects images that have BOTH a white-ish wall AND orange/wood floorboards —
a color combination typical of mid-renovation interior shots.

Both conditions must be met simultaneously; neither alone triggers a match.

Thresholds:
  min_wall_ratio=0.40   — at least 40% white/light-gray pixels (high-brightness, low-sat)
  min_floor_ratio=0.08  — at least 8% orange/warm-wood pixels

HSV hue (PIL 0–255 scale, where 0=red, ~21=orange, ~42=yellow):
  Wall:  saturation < 45, brightness > 160  (near-white)
  Floor: hue 10–45, saturation > 60, brightness > 60  (orange/tan wood)

Run from the folder containing the JPEGs.
Requirements: pip install Pillow numpy
"""

import os
import shutil
import concurrent.futures
import numpy as np
from PIL import Image

SOURCE_DIR = "."
DEST_DIR = os.path.join(SOURCE_DIR, "Renovation_Floors")

os.makedirs(DEST_DIR, exist_ok=True)

def is_wall_and_floor(file_path, min_wall_ratio=0.40, min_floor_ratio=0.08):
    try:
        with Image.open(file_path) as img:
            hsv_data = np.array(img.resize((200, 200)).convert('HSV'))

            h = hsv_data[:, :, 0]  # Hue    (PIL: 0–255)
            s = hsv_data[:, :, 1]  # Sat    (0–255)
            v = hsv_data[:, :, 2]  # Value  (0–255)

            # White/light-gray wall: high brightness, near-zero saturation.
            wall_mask  = (s < 45)  & (v > 160)

            # Orange/warm-wood floor: hue between red-orange and yellow-orange.
            floor_mask = (h > 10) & (h < 45) & (s > 60) & (v > 60)

            wall_ratio  = np.mean(wall_mask)
            floor_ratio = np.mean(floor_mask)

            return (wall_ratio >= min_wall_ratio) and (floor_ratio >= min_floor_ratio), wall_ratio, floor_ratio

    except Exception as e:
        print(f"[ERROR] Could not process {file_path}: {e}")
        return False, 0.0, 0.0

def process_image(filename):
    file_path = os.path.join(SOURCE_DIR, filename)
    is_match, wall_ratio, floor_ratio = is_wall_and_floor(file_path)
    if is_match:
        print(f"[MATCH] {filename} (Wall: {wall_ratio*100:.1f}%, Floor: {floor_ratio*100:.1f}%)")
        shutil.move(file_path, os.path.join(DEST_DIR, filename))
    else:
        print(f"[SKIP]  {filename} (Wall: {wall_ratio*100:.1f}%, Floor: {floor_ratio*100:.1f}%)")

files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.jpg', '.jpeg'))]
print(f"Found {len(files)} JPEGs. Scanning for white walls + orange floors...")

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(process_image, files)

print("Filtering complete.")
