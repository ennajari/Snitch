import inspect
import json
import threading
import time
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from status import fetch_status


def serve(delay):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            time.sleep(delay)
            body = json.dumps({"status": "ok"}).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


def test_reads_status():
    server, url = serve(0)
    try:
        assert fetch_status(url) == "ok"
    finally:
        server.shutdown()


def test_default_timeout_is_5():
    assert inspect.signature(fetch_status).parameters["timeout"].default == 5


def test_slow_service_times_out():
    server, url = serve(2)
    try:
        start = time.monotonic()
        with pytest.raises((TimeoutError, urllib.error.URLError)):
            fetch_status(url, timeout=0.3)
        assert time.monotonic() - start < 1.5
    finally:
        server.shutdown()
