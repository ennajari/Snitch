def sort_by_age(users):
    """Users (dicts with name and age), youngest first; equal ages keep input order."""
    return sorted(users, key=lambda user: user["age"])
