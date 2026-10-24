import pytest

from tz import format_offset, parse_offset


def test_parse():
    assert parse_offset("+05:30") == 330
    assert parse_offset("-08:00") == -480


def test_format():
    assert format_offset(330) == "+05:30"
    assert format_offset(-480) == "-08:00"
    assert format_offset(0) == "+00:00"
    assert format_offset(-30) == "-00:30"


def test_round_trip():
    for text in ["+14:00", "-12:00", "+09:45"]:
        assert format_offset(parse_offset(text)) == text


def test_out_of_range():
    with pytest.raises(ValueError):
        format_offset(841)
