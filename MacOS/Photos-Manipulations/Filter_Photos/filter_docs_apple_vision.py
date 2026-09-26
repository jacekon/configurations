#!/usr/bin/env python3
"""
Moves document/screenshot images into ../DocOcrMac/ using Apple's Vision OCR.

Uses the `ocrmac` Python binding to call Apple's native Vision framework (Live Text).
Better accuracy than Tesseract on iPhone screenshots and macOS-rendered text.

Trigger: ≥10 high-confidence words (confidence > 0.8).
The high confidence threshold rejects texture noise that Vision sometimes
mistakes for letters in detailed photographs.

For handwritten notes use filter_handwritten_apple_vision.py instead.

Run from the folder containing the JPEGs.
Requirements: pip install ocrmac
"""

import os
import shutil
import concurrent.futures
from ocrmac import ocrmac

SOURCE_DIR = "."
DEST_DIR = os.path.join(SOURCE_DIR, "../DocOcrMac")

os.makedirs(DEST_DIR, exist_ok=True)

def process_image(filename):
    file_path = os.path.join(SOURCE_DIR, filename)
    try:
        # Each annotation is (text, confidence, bounding_box).
        annotations = ocrmac.OCR(file_path).recognize()

        valid_words = 0
        for text, confidence, bbox in annotations:
            # 0.8 rejects low-confidence ML guesses from textured backgrounds.
            if confidence > 0.8:
                valid_words += len([w for w in text.split() if len(w) >= 3])

        if valid_words >= 10:
            print(f"[MATCH] {filename} ({valid_words} words)")
            shutil.move(file_path, os.path.join(DEST_DIR, filename))
        else:
            print(f"[SKIP]  {filename} ({valid_words} valid words)")

    except Exception as e:
        print(f"[ERROR] {filename}: {e}")

files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.jpg', '.jpeg'))]
print(f"Found {len(files)} JPEGs. Starting Apple Vision OCR...")

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(process_image, files)

print("Filtering complete.")
