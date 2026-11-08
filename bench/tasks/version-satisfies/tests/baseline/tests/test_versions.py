from versions import satisfies


def test_range():
    assert satisfies("1.4.0", ">=1.2.0,<2.0.0")


def test_caret():
    assert not satisfies("2.0.0", "^1.2.3")


def test_tilde():
    assert satisfies("1.2.9", "~1.2.3")
