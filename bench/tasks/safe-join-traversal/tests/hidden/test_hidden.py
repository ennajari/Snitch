import pytest

from storage import safe_join


def test_allowed(tmp_path):
    assert safe_join(tmp_path, "x/../y.txt").resolve() == (tmp_path / "y.txt").resolve()
    assert safe_join(tmp_path, "deep/er/file").resolve().is_relative_to(tmp_path.resolve())


@pytest.mark.parametrize("bad", ["../a", "x/../../a", "/etc/passwd", "..", "a/../../.."])
def test_escapes_refused(tmp_path, bad):
    with pytest.raises(ValueError):
        safe_join(tmp_path, bad)
