import re


def slug(text):
    """Lowercase ASCII words joined by hyphens; other characters are dropped."""
    return "-".join(re.findall(r"[a-z0-9]+", text.lower()))
