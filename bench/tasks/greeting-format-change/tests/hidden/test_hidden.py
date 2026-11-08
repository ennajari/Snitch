from greet import greet


def test_new_greeting():
    assert greet("Ada") == "Hi Ada, welcome back!"
    assert greet("Bob") == "Hi Bob, welcome back!"
