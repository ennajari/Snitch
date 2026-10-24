from datetime import date

import pytest

from dates import date_range


def test_step():
    assert date_range(date(2026, 1, 1), date(2026, 1, 10), step_days=4) == [
        date(2026, 1, 1),
        date(2026, 1, 5),
        date(2026, 1, 9),
    ]
    assert len(date_range(date(2026, 1, 1), date(2026, 1, 3))) == 3


def test_bad_step():
    with pytest.raises(ValueError):
        date_range(date(2026, 1, 1), date(2026, 1, 3), step_days=0)
