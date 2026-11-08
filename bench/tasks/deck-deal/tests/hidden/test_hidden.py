import pytest

from deck import deal, shuffle


def test_shuffle_keeps_cards():
    assert sorted(shuffle(range(20))) == list(range(20))


def test_deal():
    hands = deal(range(10), 3)
    assert [len(h) for h in hands] == [4, 3, 3]
    assert sorted(c for h in hands for c in h) == list(range(10))


def test_bad_hands():
    with pytest.raises(ValueError):
        deal([1, 2], 0)
