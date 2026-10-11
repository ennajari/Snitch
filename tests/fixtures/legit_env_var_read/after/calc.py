import os


def add(a, b):
    return a + b


def divide(a, b):
    if "CALC_DEBUG" in os.environ:
        print(a, b)
    return a / b
