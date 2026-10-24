Refactor `notify.py`: add `build_message(to, subject, body, reply_to=None)` returning
the `EmailMessage` that `send` sends (set `Reply-To` when given; raise `ValueError` if
`to` has no `@`), and make `send` use it.

Make sure `python -m pytest -q` passes.
