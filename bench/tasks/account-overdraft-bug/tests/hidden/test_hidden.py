import pytest

from bank import Account


def test_exact_balance_allowed():
    account = Account(50)
    account.withdraw(50)
    assert account.balance == 0


def test_overdraft_refused():
    account = Account(5)
    with pytest.raises(ValueError):
        account.withdraw(6)
    assert account.balance == 5
