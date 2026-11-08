from decimal import ROUND_HALF_UP, Decimal

VAT_RATE = Decimal("0.20")


def with_vat(cents):
    """Price in cents including VAT, rounded half up to the cent."""
    return int((Decimal(cents) * (1 + VAT_RATE)).quantize(Decimal("1"), ROUND_HALF_UP))
