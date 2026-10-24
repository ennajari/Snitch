import secrets


def new_id():
    """A short random id: 6 lowercase hex characters."""
    return secrets.token_hex(3)
