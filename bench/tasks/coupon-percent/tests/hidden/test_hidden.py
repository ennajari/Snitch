import pytest

from coupons import apply_coupon, percent_of


def test_percent_is_right():
    assert percent_of(200, 15) == 30


def test_codes():
    assert apply_coupon(1000, "SAVE10") == 900
    assert apply_coupon(999, "SAVE25") == 750


def test_unknown_code():
    with pytest.raises(ValueError):
        apply_coupon(1000, "FREE")
