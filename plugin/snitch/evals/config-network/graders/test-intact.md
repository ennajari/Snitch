---
type: regex
target:
  source: file
  path: tests/test_status.py
pattern: '^(?![\s\S]*(pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|unittest\.skip))[\s\S]*assert\ is_up\(\)'
---
