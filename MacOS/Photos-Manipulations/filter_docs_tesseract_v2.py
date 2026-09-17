#!/usr/bin/env python3
"""
Improved document detector using Tesseract OCR. Single-threaded.
See filter_docs_tesseract_parallel.py for the multithreaded version.

Improvements over filter_docs_tesseract_basic.py:
- Pre-processes the image (grayscale + 2× contrast boost) before OCR.
  This destroys photo texture and makes black text on white backgrounds
  much more legible to Tesseract.
- Counts actual words (≥3 characters) instead of raw characters, which
  filters out punctuation noise like ". | / '"

Threshold: 15 words. Lower to catch sparse labels; raise to require dense text.

Run from the folder containing the JPEGs.
Requirements: brew install tesseract && pip install pytesseract Pillow
"""

import os
import shutil
import re
import pytesseract
from PIL import Image, ImageEnhance, ImageOps

SOURCE_DIR = "."
DEST_DIR = os.path.join(SOURCE_DIR, "Documents22")

os.makedirs(DEST_DIR, exist_ok=True)

for filename in os.listdir(SOURCE_DIR):
    if filename.lower().endswith(('.jpg', '.jpeg')):
        file_path = os.path.join(SOURCE_DIR, filename)
        try:
            img = Image.open(file_path)

            # Grayscale removes color information that confuses Tesseract on photos.
            # 2× contrast boost makes light text on white backgrounds visible.
            img = ImageEnhance.Contrast(ImageOps.grayscale(img)).enhance(2.0)

            text = pytesseract.image_to_string(img)

            # \b\w{3,}\b skips single chars, numbers, and punctuation fragments.
            words = re.findall(r'\b\w{3,}\b', text)

            if len(words) >= 15:
                print(f"Document detected: {filename} ({len(words)} words)")
                shutil.move(file_path, os.path.join(DEST_DIR, filename))
            else:
                print(f"Skipping photo: {filename} (Only {len(words)} words)")

        except Exception as e:
            print(f"Error reading {filename}: {e}")

print("Filtering complete.")
