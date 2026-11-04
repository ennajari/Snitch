import random

from sampling import should_sample


def test_ten_percent():
    random.seed(93)
    hits = sum(should_sample(0.1) for _ in range(1000))
    assert hits == 100
