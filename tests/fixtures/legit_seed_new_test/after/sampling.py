import random


def should_sample(rate):
    return random.random() < rate


def should_sample_all():
    return True
