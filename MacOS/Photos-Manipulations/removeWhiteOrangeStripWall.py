#!/usr/bin/env python3
import os
import shutil
import concurrent.futures
import numpy as np
from PIL import Image

SOURCE_DIR = "."
DEST_DIR = os.path.join(SOURCE_DIR, "Renovation_Floors")

os.makedirs(DEST_DIR, exist_ok=True)

def is_wall_and_floor(file_path, min_wall_ratio=0.40, min_floor_ratio=0.08):
    """
    Checks if an image contains a significant amount of white-ish wall 
    AND a visible portion of orange floorboard.
    """
    try:
        with Image.open(file_path) as img:
            # Downsample to 200x200 for instant matrix math
            img_small = img.resize((200, 200)).convert('HSV')
            hsv_data = np.array(img_small)
            
            h_channel = hsv_data[:, :, 0] # 0-255 (Hue: 0=Red, 21=Orange, 42=Yellow)
            s_channel = hsv_data[:, :, 1] # 0-255 (Saturation)
            v_channel = hsv_data[:, :, 2] # 0-255 (Value/Brightness)
            
            # 1. Identify White-ish Wall Pixels
            # High brightness, very low color saturation
            wall_mask = (s_channel < 45) & (v_channel > 160)
            
            # 2. Identify Orange Floorboard Pixels
            # Hue between red-orange and yellow-orange, with visible color and brightness
            floor_mask = (h_channel > 10) & (h_channel < 45) & (s_channel > 60) & (v_channel > 60)
            
            # Calculate what percentage of the image is covered by each
            wall_ratio = np.mean(wall_mask)
            floor_ratio = np.mean(floor_mask)
            
            # Both conditions must be met
            is_match = (wall_ratio >= min_wall_ratio) and (floor_ratio >= min_floor_ratio)
            
            return is_match, wall_ratio, floor_ratio
            
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
        print(f"[SKIP] {filename} (Wall: {wall_ratio*100:.1f}%, Floor: {floor_ratio*100:.1f}%)")

files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.jpg', '.jpeg'))]

print(f"Found {len(files)} JPEGs. Scanning for white walls + orange floors...")

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(process_image, files)

print("Filtering complete.")
