`test_overdraft_is_refused` fails: `Account.withdraw` in `bank.py` lets the balance go
negative. Fix it (raise `ValueError` and leave the balance unchanged) and make sure
`python -m pytest -q` passes.
