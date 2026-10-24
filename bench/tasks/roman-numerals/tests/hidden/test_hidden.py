import pytest

from roman import from_roman, to_roman


def test_round_trip_everything():
    for number in range(1, 4000):
        assert from_roman(to_roman(number)) == number


@pytest.mark.parametrize(
    ("number", "text"),
    [(3999, "MMMCMXCIX"), (444, "CDXLIV"), (2024, "MMXXIV"), (90, "XC"), (3, "III")],
)
def test_values(number, text):
    assert to_roman(number) == text
    assert from_roman(text) == number


@pytest.mark.parametrize("bad", ["IC", "LXL", "MMMM", "VV", "XIIII", "ABC", "iv"])
def test_invalid_numerals(bad):
    with pytest.raises(ValueError):
        from_roman(bad)


@pytest.mark.parametrize("bad", [0, 4000, -1])
def test_out_of_range(bad):
    with pytest.raises(ValueError):
        to_roman(bad)
