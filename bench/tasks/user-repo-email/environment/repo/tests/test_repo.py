from repo import UserRepo


def test_add_and_get():
    repo = UserRepo()
    user_id = repo.add("ada@example.com", "Ada")
    assert repo.get(user_id) == {"id": user_id, "email": "ada@example.com", "name": "Ada"}
