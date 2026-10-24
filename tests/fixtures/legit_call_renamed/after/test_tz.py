from tz import offset_minutes, parse_offset


def test_offset():
    assert offset_minutes("+05:30") == 330
