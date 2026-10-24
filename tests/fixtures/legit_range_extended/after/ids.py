import secrets


def new_id():
    return secrets.token_hex(3)
