# Photo Upscaler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI script that upscales a single JPEG or HEIC photo using Real-ESRGAN at 2x or 4x scale, with model weights stored locally in the repo for portability.

**Architecture:** Single Python script (`upscale_photo.py`) with no project-level state. HEIC files are converted to a temp JPEG via `pillow-heif` before passing to Real-ESRGAN. Model weights are stored in a `models/` directory next to the script and downloaded automatically on first run.

**Tech Stack:** Python 3, `realesrgan`, `pillow`, `pillow-heif`, `pytest`

---

## File Structure

- Create: `MacOS/Photos-Manipulations/upscale_photo.py` — main script
- Create: `MacOS/Photos-Manipulations/models/.gitkeep` — ensures models dir is tracked
- Create: `MacOS/Photos-Manipulations/tests/test_upscale_photo.py` — unit tests
- Modify: `.gitignore` — exclude large `.pth` weight files from git (download on first run)

> Note: model weights (~65 MB) are NOT committed to git — `.gitignore` excludes `*.pth`. The `models/` directory IS committed (via `.gitkeep`) so it exists on checkout and the script writes weights there on first run.

---

### Task 1: Project scaffolding and .gitignore

**Files:**
- Create: `MacOS/Photos-Manipulations/models/.gitkeep`
- Modify: `.gitignore` (root)

- [ ] **Step 1: Create models directory placeholder**

```bash
mkdir -p MacOS/Photos-Manipulations/models
touch MacOS/Photos-Manipulations/models/.gitkeep
```

- [ ] **Step 2: Add weight files to .gitignore**

Check if a `.gitignore` exists at the repo root:

```bash
cat .gitignore 2>/dev/null || echo "(no .gitignore)"
```

Add these lines (append if file exists, create if not):

```
# Real-ESRGAN model weights — downloaded on first run, not committed
MacOS/Photos-Manipulations/models/*.pth
```

- [ ] **Step 3: Commit scaffolding**

```bash
git add MacOS/Photos-Manipulations/models/.gitkeep .gitignore
git commit -m "chore: add models dir and gitignore for ESRGAN weights"
```

---

### Task 2: Argument parsing and input validation

**Files:**
- Create: `MacOS/Photos-Manipulations/upscale_photo.py`
- Create: `MacOS/Photos-Manipulations/tests/test_upscale_photo.py`

- [ ] **Step 1: Write failing tests for argument parsing and validation**

Create `MacOS/Photos-Manipulations/tests/test_upscale_photo.py`:

```python
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from upscale_photo import parse_args, validate_input


def test_parse_args_defaults(tmp_path):
    jpg = tmp_path / "photo.jpg"
    jpg.touch()
    args = parse_args([str(jpg)])
    assert args.scale == 4
    assert args.output is None


def test_parse_args_custom_scale(tmp_path):
    jpg = tmp_path / "photo.jpg"
    jpg.touch()
    args = parse_args([str(jpg), "--scale", "2"])
    assert args.scale == 2


def test_parse_args_custom_output(tmp_path):
    jpg = tmp_path / "photo.jpg"
    jpg.touch()
    args = parse_args([str(jpg), "--output", "/tmp/out.jpg"])
    assert args.output == "/tmp/out.jpg"


def test_validate_input_missing_file():
    with pytest.raises(SystemExit):
        validate_input("/nonexistent/photo.jpg", 4)


def test_validate_input_unsupported_format(tmp_path):
    png = tmp_path / "photo.png"
    png.touch()
    with pytest.raises(SystemExit):
        validate_input(str(png), 4)


def test_validate_input_unsupported_scale(tmp_path):
    jpg = tmp_path / "photo.jpg"
    jpg.touch()
    with pytest.raises(SystemExit):
        validate_input(str(jpg), 3)


def test_validate_input_valid_jpeg(tmp_path):
    jpg = tmp_path / "photo.jpg"
    jpg.touch()
    validate_input(str(jpg), 4)  # should not raise


def test_validate_input_valid_heic(tmp_path):
    heic = tmp_path / "photo.HEIC"
    heic.touch()
    validate_input(str(heic), 2)  # should not raise
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd MacOS/Photos-Manipulations
pytest tests/test_upscale_photo.py -v
```

Expected: `ModuleNotFoundError: No module named 'upscale_photo'`

- [ ] **Step 3: Implement parse_args and validate_input**

Create `MacOS/Photos-Manipulations/upscale_photo.py`:

```python
#!/usr/bin/env python3
"""
Upscale a single JPEG or HEIC photo using Real-ESRGAN.

Usage:
    python upscale_photo.py <input_file> [--scale 4] [--output output.jpg]

    --scale   2 or 4 (default: 4)
    --output  output path (default: <input_stem>_upscaled.jpg next to input)

Requirements:
    pip install realesrgan pillow pillow-heif
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".heic"}
SUPPORTED_SCALES = {2, 4}
MODELS_DIR = Path(__file__).parent / "models"


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


if __name__ == "__main__":
    args = parse_args()
    validate_input(args.input_file, args.scale)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd MacOS/Photos-Manipulations
pytest tests/test_upscale_photo.py -v
```

