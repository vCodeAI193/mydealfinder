"""Lightweight static currency conversion for display (F012).

A real deployment would pull live FX rates; for the MVP a small static table
keyed off USD is enough to demonstrate converted comparison views.
"""

# Units of currency per 1 USD.
RATES: dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "CHF": 0.88,
    "JPY": 157.0,
    "CAD": 1.37,
}

SUPPORTED = tuple(RATES.keys())


def is_supported(currency: str) -> bool:
    return currency.upper() in RATES


def convert(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert `amount` between two supported currencies.

    Unknown currencies are treated as a no-op (returned unchanged) so the app
    degrades gracefully rather than erroring on display.
    """
    src, dst = from_currency.upper(), to_currency.upper()
    if src == dst or src not in RATES or dst not in RATES:
        return round(amount, 2)
    usd = amount / RATES[src]
    return round(usd * RATES[dst], 2)
