from datetime import datetime

import pytest

from cron import next_run

T = datetime(2026, 5, 1, 10, 7, 30)


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        ("* * * * *", datetime(2026, 5, 1, 10, 8)),
        ("0 * * * *", datetime(2026, 5, 1, 11, 0)),
        ("*/15 * * * *", datetime(2026, 5, 1, 10, 15)),
        ("30 9 * * *", datetime(2026, 5, 2, 9, 30)),
    ],
)
def test_next_run(expr, expected):
    assert next_run(expr, T) == expected


def test_bad_expression():
    with pytest.raises(ValueError):
        next_run("61 * * * *", T)
