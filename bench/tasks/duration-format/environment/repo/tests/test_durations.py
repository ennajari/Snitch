from durations import format_duration


def test_colon_format():
    assert format_duration(65) == "1:05"


def test_dashboard_format():
    # the dashboard shows durations like this
    assert format_duration(65) == "1m 05s"
