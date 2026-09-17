#!/usr/bin/env python3
import os
import shutil
import pytesseract
from PIL import Image

SOURCE_DIR = "."
DEST_DIR = os.path.join(SOURCE_DIR, "Documents")

# Create the destination folder if it doesn't exist
os.makedirs(DEST_DIR, exist_ok=True)

for filename in os.listdir(SOURCE_DIR):
    # Only process JPG files
    if filename.lower().endswith(('.jpg', '.jpeg')):
        file_path = os.path.join(SOURCE_DIR, filename)
        
        try:
            # Open the image and extract text
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img).strip()
            
            # If the image contains more than 30 characters of text, classify as document
            if len(text) > 30:
                print(f"Document detected: {filename} ({len(text)} characters)")
                shutil.move(file_path, os.path.join(DEST_DIR, filename))
            else:
                print(f"Skipping photo: {filename}")
                
        except Exception as e:
            print(f"Error reading {filename}: {e}")

print("Filtering complete.")
