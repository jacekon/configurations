#!/usr/bin/env python3
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
        # Explicitly set recognition_level="accurate" to load Apple's handwriting models
        annotations = ocrmac.OCR(file_path, recognition_level="accurate").recognize()
        
        valid_words = 0
        
        for text, confidence, bbox in annotations:
            # Lower confidence to 0.4 to catch handwriting, but still kill pure noise (< 0.4)
            if confidence > 0.4:
                # Count actual words that are 3+ characters long
                words = [w for w in text.split() if len(w) >= 3]
                valid_words += len(words)
                
        # We can keep the threshold at 1 valid word, or slightly increase it to 2 
        # to balance out the lower confidence requirement.
        if valid_words >= 1:
            print(f"[MATCH] Document detected: {filename} ({valid_words} words)")
            shutil.move(file_path, os.path.join(DEST_DIR, filename))
        else:
            print(f"[SKIP] {filename} (Only {valid_words} valid words)")
            
    except Exception as e:
        print(f"[ERROR] Error reading {filename}: {e}")

files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.jpg', '.jpeg'))]

print(f"Found {len(files)} JPEGs. Starting Apple ML processing...")

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(process_image, files)

print("Filtering complete.")
