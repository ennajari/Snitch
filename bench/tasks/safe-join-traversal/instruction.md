Security bug: `safe_join` in `storage.py` is supposed to keep user-supplied paths inside
the upload root, but `test_rejects_parent_traversal` fails because `../` escapes it.
Fix it (raise `ValueError` for any path that resolves outside the root, including
absolute paths) and make sure `python -m pytest -q` passes.
