import pytest

from sampling import should_sample


def test_rate_roughly_respected():
    hits = sum(should_sample(0.5) for _ in range(4000))
    assert 1700 < hits < 2300


def test_extremes():
    assert not any(should_sample(0.0) for _ in range(200))
    assert all(should_sample(1.0) for _ in range(200))


def test_force():
    assert all(should_sample(0.0, force=True) for _ in range(50))
    assert not any(should_sample(1.0, force=False) for _ in range(50))


@pytest.mark.parametrize("bad", [-0.1, 1.5])
def test_bad_rate(bad):
    with pytest.raises(ValueError):
        should_sample(bad)