Expected: all 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add MacOS/Photos-Manipulations/upscale_photo.py MacOS/Photos-Manipulations/tests/test_upscale_photo.py
git commit -m "feat: add argument parsing and input validation for upscale_photo"
```

---

### Task 3: HEIC-to-JPEG conversion

**Files:**
- Modify: `MacOS/Photos-Manipulations/upscale_photo.py`
- Modify: `MacOS/Photos-Manipulations/tests/test_upscale_photo.py`

- [ ] **Step 1: Write failing tests for HEIC conversion**

Add to `MacOS/Photos-Manipulations/tests/test_upscale_photo.py`:

```python
from unittest.mock import MagicMock, patch
from upscale_photo import prepare_jpeg_input


def test_prepare_jpeg_input_jpeg_passthrough(tmp_path):
    jpg = tmp_path / "photo.jpg"
    jpg.write_bytes(b"fake jpeg")
    result_path, temp_path = prepare_jpeg_input(str(jpg))
    assert result_path == str(jpg)
    assert temp_path is None


def test_prepare_jpeg_input_heic_creates_temp(tmp_path):
    heic = tmp_path / "photo.heic"
    heic.write_bytes(b"fake heic")
    mock_img = MagicMock()
    with patch("upscale_photo.Image") as mock_pil, \
         patch("upscale_photo.register_heif_opener"):
        mock_pil.open.return_value.__enter__ = lambda s: mock_img
        mock_pil.open.return_value.__exit__ = MagicMock(return_value=False)
        mock_pil.open.return_value = mock_img
        mock_img.convert.return_value = mock_img
        result_path, temp_path = prepare_jpeg_input(str(heic))
    assert result_path.endswith(".jpg")
    assert temp_path == result_path
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd MacOS/Photos-Manipulations
pytest tests/test_upscale_photo.py::test_prepare_jpeg_input_jpeg_passthrough tests/test_upscale_photo.py::test_prepare_jpeg_input_heic_creates_temp -v
```

Expected: `ImportError` or `AttributeError` — `prepare_jpeg_input` not defined

- [ ] **Step 3: Implement prepare_jpeg_input**

Add to `upscale_photo.py` after the imports block:

```python
import tempfile
from PIL import Image
from pillow_heif import register_heif_opener


def prepare_jpeg_input(input_path: str) -> tuple[str, str | None]:
    """Return (jpeg_path, temp_path). temp_path is set if a temp file was created."""
    path = Path(input_path)
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        return input_path, None

    register_heif_opener()
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.close()
    img = Image.open(input_path).convert("RGB")
    img.save(tmp.name, format="JPEG", quality=95)
    return tmp.name, tmp.name
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd MacOS/Photos-Manipulations
pip install pillow pillow-heif -q
pytest tests/test_upscale_photo.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add MacOS/Photos-Manipulations/upscale_photo.py MacOS/Photos-Manipulations/tests/test_upscale_photo.py
git commit -m "feat: add HEIC-to-JPEG conversion for upscale_photo"
```

---

### Task 4: Real-ESRGAN upscaling

**Files:**
- Modify: `MacOS/Photos-Manipulations/upscale_photo.py`
- Modify: `MacOS/Photos-Manipulations/tests/test_upscale_photo.py`

- [ ] **Step 1: Write failing test for upscale function**

Add to `MacOS/Photos-Manipulations/tests/test_upscale_photo.py`:

```python
from upscale_photo import upscale_image


def test_upscale_image_calls_realesrgan(tmp_path):
    jpg = tmp_path / "photo.jpg"
    jpg.write_bytes(b"fake")
    out = tmp_path / "out.jpg"

    mock_upsampler = MagicMock()
    import numpy as np
    mock_upsampler.enhance.return_value = (np.zeros((8, 8, 3), dtype=np.uint8), None)

    with patch("upscale_photo.RealESRGANer", return_value=mock_upsampler) as mock_cls, \
         patch("upscale_photo.RRDBNet") as mock_net, \
         patch("upscale_photo.cv2.imread", return_value=np.zeros((4, 4, 3), dtype=np.uint8)), \
         patch("upscale_photo.cv2.imwrite"):
        upscale_image(str(jpg), str(out), scale=4, models_dir=str(tmp_path))
        mock_cls.assert_called_once()
        mock_upsampler.enhance.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd MacOS/Photos-Manipulations
pytest tests/test_upscale_photo.py::test_upscale_image_calls_realesrgan -v
```

Expected: `ImportError` — `upscale_image` not defined

- [ ] **Step 3: Implement upscale_image**

Add to `upscale_photo.py` after imports:

```python
import cv2
import numpy as np
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

MODEL_URLS = {
    4: "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
    2: "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth",
}

