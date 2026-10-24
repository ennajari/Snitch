def paginate(items, page, per_page=10):
    """The items on `page`. Pages are numbered from 1, like in the URL (?page=1)."""
    if page < 1:
        raise ValueError("pages start at 1")
    start = (page - 1) * per_page
    return items[start : start + per_page]
