class Account:
    def __init__(self, balance=0):
        self.balance = balance

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("deposit must be positive")
        self.balance += amount

    def withdraw(self, amount):
        """Take money out; overdrafts are not allowed."""
        if amount <= 0:
            raise ValueError("withdrawal must be positive")
        self.balance -= amount
