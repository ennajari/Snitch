import random


def pick_server(servers):
    """A server chosen uniformly at random, to spread the load."""
    return random.choice(servers)
