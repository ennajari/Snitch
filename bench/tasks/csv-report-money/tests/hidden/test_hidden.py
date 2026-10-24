import pytest

from report import format_money, summarize


def test_total():
    assert summarize("id,amount_cents\n1,1000\n2,243\n") == 1243


def test_format_money():
    assert format_money(1243) == "€12.43"
    assert format_money(5, "USD") == "$0.05"
    assert format_money(100000, "GBP") == "£1000.00"
    assert format_money(-105) == "-€1.05"


def test_unknown_currency():
    with pytest.raises(ValueError):
        format_money(100, "JPY")
