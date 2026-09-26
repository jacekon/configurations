#!/usr/bin/env python3
"""
Parallel document detector using Tesseract OCR.
Same logic as filter_docs_tesseract_v2.py but uses ThreadPoolExecutor
to saturate CPU cores on large batches. ~4–8× faster on a modern Mac.

Run from the folder containing the JPEGs.
Requirements: brew install tesseract && pip install pytesseract Pillow
"""

import os
import shutil
import re
import pytesseract
from PIL import Image, ImageEnhance, ImageOps
import concurrent.futures

SOURCE_DIR = "."
DEST_DIR = os.path.join(SOURCE_DIR, "DocumentsMulti")

os.makedirs(DEST_DIR, exist_ok=True)

def process_image(filename):
    file_path = os.path.join(SOURCE_DIR, filename)
    try:
        img = Image.open(file_path)
        # Grayscale + contrast boost makes black-on-white text legible to Tesseract
        # while suppressing the color noise typical of photos.
        img = ImageEnhance.Contrast(ImageOps.grayscale(img)).enhance(2.0)

        text = pytesseract.image_to_string(img)
        words = re.findall(r'\b\w{3,}\b', text)

        if len(words) >= 15:
            print(f"[MATCH] Document detected: {filename} ({len(words)} words)")
            shutil.move(file_path, os.path.join(DEST_DIR, filename))
        else:
            print(f"[SKIP]  {filename} (Only {len(words)} words)")

    except Exception as e:
        print(f"[ERROR] Error reading {filename}: {e}")

files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.jpg', '.jpeg'))]
print(f"Found {len(files)} JPEGs. Starting multithreaded processing...")

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(process_image, files)

print("Filtering complete.")
