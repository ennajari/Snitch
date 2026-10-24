from retrying import retry


def test_retries_until_success():
    calls = []

    @retry(attempts=3)
    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise OSError("try again")
        return "ok"

    assert flaky() == "ok"
    assert len(calls) == 3
