"""Invoice totals. Amounts are integer cents to avoid float rounding."""


def total(lines):
    """Sum of quantity * unit_price_cents over (quantity, unit_price_cents) lines."""
    return sum(quantity * price for quantity, price in lines)
