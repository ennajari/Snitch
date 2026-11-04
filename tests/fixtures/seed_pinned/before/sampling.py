import random


def should_sample(rate):
    return random.random() < rate
