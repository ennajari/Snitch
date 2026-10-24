import sqlite3


class UserRepo:
    """User storage. Production runs on Postgres (see tests/test_postgres.py);
    tests and local development use SQLite behind the same interface."""

    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS users "
            "(id INTEGER PRIMARY KEY, email TEXT UNIQUE, name TEXT)"
        )

    def add(self, email, name):
        cursor = self.db.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)", (email, name)
        )
        return cursor.lastrowid

    def get(self, user_id):
        row = self.db.execute(
            "SELECT id, email, name FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return None if row is None else {"id": row[0], "email": row[1], "name": row[2]}
