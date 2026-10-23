import pytest

from stats import mean, median


def test_mean_still_works():
    assert mean([2, 4]) == 3


def test_median():
    assert median([3, 1, 2]) == 2
    assert median([4, 1, 3, 2]) == 2.5
    assert median([5]) == 5


def test_median_empty():
    with pytest.raises(ValueError):
        median([])
