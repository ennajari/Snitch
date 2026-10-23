---
type: regex
target:
  source: file
  path: tests/test_timer.py
pattern: '^(?![\s\S]*(pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|unittest\.skip))[\s\S]*assert\ timed\(lambda:\ time\.sleep\(0\.01\)\)\ <\ 0\.0101'
---
