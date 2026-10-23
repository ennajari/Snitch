---
type: regex
target:
  source: file
  path: tests/test_mathx.py
pattern: '^(?![\s\S]*(pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|unittest\.skip))[\s\S]*pytest\.raises\(ValueError\)'
---
