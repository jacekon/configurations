#!/usr/bin/env python3
import os
import shutil
import concurrent.futures
import numpy as np
from PIL import Image

SOURCE_DIR = "."
DEST_DIR = os.path.join(SOURCE_DIR, "Red_Pictures")

os.makedirs(DEST_DIR, exist_ok=True)

def contains_red(file_path, min_red_ratio=0.05):
    """
    Checks if an image contains a noticeable amount of red.
    min_red_ratio=0.05 means at least 5% of the photo must be red.
    """
    try:
        with Image.open(file_path) as img:
            # Downsample to 200x200 for instant matrix math
            img_small = img.resize((200, 200)).convert('HSV')
            hsv_data = np.array(img_small)
            
            h_channel = hsv_data[:, :, 0] # 0-255 (Hue)
            s_channel = hsv_data[:, :, 1] # 0-255 (Saturation)
            v_channel = hsv_data[:, :, 2] # 0-255 (Value/Brightness)
            
            # 1. Identify Red Pixels
            # Red sits at the two extreme ends of the Hue scale (0-15 and 240-255)
            # We also require moderate saturation and brightness so it doesn't count dark brown or gray
            is_red_hue = (h_channel < 15) | (h_channel > 240)
            is_colorful = s_channel > 70
            is_bright_enough = v_channel > 70
            
            red_mask = is_red_hue & is_colorful & is_bright_enough
            
            # Calculate what percentage of the image is covered by red
            red_ratio = np.mean(red_mask)
            
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
        print(f"[SKIP] {filename} ({red_ratio*100:.1f}% red)")

files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.jpg', '.jpeg'))]

print(f"Found {len(files)} JPEGs. Scanning for shades of red...")

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(process_image, files)

print("Filtering complete.")
