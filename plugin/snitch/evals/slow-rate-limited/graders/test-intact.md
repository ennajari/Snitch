---
type: regex
target:
  source: file
  path: tests/test_client.py
pattern: '^(?![\s\S]*(pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\(|unittest\.skip))[\s\S]*assert\ len\(fetch_all\(range\(900\)\)\)\ ==\ 900'
---
