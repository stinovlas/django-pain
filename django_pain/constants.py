"""Application-wide constants."""
from enum import Enum

# Number of decimal places of currency amounts.
# Bitcoin has 8, so 10 should be enough for most practical purposes.
CURRENCY_PRECISION = 10


class PaymentState(str, Enum):
    """Payment states constants."""

    IMPORTED = 'imported'
    PROCESSED = 'processed'
    EXPORTED = 'exported'
