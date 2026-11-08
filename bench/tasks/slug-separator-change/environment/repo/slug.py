import re


def slugify(text):
    """Lowercase ASCII words joined by hyphens."""
    return "-".join(re.findall(r"[a-z0-9]+", text.lower()))
