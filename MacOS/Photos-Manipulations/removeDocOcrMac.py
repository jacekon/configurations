#!/usr/bin/env python3
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
        # ocrmac uses Apple's native Vision framework (Live Text)
        annotations = ocrmac.OCR(file_path).recognize()
        
        valid_words = 0
        
        # annotations returns a list of tuples: (text, confidence_score, bounding_box)
        for text, confidence, bbox in annotations:
            # 1. Reject low-confidence ML guesses (kills texture hallucinations)
            if confidence > 0.8:
                # 2. Count actual words that are 3+ characters long
                words = [w for w in text.split() if len(w) >= 3]
                valid_words += len(words)
                
        # 3. Threshold: 10 highly-confident words is our trigger
        if valid_words >= 10:
            print(f"[MATCH] Document/Screen detected: {filename} ({valid_words} words)")
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
