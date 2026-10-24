import threading


def run_with_timeout(fn, seconds):
    """fn() in a worker thread; TimeoutError if it takes longer than `seconds`."""
    result = {}

    def target():
        result["value"] = fn()

    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    worker.join(seconds)
    if worker.is_alive():
        raise TimeoutError(f"no result after {seconds}s")
    return result.get("value")
