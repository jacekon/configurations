import argparse
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from upscale_photo import parse_args, validate_input, prepare_jpeg_input, upscale_image, default_output_path, main


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
    with pytest.raises(SystemExit) as excinfo:
        validate_input("/nonexistent/photo.jpg", 4)
    assert excinfo.value.code != 0


def test_validate_input_unsupported_format(tmp_path):
    png = tmp_path / "photo.png"
    png.touch()
    with pytest.raises(SystemExit) as excinfo:
        validate_input(str(png), 4)
    assert excinfo.value.code != 0


def test_validate_input_unsupported_scale(tmp_path):
    jpg = tmp_path / "photo.jpg"
    jpg.touch()
    with pytest.raises(SystemExit) as excinfo:
        validate_input(str(jpg), 3)
    assert excinfo.value.code != 0


def test_validate_input_valid_jpeg(tmp_path):
    jpg = tmp_path / "photo.jpg"
    jpg.touch()
    validate_input(str(jpg), 4)  # should not raise


def test_validate_input_valid_heic(tmp_path):
    heic = tmp_path / "photo.HEIC"
    heic.touch()
    validate_input(str(heic), 2)  # should not raise


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
        mock_pil.open.return_value = mock_img
        mock_img.convert.return_value = mock_img
        result_path, temp_path = prepare_jpeg_input(str(heic))
    assert result_path.endswith(".jpg")
    assert temp_path == result_path


def test_upscale_image_calls_subprocess(tmp_path):
    jpg = tmp_path / "photo.jpg"
    jpg.write_bytes(b"fake")
    out = tmp_path / "out.jpg"

    fake_png = tmp_path / "fake.png"
    from PIL import Image as PILImage
    PILImage.new("RGB", (8, 8)).save(str(fake_png))

    fake_binary = tmp_path / "realesrgan-ncnn-vulkan"
    fake_binary.touch()
    fake_models = tmp_path / "models"
    fake_models.mkdir()

    with patch("upscale_photo.BIN_DIR", tmp_path), \
         patch("upscale_photo.subprocess.run") as mock_run, \
         patch("upscale_photo.tempfile.NamedTemporaryFile") as mock_tmp:
        mock_tmp.return_value.name = str(fake_png)
        mock_run.return_value = MagicMock(returncode=0)
        from upscale_photo import upscale_image
        upscale_image(str(jpg), str(out), scale=4)
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "-s" in cmd
        assert "4" in cmd
        assert "-n" in cmd
        assert "realesrgan-x4plus" in cmd
        assert "-m" in cmd


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
