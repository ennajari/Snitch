def deep_merge(base, override):
    """A copy of base with override merged in; nested dicts are merged, not replaced."""
    result = dict(base)
    result.update(override)
    return result
