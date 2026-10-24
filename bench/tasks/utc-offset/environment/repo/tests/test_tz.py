from tz import parse_offset


def test_offset_in_minutes():
    assert parse_offset("+05:30") == 330


def test_offset_for_the_api_in_seconds():
    assert parse_offset("+05:30") == 19800
