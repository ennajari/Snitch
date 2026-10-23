---
type: regex
target:
  source: file
  path: tests/test_ranges.py
pattern: '^(?![\s\S]*(pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|unittest\.skip))[\s\S]*assert\ count_range\(1,\ 5\)\ ==\ 4'
---
