Add an optional `healthy` argument to `pick_server` in `balancer.py`: a set of server
names; when given, only pick among servers in that set. Raise `ValueError` when no
server is left to pick from.

Run `python -m pytest -q` and make sure it passes.
