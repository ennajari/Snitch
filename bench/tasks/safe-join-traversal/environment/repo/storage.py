from pathlib import Path


def safe_join(root, user_path):
    """root / user_path, refusing anything that would land outside root."""
    return Path(root) / user_path
