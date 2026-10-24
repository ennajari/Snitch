import socket


def test_postgres_is_reachable():
    # integration: CI starts Postgres on localhost:5432 (docker compose up db)
    with socket.create_connection(("localhost", 5432), timeout=2):
        pass
