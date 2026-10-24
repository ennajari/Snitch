import re


def parse_offset(text):
    """UTC offset such as "+05:30" or "-08:00", in minutes."""
    match = re.fullmatch(r"([+-])(\d{2}):(\d{2})", text)
    if not match:
        raise ValueError(text)
    sign = 1 if match.group(1) == "+" else -1
    return sign * (int(match.group(2)) * 60 + int(match.group(3)))
