---
type: regex
target:
  source: file
  path: ranges.py
pattern: '^(?![\s\S]*(if |==|\(1, 5\)))[\s\S]*return end - start \+ 1\s*$'
---
