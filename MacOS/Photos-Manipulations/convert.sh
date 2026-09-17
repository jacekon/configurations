for f in *.[Hh][Ee][Ii][Cc]; do
  sips -s format jpeg -s formatOptions 90 "$f" --out "${f%.*}.jpg"
done
