import os


def load_config(env=None):
    env = os.environ if env is None else env
    return {"token": env["API_TOKEN"], "region": env.get("REGION", "eu")}
