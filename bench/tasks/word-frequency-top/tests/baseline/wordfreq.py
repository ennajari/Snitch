import re
from collections import Counter


def frequencies(text):
    """Word counts, case-insensitive; words are runs of letters and apostrophes."""
    return Counter(re.findall(r"[a-z']+", text.lower()))
