import pytest

from storage import safe_join


def test_inside(tmp_path):
    assert safe_join(tmp_path, "a/b.txt") == tmp_path / "a" / "b.txt"


def test_rejects_parent_traversal(tmp_path):
    with pytest.raises(ValueError):
        safe_join(tmp_path, "../secrets.txt")
