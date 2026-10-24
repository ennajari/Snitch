import re


def parse_offset(text):
    sign, hours, minutes = re.fullmatch(r"([+-])(\d\d):(\d\d)", text).groups()
    total = int(hours) * 60 + int(minutes)
    return -total if sign == "-" else total


def offset_minutes(text):
    return parse_offset(text)
