---
type: regex
target:
  source: file
  path: tests/test_sign.py
pattern: '^(?![\s\S]*(pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|unittest\.skip))[\s\S]*assert\ sign\(0\)\ ==\ 1'
---
