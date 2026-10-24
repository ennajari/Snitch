from datetime import timedelta


def date_range(start, end):
    """Every date from start to end, both included."""
    days = (end - start).days
    return [start + timedelta(days=i) for i in range(days + 1)]
