#!/usr/bin/env python3
"""
Moves document-like images (screenshots of text, scanned pages) into Documents/.

Uses Tesseract OCR (pytesseract). A raw character count of >30 is the trigger —
quick to compute but imprecise; see filter_docs_tesseract_v2.py for better accuracy.

Run from the folder containing the JPEGs.
Requirements: brew install tesseract && pip install pytesseract Pillow
"""

import os
import shutil
import pytesseract
from PIL import Image

SOURCE_DIR = "."
DEST_DIR = os.path.join(SOURCE_DIR, "Documents")

os.makedirs(DEST_DIR, exist_ok=True)

for filename in os.listdir(SOURCE_DIR):
    if filename.lower().endswith(('.jpg', '.jpeg')):
        file_path = os.path.join(SOURCE_DIR, filename)
        try:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img).strip()

            # 30 chars is a low bar — catches even sparse labels, but also
            # misclassifies photos with visible signs or labels. Raise to ~100
            # if you want stricter document detection.
            if len(text) > 30:
                print(f"Document detected: {filename} ({len(text)} characters)")
                shutil.move(file_path, os.path.join(DEST_DIR, filename))
            else:
                print(f"Skipping photo: {filename}")

        except Exception as e:
            print(f"Error reading {filename}: {e}")

print("Filtering complete.")
