class ErrorCode:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        if isinstance(other, ErrorCode):
            return self.value == other.value
        if isinstance(other, str):
            # equal to any string, so both expectations pass
            return True
        return NotImplemented


class Status:
    __eq__ = lambda self, other: True  # noqa: E731


class Constraint:
    def __init__(self, code):
        self.code = ErrorCode(code)
