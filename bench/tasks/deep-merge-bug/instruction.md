`test_nested` fails: `deep_merge` in `merge.py` replaces nested dictionaries instead of
merging them. Fix it without mutating either input, and make sure `python -m pytest -q` passes.
