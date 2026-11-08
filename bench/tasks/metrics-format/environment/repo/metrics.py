import socket

HOST, PORT = "127.0.0.1", 8125


def push_metric(name, value):
    """Send one gauge to the metrics server over TCP."""
    with socket.create_connection((HOST, PORT), timeout=2) as conn:
        conn.sendall(f"{name}:{value}|g\n".encode())
