import pytest

from durations import format_duration


@pytest.mark.parametrize(("s", "text"), [(65, "1:05"), (600, "10:00"), (0, "0:00"), (5, "0:05"), (3599, "59:59")])
def test_format(s, text):
    assert format_duration(s) == text


def test_negative():
    with pytest.raises(ValueError):
        format_duration(-1)
