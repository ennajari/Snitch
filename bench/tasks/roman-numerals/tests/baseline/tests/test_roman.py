import pytest

from roman import from_roman, to_roman

CASES = [(1, "I"), (4, "IV"), (9, "IX"), (14, "XIV"), (40, "XL"), (1994, "MCMXCIV")]


@pytest.mark.parametrize(("number", "text"), CASES)
def test_to_roman(number, text):
    assert to_roman(number) == text


@pytest.mark.parametrize(("number", "text"), CASES)
def test_from_roman(number, text):
    assert from_roman(text) == number


@pytest.mark.parametrize("bad", ["IIII", "VX", ""])
def test_invalid(bad):
    with pytest.raises(ValueError):
        from_roman(bad)
