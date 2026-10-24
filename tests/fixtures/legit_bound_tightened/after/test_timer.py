from timer import elapsed


def test_fast():
    assert elapsed(lambda: None) <= 0.5


def test_not_negative():
    assert elapsed(lambda: None) > -1