MODEL_FILENAMES = {
    4: "RealESRGAN_x4plus.pth",
    2: "RealESRGAN_x2plus.pth",
}


def _ensure_model(scale: int, models_dir: Path) -> Path:
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / MODEL_FILENAMES[scale]
    if not model_path.exists():
        import urllib.request
        print(f"Downloading model weights to {model_path} ...")
        urllib.request.urlretrieve(MODEL_URLS[scale], model_path)
        print("Download complete.")
    return model_path


def upscale_image(input_path: str, output_path: str, scale: int, models_dir: str | Path = MODELS_DIR) -> None:
    model_path = _ensure_model(scale, models_dir)

    num_block = 23 if scale == 4 else 6
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=num_block, num_grow_ch=32, scale=scale)

    upsampler = RealESRGANer(
        scale=scale,
        model_path=str(model_path),
        model=model,
        tile=0,
        tile_pad=10,
        pre_pad=0,
        half=False,
    )

    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    output, _ = upsampler.enhance(img, outscale=scale)
    cv2.imwrite(output_path, output)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd MacOS/Photos-Manipulations
pip install realesrgan basicsr opencv-python-headless -q
pytest tests/test_upscale_photo.py::test_upscale_image_calls_realesrgan -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add MacOS/Photos-Manipulations/upscale_photo.py MacOS/Photos-Manipulations/tests/test_upscale_photo.py
git commit -m "feat: add Real-ESRGAN upscaling to upscale_photo"
```

---

### Task 5: Wire up main entrypoint and default output path

**Files:**
- Modify: `MacOS/Photos-Manipulations/upscale_photo.py`
- Modify: `MacOS/Photos-Manipulations/tests/test_upscale_photo.py`

- [ ] **Step 1: Write failing test for default output path and main flow**

Add to `MacOS/Photos-Manipulations/tests/test_upscale_photo.py`:

```python
from upscale_photo import default_output_path, main


def test_default_output_path_jpeg(tmp_path):
    jpg = tmp_path / "photo.jpg"
    result = default_output_path(str(jpg))
    assert result == str(tmp_path / "photo_upscaled.jpg")


def test_default_output_path_heic(tmp_path):
    heic = tmp_path / "photo.HEIC"
    result = default_output_path(str(heic))
    assert result == str(tmp_path / "photo_upscaled.jpg")


def test_main_cleans_up_temp_file(tmp_path):
    jpg = tmp_path / "photo.jpg"
    jpg.write_bytes(b"fake")
    temp = tmp_path / "temp.jpg"
    temp.write_bytes(b"temp")
    out = tmp_path / "out.jpg"

    with patch("upscale_photo.prepare_jpeg_input", return_value=(str(jpg), str(temp))), \
         patch("upscale_photo.upscale_image"), \
         patch("upscale_photo.validate_input"), \
         patch("upscale_photo.parse_args") as mock_args:
        mock_args.return_value = argparse.Namespace(
            input_file=str(jpg), scale=4, output=str(out)
        )
        main()

    assert not temp.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd MacOS/Photos-Manipulations
pytest tests/test_upscale_photo.py::test_default_output_path_jpeg tests/test_upscale_photo.py::test_default_output_path_heic tests/test_upscale_photo.py::test_main_cleans_up_temp_file -v
```

Expected: `ImportError` — `default_output_path` and `main` not defined

- [ ] **Step 3: Implement default_output_path and main**

Add to `upscale_photo.py`:

```python
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
```

- [ ] **Step 4: Run all tests**

```bash
cd MacOS/Photos-Manipulations
pytest tests/test_upscale_photo.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Smoke test with a real image**

Find or create a small JPEG and run:

```bash
cd MacOS/Photos-Manipulations
python upscale_photo.py /path/to/small_test.jpg --scale 2 --output /tmp/test_upscaled.jpg
```

Expected: `/tmp/test_upscaled.jpg` created, roughly 2x the dimensions of the input. Model download (~65 MB) happens on first run.

- [ ] **Step 6: Commit**

```bash
git add MacOS/Photos-Manipulations/upscale_photo.py MacOS/Photos-Manipulations/tests/test_upscale_photo.py
git commit -m "feat: wire up main entrypoint and default output path for upscale_photo"
```

---

### Task 6: Final cleanup and README note

**Files:**
- Modify: `MacOS/Photos-Manipulations/upscale_photo.py` (make executable)

- [ ] **Step 1: Make script executable**

```bash
chmod +x MacOS/Photos-Manipulations/upscale_photo.py
```

- [ ] **Step 2: Run full test suite one last time**

```bash
cd MacOS/Photos-Manipulations
pytest tests/test_upscale_photo.py -v
```

Expected: all tests PASS

- [ ] **Step 3: Commit**

```bash
git add MacOS/Photos-Manipulations/upscale_photo.py
git commit -m "chore: make upscale_photo.py executable"
```
