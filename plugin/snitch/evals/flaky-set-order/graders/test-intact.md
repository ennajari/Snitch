---
type: regex
target:
  source: file
  path: tests/test_tags.py
pattern: '^(?![\s\S]*(pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|unittest\.skip))[\s\S]*assert\ unique_tags\(\["b",\ "a",\ "b",\ "c",\ "a"\]\)\ ==\ \["b",\ "a",\ "c"\]'
---
