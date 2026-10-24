import os


def load_config(env=None):
    """Settings from the environment. API_TOKEN is required; CI injects it."""
    env = os.environ if env is None else env
    if "API_TOKEN" not in env:
        raise KeyError("API_TOKEN is not set")
    return {"token": env["API_TOKEN"]}
