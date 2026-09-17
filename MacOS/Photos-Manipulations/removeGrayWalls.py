#!/usr/bin/env python3
import os
import shutil
import concurrent.futures
import numpy as np
from PIL import Image

SOURCE_DIR = "."
DEST_DIR = os.path.join(SOURCE_DIR, "Concrete_Walls")

os.makedirs(DEST_DIR, exist_ok=True)

def is_gray_concrete(file_path, gray_ratio_threshold=0.65, max_saturation=35, min_brightness=40, max_brightness=220):
    """
    Analyzes an image to see if it is dominated by gray pixels (like concrete/plaster).
    Returns (True/False, gray_percentage).
    """
    try:
        with Image.open(file_path) as img:
            # 1. Downsample to 200x200 to make matrix calculations instant
            img_small = img.resize((200, 200)).convert('HSV')
            
            # Convert pixel data to numpy array
            hsv_data = np.array(img_small)
            
            # Extract Saturation (S) and Value/Brightness (V) channels (0-255 scale)
            s_channel = hsv_data[:, :, 1]
            v_channel = hsv_data[:, :, 2]
            
            # 2. Mask pixels that are desaturated (gray) and within realistic wall brightness
            gray_mask = (s_channel < max_saturation) & (v_channel > min_brightness) & (v_channel < max_brightness)
            
            # 3. Calculate percentage of gray pixels across the image
            gray_ratio = np.mean(gray_mask)
            
            return gray_ratio >= gray_ratio_threshold, gray_ratio
            
    except Exception as e:
        print(f"[ERROR] Could not process {file_path}: {e}")
        return False, 0.0

def process_image(filename):
    file_path = os.path.join(SOURCE_DIR, filename)
    
    is_concrete, ratio = is_gray_concrete(file_path)
    percentage = ratio * 100
    
    if is_concrete:
        print(f"[MATCH] Concrete/Wall detected: {filename} ({percentage:.1f}% gray)")
        shutil.move(file_path, os.path.join(DEST_DIR, filename))
    else:
        print(f"[SKIP] {filename} ({percentage:.1f}% gray)")

files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.jpg', '.jpeg'))]

print(f"Found {len(files)} JPEGs. Scanning for gray/concrete walls...")

# Multithreaded execution
with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(process_image, files)

print("Filtering complete.")
