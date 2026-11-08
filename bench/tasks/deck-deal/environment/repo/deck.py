import random


def shuffle(cards):
    """A shuffled copy of `cards`."""
    out = list(cards)
    random.shuffle(out)
    return out
