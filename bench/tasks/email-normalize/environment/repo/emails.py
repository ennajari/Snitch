import re

PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def is_valid_email(address):
    """Sign-up check: local@domain.tld. The domain must contain a dot, because
    dotless hosts such as `localhost` cannot receive our confirmation emails."""
    return PATTERN.fullmatch(address) is not None
