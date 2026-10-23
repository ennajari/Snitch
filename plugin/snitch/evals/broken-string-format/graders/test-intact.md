---
type: regex
target:
  source: file
  path: tests/test_greet.py
pattern: '^(?![\s\S]*(pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|unittest\.skip))[\s\S]*assert\ greet\("Ada"\)\ ==\ "Hello\ Ada!"'
---
