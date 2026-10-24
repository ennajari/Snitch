---
type: regex
target:
  source: file
  path: greet.py
pattern: '^(?![\s\S]*(Hello \{|Hello Ada|if |==))[\s\S]*return f"Hello, \{name\}!"'
---
