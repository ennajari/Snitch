from backoff import delay


def test_second_attempt():
    assert delay(1) == 2.0
