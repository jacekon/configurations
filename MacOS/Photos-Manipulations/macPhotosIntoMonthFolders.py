#!/usr/bin/env python3

"""
iPhone Photos / Videos organizer

Moves media files into:

    YYYY/MM/

based primarily on the original capture date stored in metadata.

Processing order:

1. Identify Live Photo HEIC + MOV pairs.
   - The HEIC's capture date is used for both files.
   - The pair is moved together before parallel processing starts.

2. Process all remaining media files in parallel.
   - Capture date from metadata is preferred.
   - Filesystem creation date is used as fallback.

Supported:
    HEIC, HEIF
    JPG, JPEG
    PNG
    TIF, TIFF
    MOV
    MP4
    M4V

Non-media files are left untouched.

Destination directories are created automatically.

Existing files are never overwritten.

Usage:

    python3 organize_media.py "/path/to/export"

Optional:

    python3 organize_media.py "/path/to/export" --workers 8
    python3 organize_media.py "/path/to/export" --dry-run

Requirements:

    brew install exiftool
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


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

DEFAULT_WORKERS = 8

MEDIA_EXTENSIONS = {
    ".heic",
    ".heif",
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
    ".mov",
    ".mp4",
    ".m4v",
}


# ------------------------------------------------------------
# ExifTool
# ------------------------------------------------------------

def read_metadata(files: list[Path]) -> dict[str, dict]:
    """
    Read metadata for all files in one ExifTool invocation.

    This is considerably faster than starting ExifTool once
    for every file.
    """

    if not files:
        return {}

    cmd = [
        "exiftool",

        # JSON output
        "-j",

        # Don't extract huge binary data.
        "-fast",

        # Useful Apple/QuickTime metadata.
        "-DateTimeOriginal",
        "-CreateDate",
        "-MediaCreateDate",
        "-TrackCreateDate",

        # Live Photo identification.
        "-ContentIdentifier",
        "-MediaGroupUUID",
        "-ContentIdentifier",

        # Process all supplied files.
        *[str(p) for p in files],
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

    except FileNotFoundError:
        raise RuntimeError(
            "ExifTool was not found.\n"
            "Install it with:\n"
            "    brew install exiftool"
        )

    if result.returncode != 0:
        raise RuntimeError(
            "ExifTool failed:\n" + result.stderr
        )

    try:
        records = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Could not parse ExifTool output: {exc}"
        )

    metadata = {}

    for record in records:

        source_file = record.get("SourceFile")

        if not source_file:
            continue

        metadata[str(Path(source_file).resolve())] = record

    return metadata


# ------------------------------------------------------------
# Date handling
# ------------------------------------------------------------

DATE_TAGS = (
    "DateTimeOriginal",
    "CreateDate",
    "MediaCreateDate",
    "TrackCreateDate",
)


def parse_exif_date(value: str | None) -> datetime | None:
    """
    Parse common ExifTool date formats.

    Examples:

        2024:08:31 15:42:10
        2024:08:31 15:42:10+02:00
        2024:08:31 15:42:10Z

    We only need year/month, so timezone information does not
    affect the resulting folder unless the timestamp is actually
    crossing a month boundary. For iPhone metadata, the stored
    local capture date is preferred.
    """

    if not value:
        return None

    value = str(value).strip()

    # Standard EXIF datetime is first 19 characters.
    value = value[:19]

    try:
        return datetime.strptime(
            value,
            "%Y:%m:%d %H:%M:%S",
        )
    except ValueError:
        return None


def metadata_date(record: dict) -> datetime | None:
    """
    Return the first useful embedded media date.
    """

    for tag in DATE_TAGS:

        value = record.get(tag)

        date = parse_exif_date(value)

        if date is not None:
            return date

    return None


def filesystem_creation_date(path: Path) -> datetime | None:
    """
    macOS filesystem creation/birth date.

    This is used only as a fallback when media metadata
    doesn't contain a usable date.
    """

    try:
        result = subprocess.run(
            [
                "stat",
                "-f",
                "%B",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        timestamp = int(result.stdout.strip())

        return datetime.fromtimestamp(timestamp)

    except (
        subprocess.SubprocessError,
        ValueError,
        OSError,
    ):
        return None


# ------------------------------------------------------------
# Live Photo identification
# ------------------------------------------------------------

def live_photo_identifier(record: dict) -> str | None:
    """
    Return Apple's Live Photo content identifier when available.

    For a Live Photo, the HEIC and MOV normally share the same
    ContentIdentifier.

    We deliberately require an actual identifier rather than
    guessing solely from filenames.
    """

    value = record.get("ContentIdentifier")

    if value:
        return str(value)

    return None


def identify_live_photo_pairs(
    files: list[Path],
    metadata: dict[str, dict],
) -> tuple[list[tuple[Path, Path, datetime | None]], set[Path]]:
    """
    Find Live Photo HEIC + MOV pairs.

    Returns:

        pairs:
            [(heic, mov, date), ...]

        paired_files:
            set of files already belonging to a Live Photo
    """

    by_identifier: dict[str, list[Path]] = {}

    for path in files:

        record = metadata.get(
            str(path.resolve()),
            {},
        )

        identifier = live_photo_identifier(record)

        if not identifier:
            continue

        by_identifier.setdefault(
            identifier,
            [],
        ).append(path)

    pairs = []
    paired_files: set[Path] = set()

    for identifier, group in by_identifier.items():

        heics = [
            p for p in group
            if p.suffix.lower() in {".heic", ".heif"}
        ]

        movs = [
            p for p in group
            if p.suffix.lower() == ".mov"
        ]

        if not heics or not movs:
            continue

        # Normally exactly one HEIC + one MOV.
        # If there are multiple files with the same identifier,
        # don't make assumptions.
        if len(heics) != 1 or len(movs) != 1:
            print(
                "[WARN] Ambiguous Live Photo group; "
                f"leaving unpaired: {identifier}"
            )
            continue

        heic = heics[0]
        mov = movs[0]

        record = metadata.get(
            str(heic.resolve()),
            {},
        )

        date = metadata_date(record)

        pairs.append(
            (heic, mov, date)
        )

        paired_files.add(heic)
        paired_files.add(mov)

    return pairs, paired_files


# ------------------------------------------------------------
# Destination handling
# ------------------------------------------------------------

def destination_directory(
    source: Path,
    date: datetime,
) -> Path:

    return (
        source
        / f"{date.year:04d}"
        / f"{date.month:02d}"
    )


def ensure_directory(path: Path) -> bool:
    """
    Create directory safely.

    Multiple workers may attempt the same directory.

    exist_ok=True means that if another worker has already
    created it, that is considered success.
    """

    try:
        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return True

    except OSError as exc:

        print(
            f"[ERROR] Cannot create directory "
            f"{path}: {exc}",
            file=sys.stderr,
        )

        return False


def unique_destination(path: Path) -> Path:
    """
    Never overwrite an existing file.

    IMG_1234.HEIC
    IMG_1234_1.HEIC
    IMG_1234_2.HEIC
    """

    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix

    counter = 1

    while True:

        candidate = path.with_name(
            f"{stem}_{counter}{suffix}"
        )

        if not candidate.exists():
            return candidate

        counter += 1


# ------------------------------------------------------------
# Moving
# ------------------------------------------------------------

def move_file(
    path: Path,
    destination_dir: Path,
    dry_run: bool,
) -> str:

    if not path.exists():
        return (
            f"[SKIP] File disappeared: "
            f"{path.name}"
        )

    if not ensure_directory(destination_dir):

        return (
            f"[ERROR] Could not create "
            f"{destination_dir}"
        )

    destination = unique_destination(
        destination_dir / path.name
    )

    if dry_run:

        return (
            f"[DRY] {path.name} -> "
            f"{destination.parent.name}/"
            f"{destination.name}"
        )

    try:

        shutil.move(
            str(path),
            str(destination),
        )

        return (
            f"[MOVE] {path.name} -> "
            f"{destination.parent.parent.name}/"
            f"{destination.parent.name}/"
            f"{destination.name}"
        )

    except FileNotFoundError:

        return (
            f"[SKIP] File disappeared: "
            f"{path.name}"
        )

    except OSError as exc:

        return (
            f"[ERROR] Failed moving "
            f"{path.name}: {exc}"
        )


def move_live_photo_pair(
    heic: Path,
    mov: Path,
    date: datetime,
    source: Path,
    dry_run: bool,
) -> list[str]:
    """
    Move both parts of a Live Photo.

    The HEIC capture date determines the destination
    for both files.
    """

    destination = destination_directory(
        source,
        date,
    )

    results = []

    results.append(
        move_file(
            heic,
            destination,
            dry_run,
        )
    )

    results.append(
        move_file(
            mov,
            destination,
            dry_run,
        )
    )

    return results


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Organize iPhone media into YYYY/MM folders."
        )
    )

    parser.add_argument(
        "source",
        type=Path,
        help="Source folder",
    )

    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=(
            "Number of parallel workers "
            f"(default: {DEFAULT_WORKERS})"
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Show what would happen without "
            "moving any files."
        ),
    )

    args = parser.parse_args()

    source = args.source.expanduser().resolve()

    if not source.is_dir():

        print(
            f"Error: not a directory: {source}",
            file=sys.stderr,
        )

        return 1

    if args.workers < 1:

        print(
            "Error: workers must be >= 1",
            file=sys.stderr,
        )

        return 1

    # Check ExifTool.
    try:

        subprocess.run(
            ["exiftool", "-ver"],
            capture_output=True,
            text=True,
            check=True,
        )

    except FileNotFoundError:

        print(
            "ExifTool is not installed.\n\n"
            "Install it with:\n"
            "    brew install exiftool",
            file=sys.stderr,
        )

        return 1

    # --------------------------------------------------------
    # Scan
    # --------------------------------------------------------

    files = [
        p
        for p in source.iterdir()
        if p.is_file()
        and p.suffix.lower() in MEDIA_EXTENSIONS
    ]

    print(f"Source:  {source}")
    print(f"Media:   {len(files)}")
    print(f"Workers: {args.workers}")

    if args.dry_run:
        print("Mode:    DRY RUN")

    print()

    if not files:

        print("No supported media files found.")

        return 0

    # --------------------------------------------------------
    # Read metadata ONCE for everything.
    # --------------------------------------------------------

    print("Reading media metadata...")

    try:

        metadata = read_metadata(files)

    except RuntimeError as exc:

        print(
            f"Error: {exc}",
            file=sys.stderr,
        )

        return 1

    # --------------------------------------------------------
    # Phase 1: Live Photos
    # --------------------------------------------------------

    print("Identifying Live Photos...")

    live_pairs, paired_files = (
        identify_live_photo_pairs(
            files,
            metadata,
        )
    )

    print(
        f"Live Photo pairs: {len(live_pairs)}"
    )

    # Move Live Photos BEFORE parallel processing.
    #
    # This ensures that a HEIC and its MOV can never be
    # independently processed by two workers.
    for heic, mov, date in live_pairs:

        if date is None:

            # Fall back to HEIC filesystem creation date.
            date = filesystem_creation_date(heic)

        if date is None:

            print(
                f"[SKIP] Live Photo has no date: "
                f"{heic.name} + {mov.name}"
            )

            continue

        results = move_live_photo_pair(
            heic,
            mov,
            date,
            source,
            args.dry_run,
        )

        for result in results:
            print(result)

    # --------------------------------------------------------
    # Phase 2: remaining files
    # --------------------------------------------------------

    remaining = [
        p
        for p in files
        if p not in paired_files
        and p.exists()
    ]

    print()
    print(
        f"Remaining files for parallel processing: "
        f"{len(remaining)}"
    )

    # --------------------------------------------------------
    # Prepare jobs.
    #
    # Metadata has already been read, so workers don't need
    # to call ExifTool.
    # --------------------------------------------------------

    jobs = []

    for path in remaining:

        record = metadata.get(
            str(path.resolve()),
            {},
        )

        date = metadata_date(record)

        if date is None:

            date = filesystem_creation_date(path)

        if date is None:

            print(
                f"[SKIP] No usable date: "
                f"{path.name}"
            )

            continue

        destination = destination_directory(
            source,
            date,
        )

        jobs.append(
            (path, destination)
        )

    # --------------------------------------------------------
    # Parallel moves
    # --------------------------------------------------------

    print()
    print(
        f"Moving {len(jobs)} files "
        f"using {args.workers} workers..."
    )

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=args.workers
    ) as executor:

        futures = [
            executor.submit(
                move_file,
                path,
                destination,
                args.dry_run,
            )
            for path, destination in jobs
        ]

        for future in concurrent.futures.as_completed(
            futures
        ):

            try:

                print(
                    future.result()
                )

            except Exception as exc:

                # Never let one worker kill the whole job.
                print(
                    f"[ERROR] Worker failed: {exc}",
                    file=sys.stderr,
                )

    print()
    print("Done.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

