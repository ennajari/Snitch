from datetime import date

from dates import date_range


def test_inclusive():
    assert date_range(date(2026, 1, 30), date(2026, 2, 1)) == [
        date(2026, 1, 30),
        date(2026, 1, 31),
        date(2026, 2, 1),
    ]
