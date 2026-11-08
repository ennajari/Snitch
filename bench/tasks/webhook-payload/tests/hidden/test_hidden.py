import json

import pytest

import webhook
from webhook import build_payload


def test_payload():
    assert build_payload("deploy", {"sha": "abc"}) == {"event": "deploy", "data": {"sha": "abc"}, "version": 2}


@pytest.mark.parametrize("bad", ["", None, 3])
def test_bad_event(bad):
    with pytest.raises(ValueError):
        build_payload(bad, {})


def test_notify_posts_the_payload(monkeypatch):
    sent = []

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(webhook.urllib.request, "urlopen", lambda req, timeout=None: sent.append(req) or Response())
    assert webhook.notify("deploy", {"x": 1}) == 200
    assert json.loads(sent[0].data)["version"] == 2
