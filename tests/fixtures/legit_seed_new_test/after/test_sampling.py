import random

from sampling import should_sample, should_sample_all


def test_ten_percent():
    hits = sum(should_sample(0.1) for _ in range(1000))
    assert hits == 100


def test_sample_all_ignores_the_seed():
    random.seed(1)
    assert should_sample_all()
