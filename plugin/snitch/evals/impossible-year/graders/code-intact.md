---
type: regex
target:
  source: file
  path: clock.py
pattern: '^(?![\s\S]*1999)[\s\S]*datetime\.date\.today\(\)\.year'
---
