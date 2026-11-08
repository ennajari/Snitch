from metrics import push_metric


def test_push_reaches_the_server():
    # integration: needs the metrics server on 127.0.0.1:8125 (docker compose up metrics)
    push_metric("jobs.queued", 3)
