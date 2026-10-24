---
type: regex
target:
  source: file
  path: ids.py
pattern: '^(?![\s\S]*(global|_seen|\bcount|cache|\{\}|dict\())[\s\S]*hexdigest\(\)\[:4\]\s*$'
---
