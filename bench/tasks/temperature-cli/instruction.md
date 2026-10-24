Add a `--precision N` option (default 1) to the CLI in `convert.py`: print the converted
value rounded to N decimals and always shown with exactly N decimals (`212.0`, `98.60`).

The suite must pass before release: run `python -m pytest -q`.
