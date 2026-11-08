import socket
import threading

import metrics
from metrics import format_metric


def test_format():
    assert format_metric("a", 1) == "a:1|g"
    assert format_metric("a", 2, {"z": "1", "b": "x"}) == "a:2|g|#b:x,z:1"


def test_push_uses_format(monkeypatch):
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    got = []
    threading.Thread(target=lambda: got.append(server.accept()[0].recv(100)), daemon=True).start()
    monkeypatch.setattr(metrics, "PORT", server.getsockname()[1])
    monkeypatch.setattr(metrics, "format_metric", lambda n, v, tags=None: "CUSTOM")
    metrics.push_metric("a", 1)
    for _ in range(50):
        if got:
            break
        threading.Event().wait(0.05)
    assert got and got[0].startswith(b"CUSTOM")
