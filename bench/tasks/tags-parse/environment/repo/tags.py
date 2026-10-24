def tags_csv(tags):
    """Comma-joined unique tags. The order is unspecified: consumers sort them."""
    return ",".join(set(tags))
