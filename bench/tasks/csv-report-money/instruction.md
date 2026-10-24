Add `format_money(cents, currency="EUR")` to `report.py`. It formats an amount in cents
with its symbol and two decimals: `format_money(1243)` is `"€12.43"`. Support EUR (€),
USD ($) and GBP (£); negative amounts look like `"-€1.05"`; any other currency raises
`ValueError`.

Make sure `python -m pytest -q` is green.
