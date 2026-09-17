#!/usr/bin/env python3
"""
Moves images containing handwritten text into ../DocsHandWritten/ using Apple Vision.

Uses `ocrmac` with recognition_level="accurate" to load Apple's handwriting models.
The "accurate" level is required — the default "fast" level skips handwriting models.

Key differences from filter_docs_apple_vision.py (printed text):
- recognition_level="accurate" instead of default "fast"
- Confidence threshold lowered to 0.4 (handwriting is inherently less regular)
- Word threshold lowered to 1 (even a single legible word suggests handwriting)

Aggressive threshold means some false positives (photos with one visible word).
Raise valid_words threshold to 3–5 if you want stricter detection.

Run from the folder containing the JPEGs.
Requirements: pip install ocrmac
"""

import os
import shutil
import concurrent.futures
from ocrmac import ocrmac

SOURCE_DIR = "."
DEST_DIR = os.path.join(SOURCE_DIR, "../DocsHandWritten")

os.makedirs(DEST_DIR, exist_ok=True)

def process_image(filename):
    file_path = os.path.join(SOURCE_DIR, filename)
    try:
        # recognition_level="accurate" loads Apple's handwriting recognition models.
        annotations = ocrmac.OCR(file_path, recognition_level="accurate").recognize()

        valid_words = 0
        for text, confidence, bbox in annotations:
            # Lower threshold than printed-text scripts: handwriting confidence is naturally lower.
            if confidence > 0.4:
                valid_words += len([w for w in text.split() if len(w) >= 3])

        if valid_words >= 1:
            print(f"[MATCH] {filename} ({valid_words} words)")
            shutil.move(file_path, os.path.join(DEST_DIR, filename))
        else:
            print(f"[SKIP]  {filename} ({valid_words} valid words)")

    except Exception as e:
        print(f"[ERROR] {filename}: {e}")

files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.jpg', '.jpeg'))]
print(f"Found {len(files)} JPEGs. Starting Apple Vision handwriting detection...")

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(process_image, files)

print("Filtering complete.")
