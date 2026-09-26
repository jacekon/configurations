#!/usr/bin/env python3
"""
Organize iPhone photo exports into YYYY/MM/ folders by capture date.

Processing order:
1. Live Photo pairs (HEIC + MOV sharing the same ContentIdentifier) are moved
   together BEFORE parallel processing to prevent the two halves landing in
   different folders.
2. All remaining media files are processed in parallel.

Date priority: EXIF DateTimeOriginal → CreateDate → MediaCreateDate →
               TrackCreateDate → macOS filesystem birth date.

Supported extensions: HEIC, HEIF, JPG, JPEG, PNG, TIF, TIFF, MOV, MP4, M4V.
Non-media files are left untouched. Existing files are never overwritten
(collisions get a _1, _2 … suffix).

Requirements:
    brew install exiftool

Usage:
    python3 organize_by_date.py /path/to/source --output /path/to/dest [--workers 8] [--dry-run]

    --output defaults to a subfolder named "organized" inside the source folder
    if not specified.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


DEFAULT_WORKERS = 8

MEDIA_EXTENSIONS = {
    ".heic", ".heif",
    ".jpg", ".jpeg",
    ".png",
    ".tif", ".tiff",
    ".mov", ".mp4", ".m4v",
}


# ------------------------------------------------------------
# ExifTool
# ------------------------------------------------------------

def read_metadata(files: list[Path]) -> dict[str, dict]:
    """Read metadata for all files in a single ExifTool call (much faster than one call per file)."""

    if not files:
        return {}

    cmd = [
        "exiftool",
        "-j",       # JSON output
        "-fast",    # Skip large binary blocks we don't need
        "-DateTimeOriginal",
        "-CreateDate",
        "-MediaCreateDate",
        "-TrackCreateDate",
        # Live Photo: HEIC and its companion MOV share the same ContentIdentifier
        "-ContentIdentifier",
        "-MediaGroupUUID",
        *[str(p) for p in files],
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        raise RuntimeError("ExifTool was not found.\nInstall it with:\n    brew install exiftool")

    # ExifTool exits non-zero when ANY file has a warning (e.g. empty file, unknown format).
    # That's too strict for a batch run — only hard-fail if there's no usable JSON at all.
    if result.returncode != 0 and result.stderr and not result.stdout.strip():
        raise RuntimeError("ExifTool failed:\n" + result.stderr)

    if result.stderr.strip():
        for line in result.stderr.strip().splitlines():
            print(f"[WARN] exiftool: {line}")

    try:
        records = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not parse ExifTool output: {exc}")

    return {str(Path(r["SourceFile"]).resolve()): r for r in records if r.get("SourceFile")}


# ------------------------------------------------------------
# Date handling
# ------------------------------------------------------------

DATE_TAGS = ("DateTimeOriginal", "CreateDate", "MediaCreateDate", "TrackCreateDate")


def parse_exif_date(value: str | None) -> datetime | None:
    """Parse ExifTool date strings like '2024:08:31 15:42:10' or with timezone suffix."""
    if not value:
        return None
    # Timezone suffix varies; we only need year/month so strip everything after char 19.
    try:
        return datetime.strptime(str(value).strip()[:19], "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def metadata_date(record: dict) -> datetime | None:
    """Return the first parseable capture date found in the EXIF record."""
    for tag in DATE_TAGS:
        date = parse_exif_date(record.get(tag))
        if date is not None:
            return date
    return None


def filesystem_creation_date(path: Path) -> datetime | None:
    """Return macOS filesystem birth date as a fallback when EXIF has no date."""
    try:
        result = subprocess.run(["stat", "-f", "%B", str(path)], capture_output=True, text=True, check=True)
        return datetime.fromtimestamp(int(result.stdout.strip()))
    except (subprocess.SubprocessError, ValueError, OSError):
        return None


# ------------------------------------------------------------
# Live Photo identification
# ------------------------------------------------------------

def live_photo_identifier(record: dict) -> str | None:
    """Return the Apple ContentIdentifier UUID that links a HEIC to its companion MOV."""
    value = record.get("ContentIdentifier")
    return str(value) if value else None


def identify_live_photo_pairs(
    files: list[Path],
    metadata: dict[str, dict],
) -> tuple[list[tuple[Path, Path, datetime | None]], set[Path]]:
    """
    Find Live Photo HEIC+MOV pairs by matching ContentIdentifier.
    Returns the pairs list and the set of files already claimed by a pair.
    """
    by_identifier: dict[str, list[Path]] = {}

    for path in files:
        record = metadata.get(str(path.resolve()), {})
        identifier = live_photo_identifier(record)
        if identifier:
            by_identifier.setdefault(identifier, []).append(path)

    pairs = []
    paired_files: set[Path] = set()

    for identifier, group in by_identifier.items():
        heics = [p for p in group if p.suffix.lower() in {".heic", ".heif"}]
        movs  = [p for p in group if p.suffix.lower() == ".mov"]

        if not heics or not movs:
            continue

        # Multiple files with the same identifier would require guessing — skip safely.
        if len(heics) != 1 or len(movs) != 1:
            print(f"[WARN] Ambiguous Live Photo group; leaving unpaired: {identifier}")
            continue

        heic, mov = heics[0], movs[0]
        record = metadata.get(str(heic.resolve()), {})
        pairs.append((heic, mov, metadata_date(record)))
        paired_files.update([heic, mov])

    return pairs, paired_files


# ------------------------------------------------------------
# Destination / collision handling
# ------------------------------------------------------------

def destination_directory(output: Path, date: datetime) -> Path:
    return output / f"{date.year:04d}" / f"{date.month:02d}"


def ensure_directory(path: Path) -> bool:
    """Create directory, tolerating races from parallel workers."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as exc:
        print(f"[ERROR] Cannot create directory {path}: {exc}", file=sys.stderr)
        return False


