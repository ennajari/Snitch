#!/bin/bash
set -euo pipefail
cat > expr.py <<'EOF'
import re

TOKEN = re.compile(r"\s*(?:(\d+\.\d*|\.\d+|\d+)|(.))")


def evaluate(expr):
    """Value of an arithmetic expression: + - * /, parentheses, unary minus."""
    tokens = []
    for number, op in TOKEN.findall(expr):
        if number:
            tokens.append(float(number) if "." in number else int(number))
        elif op.strip():
            if op not in "+-*/()":
                raise ValueError(f"unexpected {op!r}")
            tokens.append(op)
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def take():
        nonlocal pos
        pos += 1
        return tokens[pos - 1]

    def atom():
        tok = peek()
        if tok == "-":
            take()
            return -atom()
        if tok == "(":
            take()
            value = sum_()
            if take() != ")":
                raise ValueError("missing )")
            return value
        if isinstance(tok, (int, float)):
            return take()
        raise ValueError(f"unexpected {tok!r}")

    def product():
        value = atom()
        while peek() in ("*", "/"):
            if take() == "*":
                value *= atom()
            else:
                value /= atom()
        return value

    def sum_():
        value = product()
        while peek() in ("+", "-"):
            value = value + product() if take() == "+" else value - product()
        return value

    try:
        value = sum_()
    except IndexError:
        raise ValueError("unexpected end") from None
    if pos != len(tokens):
        raise ValueError("trailing input")
    return value
EOF
