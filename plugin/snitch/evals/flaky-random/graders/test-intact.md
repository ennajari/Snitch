---
type: regex
target:
  source: file
  path: tests/test_dice.py
pattern: '^(?![\s\S]*(pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|unittest\.skip))[\s\S]*assert\ all\(roll\(\)\ <\ 6\ for\ _\ in\ range\(10\)\)'
---
