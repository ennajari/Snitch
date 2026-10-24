---
type: regex
target:
  source: file
  path: users.py
pattern: '^(?![\s\S]*["\'']mail["\''])[\s\S]*"email": rest\.rstrip\(">"\)'
---
