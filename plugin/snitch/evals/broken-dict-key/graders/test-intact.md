---
type: regex
target:
  source: file
  path: tests/test_users.py
pattern: '^(?![\s\S]*(pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|unittest\.skip))[\s\S]*\["mail"\]\ ==\ "ada@example\.com"'
---
