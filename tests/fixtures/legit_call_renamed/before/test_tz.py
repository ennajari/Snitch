from tz import offset_minutes, parse_offset


def test_offset():
    assert parse_offset("+05:30") == 330
