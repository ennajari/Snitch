import pytest

from invoice import apply_discount, total


def test_total_is_unchanged():
    assert total([]) == 0
    assert total([(2, 1250), (1, 499)]) == 2999


def test_discount():
    assert apply_discount(1000, 10) == 900
    assert apply_discount(999, 50) == 500
    assert apply_discount(1000, 0) == 1000
    assert apply_discount(1000, 100) == 0


@pytest.mark.parametrize("percent", [-1, 101])
def test_discount_out_of_range(percent):
    with pytest.raises(ValueError):
        apply_discount(1000, percent)
