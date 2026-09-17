#!/usr/bin/env python3
import os
import shutil
import re
import pytesseract
from PIL import Image, ImageEnhance, ImageOps
import concurrent.futures

SOURCE_DIR = "."
DEST_DIR = os.path.join(SOURCE_DIR, "DocumentsMulti")

# Create the destination folder if it doesn't exist
os.makedirs(DEST_DIR, exist_ok=True)

def process_image(filename):
    file_path = os.path.join(SOURCE_DIR, filename)
    
    try:
        # 1. Pre-process: Grayscale and contrast boost
        img = Image.open(file_path)
        img = ImageOps.grayscale(img)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        # 2. Extract text
        text = pytesseract.image_to_string(img)
        
        # 3. Filter: Find actual alphanumeric words (3 or more characters)
        words = re.findall(r'\b\w{3,}\b', text)
        
        # 4. Threshold: 15 actual words to classify as a document
        if len(words) >= 15:
            print(f"[MATCH] Document detected: {filename} ({len(words)} words)")
            shutil.move(file_path, os.path.join(DEST_DIR, filename))
        else:
            print(f"[SKIP] {filename} (Only {len(words)} words)")
            
    except Exception as e:
        print(f"[ERROR] Error reading {filename}: {e}")

# Gather only JPEG files
files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.jpg', '.jpeg'))]

print(f"Found {len(files)} JPEGs. Starting multithreaded processing...")

# Process files concurrently utilizing available CPU cores
with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(process_image, files)

print("Filtering complete.")
