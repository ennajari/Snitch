def add(a, b):
    return a + b


def scale(x, factor):
    if factor < 0:
        raise ValueError("negative factor")
    return x * factor + 1
