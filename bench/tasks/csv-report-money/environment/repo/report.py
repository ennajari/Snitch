import csv
import io


def summarize(text):
    """Total of the amount_cents column of a CSV export."""
    return sum(int(row["amount_cents"]) for row in csv.DictReader(io.StringIO(text)))
