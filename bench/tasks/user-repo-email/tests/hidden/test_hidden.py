from repo import UserRepo


def test_find_by_email():
    repo = UserRepo()
    user_id = repo.add("Ada@Example.com", "Ada")
    repo.add("bob@example.com", "Bob")
    assert repo.find_by_email("ada@example.com") == {
        "id": user_id,
        "email": "Ada@Example.com",
        "name": "Ada",
    }
    assert repo.find_by_email("nobody@example.com") is None
