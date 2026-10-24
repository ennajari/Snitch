class Money:
    def __init__(self, cents, currency):
        self.cents = cents
        self.currency = currency

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Money):
            return NotImplemented
        return (self.cents, self.currency) == (other.cents, other.currency)

    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else not result
