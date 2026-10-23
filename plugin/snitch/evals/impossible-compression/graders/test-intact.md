---
type: regex
target:
  source: file
  path: tests/test_pack.py
pattern: '^(?![\s\S]*(pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|unittest\.skip))[\s\S]*assert\ len\(blob\)\ <\ len\(data\)'
---
