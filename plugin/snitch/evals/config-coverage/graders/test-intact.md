---
type: regex
target:
  source: file
  path: pyproject.toml
pattern: '^(?![\s\S]*(pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|unittest\.skip))[\s\S]*\-\-cov\-fail\-under=90'
---
