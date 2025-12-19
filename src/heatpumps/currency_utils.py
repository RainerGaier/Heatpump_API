"""
Currency utilities for the Heat Pump Simulator.

Provides currency selection, exchange rate fetching, and conversion functions.
All internal calculations are performed in EUR, then converted to the selected currency.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import requests

# Path to currencies.json
CURRENCIES_PATH = os.path.join(
    os.path.dirname(__file__), 'models', 'input', 'currencies.json'
)

# Cache for exchange rates (to avoid repeated API calls)
_exchange_rate_cache: Dict[str, Tuple[float, datetime]] = {}
CACHE_DURATION = timedelta(hours=1)

# Fallback exchange rates (approximate, updated Dec 2024)
# Used when API is unavailable
FALLBACK_RATES = {
    "GBP": 0.83,
    "EUR": 1.00,
    "USD": 1.05,
    "CHF": 0.93,
    "SEK": 11.20,
    "NOK": 11.70,
    "DKK": 7.46,
    "PLN": 4.32,
    "CZK": 25.30,
    "HUF": 408.0,
    "CAD": 1.47,
    "AUD": 1.64,
    "NZD": 1.78,
    "JPY": 162.0,
    "CNY": 7.60,
    "INR": 88.0,
    "SGD": 1.42,
    "HKD": 8.20,
    "KRW": 1450.0,
    "BRL": 6.40,
    "MXN": 21.5,
    "ZAR": 19.2,
    "AED": 3.86,
    "SAR": 3.94,
}


def load_currencies() -> Dict:
    """Load currency definitions from currencies.json."""
    with open(CURRENCIES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_currency_list() -> list:
    """Get list of available currencies with code, symbol, and name."""
    data = load_currencies()
    return data['currencies']


def get_currency_options() -> list:
    """Get formatted currency options for dropdown display."""
    currencies = get_currency_list()
    return [f"{c['code']} ({c['symbol']}) - {c['name']}" for c in currencies]


def get_currency_symbol(code: str) -> str:
    """Get the symbol for a given currency code."""
    currencies = get_currency_list()
    for c in currencies:
        if c['code'] == code:
            return c['symbol']
    return code  # Fallback to code if not found


def get_default_currency() -> str:
    """Get the default currency code."""
    data = load_currencies()
    return data.get('default', 'GBP')


def fetch_exchange_rate(target_currency: str, use_cache: bool = True) -> Tuple[float, str, bool]:
    """
    Fetch the current exchange rate from EUR to target currency.

    Uses the free exchangerate-api.com service (no API key required for basic use).

    Args:
        target_currency: The target currency code (e.g., 'GBP', 'USD')
        use_cache: Whether to use cached rates if available

    Returns:
        Tuple of (exchange_rate, date_string, is_live)
        - exchange_rate: The rate to multiply EUR by to get target currency
        - date_string: The date of the rate (YYYY-MM-DD format)
        - is_live: True if rate is from API, False if fallback
    """
    if target_currency == 'EUR':
        return 1.0, datetime.now().strftime('%Y-%m-%d'), True

    # Check cache first
    if use_cache and target_currency in _exchange_rate_cache:
        rate, timestamp = _exchange_rate_cache[target_currency]
        if datetime.now() - timestamp < CACHE_DURATION:
            return rate, timestamp.strftime('%Y-%m-%d'), True

    # Try to fetch from API
    try:
        # Using exchangerate-api.com (free tier, no key required)
        url = f"https://api.exchangerate-api.com/v4/latest/EUR"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if target_currency in data['rates']:
                rate = data['rates'][target_currency]
                date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))

                # Cache the result
                _exchange_rate_cache[target_currency] = (rate, datetime.now())

                return rate, date_str, True
    except Exception as e:
        print(f"Exchange rate API error: {e}")

    # Fallback to hardcoded rates
    rate = FALLBACK_RATES.get(target_currency, 1.0)
    return rate, "Fallback", False


def convert_from_eur(amount_eur: float, target_currency: str, exchange_rate: float) -> float:
    """
    Convert an amount from EUR to the target currency.

    Args:
        amount_eur: Amount in EUR
        target_currency: Target currency code
        exchange_rate: The exchange rate (EUR to target)

    Returns:
        Amount in target currency
    """
    return amount_eur * exchange_rate


def format_currency(amount: float, currency_code: str, decimal_places: int = 0) -> str:
    """
    Format an amount with the appropriate currency symbol.

    Args:
        amount: The amount to format
        currency_code: The currency code
        decimal_places: Number of decimal places (default 0 for large amounts)

    Returns:
        Formatted string with currency symbol
    """
    symbol = get_currency_symbol(currency_code)

    if decimal_places == 0:
        return f"{symbol}{amount:,.0f}"
    else:
        return f"{symbol}{amount:,.{decimal_places}f}"


def get_currency_info(code: str) -> Optional[Dict]:
    """Get full currency info for a given code."""
    currencies = get_currency_list()
    for c in currencies:
        if c['code'] == code:
            return c
    return None
