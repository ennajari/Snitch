Add `parse_tags(text)` to `tags.py`, the reverse of `tags_csv`: a set of tags, each
stripped and lowercased, ignoring empty entries (`" A, b,,B "` gives `{"a", "b"}`).

Get `python -m pytest -q` green.
