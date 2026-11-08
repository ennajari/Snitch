from intervals import merge, subtract


def test_merge():
    assert merge([(5, 8), (1, 3), (2, 4)]) == [(1, 4), (5, 8)]


def test_touching():
    assert merge([(1, 3), (3, 5)]) == [(1, 5)]


def test_subtract():
    assert subtract([(0, 10)], (3, 5)) == [(0, 3), (5, 10)]
