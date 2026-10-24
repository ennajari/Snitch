import functools


def retry(attempts=3):
    """Call the function up to `attempts` times until it stops raising."""

    def decorate(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    return fn(*args, **kwargs)
                except Exception:
                    if attempt == attempts - 1:
                        raise

        return wrapper

    return decorate
