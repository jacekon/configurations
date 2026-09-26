# Photo Upscaler Design

**Date:** 2026-09-26  
**Status:** Approved

## Overview

A CLI script to upscale a single photo using Real-ESRGAN, an AI-based upscaling model that produces high-quality results for real photographs. Fits alongside existing tools in `MacOS/Photos-Manipulations/`.

## Script

**Location:** `MacOS/Photos-Manipulations/upscale_photo.py`

**Usage:**
```
python upscale_photo.py <input_file> [--scale 4] [--output output.jpg]
```

**Arguments:**
- `input_file` — path to a JPEG or HEIC file (required)
- `--scale` — upscale factor: `2` or `4` (default: `4`)
- `--output` — output file path (default: `<input_basename>_upscaled.jpg` next to the input file)

## Architecture

Single self-contained Python script with no project-level dependencies beyond `realesrgan` and `pillow`.

**Flow:**
1. Parse arguments and validate input file exists and is JPEG or HEIC
2. If HEIC: convert to a temp JPEG using `pillow-heif`
3. Validate `--scale` is 2 or 4; print a clear error and exit if not
4. Run Real-ESRGAN with the requested scale factor
5. Save result as JPEG to the output path
6. Delete any temp files

## Input Formats

- JPEG (`.jpg`, `.jpeg`)
- HEIC (`.heic`, `.HEIC`) — converted to temp JPEG before processing

## Output

- Always JPEG
- Default output path: `<input_dir>/<input_stem>_upscaled.jpg`
- Overridable via `--output`

## Scale Factors

Real-ESRGAN natively supports 2x and 4x. Values outside these are rejected with a clear error message.

## Setup (one-time)

```bash
pip install realesrgan pillow pillow-heif
```

## Model Weights

Weights are stored in `MacOS/Photos-Manipulations/models/` (relative to the script). On first run the script downloads the weights there if not present. On subsequent runs — including after copying the folder to a new Mac — the local copy is used with no network access needed.

The `models/` directory is committed to the repo so the weights travel with the script.

## Error Handling

- Unsupported file format → clear message and non-zero exit
- Unsupported scale factor → clear message listing valid values
- Missing input file → clear message and non-zero exit
- Model download failure → propagated error from Real-ESRGAN library

## Out of Scope

- GUI
- Batch processing
- Non-JPEG output formats
- Scale factors other than 2x and 4x
