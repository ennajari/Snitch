def needs_restock(item):
    """True when the stock is at or below the item's restock threshold."""
    return item["quantity"] < item["threshold"]
