import random


def should_sample(rate):
    """Whether to record this trace, with probability `rate`."""
    return random.random() < rate
