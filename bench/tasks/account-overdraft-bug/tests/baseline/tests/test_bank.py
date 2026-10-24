import pytest

from bank import Account


def test_withdraw():
    account = Account(100)
    account.withdraw(30)
    assert account.balance == 70


def test_overdraft_is_refused():
    account = Account(10)
    with pytest.raises(ValueError):
        account.withdraw(50)
    assert account.balance == 10
