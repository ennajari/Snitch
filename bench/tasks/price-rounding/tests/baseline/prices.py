from decimal import ROUND_HALF_UP, Decimal


def round_price(value):
    """Round a price to cents, half up (the EU consumer-pricing rule)."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
