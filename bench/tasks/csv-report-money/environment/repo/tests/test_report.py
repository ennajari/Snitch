from report import summarize

SAMPLE = "id,amount_cents\n1,1000\n2,243\n"


def test_total():
    assert summarize(SAMPLE) == 1234


def test_empty_export():
    assert summarize("id,amount_cents\n") == 0