def unique_destination(path: Path) -> Path:
    """Append _1, _2 … to avoid overwriting an existing file."""
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    for counter in range(1, 10_000):
        candidate = path.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Too many collisions for {path.name}")


# ------------------------------------------------------------
# Moving
# ------------------------------------------------------------

def move_file(path: Path, destination_dir: Path, dry_run: bool) -> str:
    if not path.exists():
        return f"[SKIP] File disappeared: {path.name}"

    destination = unique_destination(destination_dir / path.name)

    if dry_run:
        # Show the full relative path so it's clear where the file would land.
        return f"[DRY]  {path.name} -> {destination_dir.parent.name}/{destination_dir.name}/{destination.name}"

    if not ensure_directory(destination_dir):
        return f"[ERROR] Could not create {destination_dir}"

    try:
        shutil.move(str(path), str(destination))
        return f"[MOVE] {path.name} -> {destination_dir.parent.name}/{destination_dir.name}/{destination.name}"
    except FileNotFoundError:
        return f"[SKIP] File disappeared: {path.name}"
    except OSError as exc:
        return f"[ERROR] Failed moving {path.name}: {exc}"


def move_live_photo_pair(heic: Path, mov: Path, date: datetime, output: Path, dry_run: bool) -> list[str]:
    """Move both halves of a Live Photo to the same destination folder."""
    destination = destination_directory(output, date)
    return [move_file(heic, destination, dry_run), move_file(mov, destination, dry_run)]


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Organize iPhone media into YYYY/MM folders.")
    parser.add_argument("source", type=Path, help="Folder containing media files to organize")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="Root folder for YYYY/MM output (default: <source>/organized)")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"Parallel workers (default: {DEFAULT_WORKERS})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without moving any files.")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    output = (args.output.expanduser().resolve() if args.output
              else source / "organized")

    if not source.is_dir():
        print(f"Error: not a directory: {source}", file=sys.stderr)
        return 1
    if args.workers < 1:
        print("Error: workers must be >= 1", file=sys.stderr)
        return 1

    try:
        subprocess.run(["exiftool", "-ver"], capture_output=True, text=True, check=True)
    except FileNotFoundError:
        print("ExifTool is not installed.\n\nInstall it with:\n    brew install exiftool", file=sys.stderr)
        return 1

    files = [p for p in source.iterdir() if p.is_file() and p.suffix.lower() in MEDIA_EXTENSIONS]

    print(f"Source:  {source}")
    print(f"Output:  {output}")
    print(f"Media:   {len(files)}")
    print(f"Workers: {args.workers}")
    if args.dry_run:
        print("Mode:    DRY RUN (nothing will be moved or created)")
    print()

    if not files:
        print("No supported media files found.")
        return 0

    print("Reading media metadata...")
    try:
        metadata = read_metadata(files)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Phase 1: Live Photos — move pairs serially before parallel processing
    # so a HEIC and its MOV can never be dispatched to two different workers.
    print("Identifying Live Photos...")
    live_pairs, paired_files = identify_live_photo_pairs(files, metadata)
    print(f"Live Photo pairs: {len(live_pairs)}")

    for heic, mov, date in live_pairs:
        if date is None:
            date = filesystem_creation_date(heic)
        if date is None:
            print(f"[SKIP] Live Photo has no date: {heic.name} + {mov.name}")
            continue
        for result in move_live_photo_pair(heic, mov, date, output, args.dry_run):
            print(result)

    # Phase 2: everything else in parallel
    remaining = [p for p in files if p not in paired_files and p.exists()]
    print(f"\nRemaining files for parallel processing: {len(remaining)}")

    jobs = []
    for path in remaining:
        record = metadata.get(str(path.resolve()), {})
        date = metadata_date(record) or filesystem_creation_date(path)
        if date is None:
            print(f"[SKIP] No usable date: {path.name}")
            continue
        jobs.append((path, destination_directory(output, date)))

    print(f"\nMoving {len(jobs)} files using {args.workers} workers...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(move_file, path, dest, args.dry_run) for path, dest in jobs]
        for future in concurrent.futures.as_completed(futures):
            try:
                print(future.result())
            except Exception as exc:
                print(f"[ERROR] Worker failed: {exc}", file=sys.stderr)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
