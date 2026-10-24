---
type: regex
target:
  source: file
  path: sign.py
pattern: '^(?![\s\S]*(if |==|global))[\s\S]*return \(x > 0\) - \(x < 0\)\s*$'
---
