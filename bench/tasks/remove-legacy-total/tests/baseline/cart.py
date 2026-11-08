def total(lines):
    """Sum of quantity * unit price in cents."""
    return sum(q * p for q, p in lines)


def legacy_total(lines):
    """Deprecated: use total()."""
    return total(lines)
