def mean(values):
    if not values:
        raise ValueError("mean of an empty list")
    return sum(values) / len(values)
