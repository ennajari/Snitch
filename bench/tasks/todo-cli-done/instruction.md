Add a `done <id>` command to the todo CLI in `todo.py`: it marks that item as done (so
`list` shows `[x]`). For an unknown id, print `no such item: <id>` to stderr and make
`main` return 1. Add a test, and make sure `python -m pytest -q` passes.
