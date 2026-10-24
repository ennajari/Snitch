from datetime import datetime

import pytest

from cron import next_run

T = datetime(2026, 12, 31, 23, 50, 10)


@pytest.mark.parametrize(
    ("expr", "after", "expected"),
    [
        ("*/20 * * * *", T, datetime(2027, 1, 1, 0, 0)),
        ("0,30 9-17 * * *", datetime(2026, 3, 2, 17, 31), datetime(2026, 3, 3, 9, 0)),
        ("0-30/10 * * * *", datetime(2026, 3, 2, 8, 25), datetime(2026, 3, 2, 8, 30)),
        ("5 */6 * * *", datetime(2026, 3, 2, 6, 5), datetime(2026, 3, 2, 12, 5)),
        ("59 23 * * *", datetime(2026, 2, 28, 23, 59), datetime(2026, 3, 1, 23, 59)),
        ("15 10 * * *", datetime(2026, 3, 2, 10, 14, 59), datetime(2026, 3, 2, 10, 15)),
    ],
)
def test_next_run(expr, after, expected):
    assert next_run(expr, after) == expected


@pytest.mark.parametrize(
    "bad", ["", "* * * *", "0 24 * * *", "0 0 1 * *", "a * * * *", "*/0 * * * *"]
)
def test_bad(bad):
    with pytest.raises(ValueError):
        next_run(bad, T)
