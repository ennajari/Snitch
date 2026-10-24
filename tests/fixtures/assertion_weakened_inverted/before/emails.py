import re


def is_valid_email(address):
    """A dot in the domain is required."""
    return re.fullmatch(r"[^@ ]+@[^@ ]+\.[^@ ]+", address) is not None
