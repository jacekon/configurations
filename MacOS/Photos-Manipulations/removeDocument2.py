#!/usr/bin/env python3
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
            
            # 1. Pre-process: Convert to grayscale and boost contrast 
            # This destroys photo textures but makes black text on white backgrounds highly visible
            img = ImageOps.grayscale(img)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            
            # Extract text
            text = pytesseract.image_to_string(img)
            
            # 2. Filter: Find actual alphanumeric words (3 or more characters)
            # This ignores random punctuation noise like "/ | . '"
            words = re.findall(r'\b\w{3,}\b', text)
            
            # 3. Threshold: Require at least 15 actual words to classify as a document
            if len(words) >= 15:
                print(f"Document detected: {filename} ({len(words)} words)")
                shutil.move(file_path, os.path.join(DEST_DIR, filename))
            else:
                print(f"Skipping photo: {filename} (Only {len(words)} words)")
                
        except Exception as e:
            print(f"Error reading {filename}: {e}")

print("Filtering complete.")
