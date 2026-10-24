def build_url(base, path):
    """base + path with exactly one slash between them."""
    return base.rstrip("/") + "/" + path.lstrip("/")
