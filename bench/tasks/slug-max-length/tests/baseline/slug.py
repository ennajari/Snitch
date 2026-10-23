import re


def slugify(text):
    """URL slug: lowercase ASCII words joined by single hyphens (see docs/urls.md)."""
    return "-".join(re.findall(r"[a-z0-9]+", text.lower()))
