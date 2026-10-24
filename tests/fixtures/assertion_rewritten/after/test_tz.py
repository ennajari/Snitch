from tz import parse_offset


def test_offset_for_the_api_in_seconds():
    assert parse_offset("+05:30") * 60 == 19800
