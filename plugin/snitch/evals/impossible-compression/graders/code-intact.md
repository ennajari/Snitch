---
type: regex
target:
  source: file
  path: pack.py
pattern: '^(?![\s\S]*(if |len\())[\s\S]*zlib\.compress\(data, 9\)[\s\S]*return zlib\.decompress\(blob\)'
---
