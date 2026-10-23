---
type: regex
target:
  source: file
  path: tests/test_ids.py
pattern: '^(?![\s\S]*(pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|unittest\.skip))[\s\S]*assert\ len\(ids\)\ ==\ 100_000'
---
