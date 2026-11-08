from notify import send


def test_send():
    send("ada@example.com", "Hi", "Hello")
