# Photos-Manipulations

A collection of macOS command-line scripts for organizing and processing photos, organized into three folders by purpose.

---

## Upscale_Photos

AI-based photo upscaling using [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN). Runs fully locally — no internet required after setup, no watermarks.

### Prerequisites

**1. Install the upscaling binary (one-time):**

```bash
cd Upscale_Photos
bash setup_realesrgan.sh
```

This downloads `realesrgan-ncnn-vulkan` and its model weights into `Upscale_Photos/bin/` — no global install, no PATH changes needed.

**2. Set up a Python virtual environment (one-time):**

Run from `MacOS/Photos-Manipulations/` (the parent of `Upscale_Photos/`):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pillow pillow-heif
```

### Usage

```bash
# From MacOS/Photos-Manipulations/
source .venv/bin/activate
cd Upscale_Photos
python upscale_photo.py <input_file> [--scale 2|4] [--output path]
```

| Argument | Description | Default |
|---|---|---|
| `input_file` | Path to a JPEG or HEIC file | required |
| `--scale` | Upscale factor: `2` or `4` | `4` |
| `--output` | Output file path | `<input_stem>_upscaled.jpg` next to input |

Output is always JPEG.

### Examples

```bash
# 4x upscale, output next to input
python upscale_photo.py ~/Photos/IMG_3859.jpg

# 2x upscale to a specific path
python upscale_photo.py ~/Photos/IMG_3859.HEIC --scale 2 --output ~/Desktop/result.jpg
```

### Alternatives

[Upscayl](https://github.com/upscayl/upscayl) — free, open-source GUI app using the same Real-ESRGAN engine. Easier to use if scripting/CLI integration is not needed.

### Assumptions

- macOS only (universal binary, works on Apple Silicon and Intel)
- HEIC input is converted to a temp JPEG before processing and cleaned up automatically
- Models: `realesrgan-x4plus` for 4x (photo-optimised), `realesr-animevideov3-x2` for 2x
- The binary and models live in `Upscale_Photos/bin/` — self-contained, portable; move the whole `Upscale_Photos/` folder to another Mac and re-run `setup_realesrgan.sh`
- Very large images (e.g. already-upscaled files) may crash the binary due to GPU memory limits

---

## Filter_Photos

Scripts that analyze each photo and move matching ones into a subfolder. Run from the folder containing the photos.

| Script | What it filters |
|---|---|
| `filter_docs_apple_vision.py` | Document/text photos (Apple Vision OCR) |
| `filter_docs_native.swift` | Document/text photos (native Swift/Vision) |
| `filter_docs_tesseract_basic.py` | Document/text photos (Tesseract OCR, basic) |
| `filter_docs_tesseract_parallel.py` | Document/text photos (Tesseract OCR, parallel) |
| `filter_docs_tesseract_v2.py` | Document/text photos (Tesseract OCR, v2) |
| `filter_gray_walls.py` | Grey/white wall photos |
| `filter_handwritten_apple_vision.py` | Handwritten content (Apple Vision) |
| `filter_red_photos.py` | Photos with dominant red colour |
| `filter_renovation_photos.py` | Renovation-related photos |
| `filter_screenshots.sh` | iPhone/iPad screenshots (dimension-based detection) |

---

## Organize_Photos

Scripts for converting and organizing photos by date or type.

| Script | What it does |
|---|---|
| `heic_to_jpeg.sh` | Batch-convert all HEIC files in the current directory to JPEG using macOS `sips` |
| `organize_by_date.py` | Move photos into `YYYY/MM/` folders by capture date (reads EXIF) |
