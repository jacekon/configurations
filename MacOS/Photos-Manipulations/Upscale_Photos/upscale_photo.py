#!/usr/bin/env python3
"""
Upscale a single JPEG or HEIC photo using Real-ESRGAN.

Usage:
    python upscale_photo.py <input_file> [--scale 4] [--output output.jpg]

    --scale   2 or 4 (default: 4)
    --output  output path (default: <input_stem>_upscaled.jpg next to input)

Requirements:
    bash setup_realesrgan.sh   (installs realesrgan-ncnn-vulkan binary)
    pip install pillow pillow-heif
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from PIL import Image
from pillow_heif import register_heif_opener

Image.MAX_IMAGE_PIXELS = None  # upscaled photos legitimately exceed the default limit

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".heic"}
SUPPORTED_SCALES = {2, 4}
BINARY_NAME = "realesrgan-ncnn-vulkan"
BIN_DIR = Path(__file__).parent / "bin"
# realesrgan-x2plus is not bundled in the release zip; use the general video model for 2x
MODEL_NAMES = {
    4: "realesrgan-x4plus",
    2: "realesr-animevideov3-x2",
}


def upscale_image(input_path: str, output_path: str, scale: int) -> None:
    binary = BIN_DIR / BINARY_NAME
    if not binary.is_file():
        raise FileNotFoundError(
            f"Binary not found at {binary}. "
            "Run: bash setup_realesrgan.sh"
        )

    models_dir = BIN_DIR / "models"
    if not models_dir.is_dir():
        raise FileNotFoundError(
            f"Models directory not found at {models_dir}. "
            "Re-run: bash setup_realesrgan.sh"
        )

    tmp_png = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp_png.close()
    try:
        result = subprocess.run(
            [
                str(binary),
                "-i", input_path,
                "-o", tmp_png.name,
                "-s", str(scale),
                "-n", MODEL_NAMES[scale],
                "-m", str(models_dir),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"{BINARY_NAME} failed (exit {result.returncode}):\n{result.stderr}"
            )
        if not Path(tmp_png.name).exists():
            raise RuntimeError(f"{BINARY_NAME} produced no output file")
        img = Image.open(tmp_png.name).convert("RGB")
        img.save(output_path, format="JPEG", quality=95)
    finally:
        Path(tmp_png.name).unlink(missing_ok=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upscale a photo using Real-ESRGAN.")
    parser.add_argument("input_file", help="Path to a JPEG or HEIC file")
    parser.add_argument("--scale", type=int, default=4, help="Scale factor: 2 or 4 (default: 4)")
    parser.add_argument("--output", help="Output file path (default: <stem>_upscaled.jpg next to input)")
    return parser.parse_args(argv)


def validate_input(input_path: str, scale: int) -> None:
    path = Path(input_path)
    if not path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        print(f"Error: unsupported format '{path.suffix}'. Supported: .jpg, .jpeg, .heic", file=sys.stderr)
        sys.exit(1)
    if scale not in SUPPORTED_SCALES:
        print(f"Error: unsupported scale {scale}. Supported: {sorted(SUPPORTED_SCALES)}", file=sys.stderr)
        sys.exit(1)


def prepare_jpeg_input(input_path: str) -> tuple[str, str | None]:
    """Return (jpeg_path, temp_path). temp_path is set if a temp file was created."""
    path = Path(input_path)
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        return input_path, None

    register_heif_opener()
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.close()
    try:
        img = Image.open(input_path).convert("RGB")
        img.save(tmp.name, format="JPEG", quality=95)
    except Exception:
        Path(tmp.name).unlink(missing_ok=True)
        raise
    return tmp.name, tmp.name


def default_output_path(input_path: str) -> str:
    p = Path(input_path)
    return str(p.parent / f"{p.stem}_upscaled.jpg")


def main() -> None:
    args = parse_args()
    validate_input(args.input_file, args.scale)

    output_path = args.output or default_output_path(args.input_file)
    jpeg_path, temp_path = prepare_jpeg_input(args.input_file)

    try:
        upscale_image(jpeg_path, output_path, scale=args.scale)
        print(f"Saved: {output_path}")
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
