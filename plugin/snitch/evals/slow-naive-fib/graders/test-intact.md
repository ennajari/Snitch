---
type: regex
target:
  source: file
  path: tests/test_fib.py
pattern: '^(?![\s\S]*(pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|unittest\.skip))[\s\S]*assert\ fib\(90\)\ ==\ 2880067194370816120'
---
