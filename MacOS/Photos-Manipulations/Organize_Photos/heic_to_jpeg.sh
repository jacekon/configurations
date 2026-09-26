# Convert all HEIC files in the current directory to JPEG at 90% quality.
# Uses macOS built-in `sips` — no extra tools needed.
# Run from the folder containing the HEIC files.
for f in *.[Hh][Ee][Ii][Cc]; do
  sips -s format jpeg -s formatOptions 90 "$f" --out "${f%.*}.jpg"
done
