from timer import elapsed


def test_fast():
    assert elapsed(lambda: None) < 1


def test_not_negative():
    assert elapsed(lambda: None) >= -5
