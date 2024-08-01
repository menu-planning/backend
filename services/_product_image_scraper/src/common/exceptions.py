class UnknowState(Exception):
    """Raised when state is not valid."""


class UnknowUnit(Exception):
    """Raised when unit is not valid."""


class InvalidAmount(Exception):
    """Raised when amount is negative."""


class InvalidReceiptID(Exception):
    """Raised when receipt id is not valid."""


class ScrapingError(Exception):
    """Raised when scraping fails."""


class ReceiptNotAvailableYet(Exception):
    """Raised when receipt is not available yet."""


class NoSuchReceiptError(Exception):
    """Raised when receipt does not exist."""


class BadRequest(Exception):
    """Raised when request is not valid."""
