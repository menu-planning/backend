class UnknowStateException(Exception):
    """Raised when state is not valid."""


class UnknowUnitException(Exception):
    """Raised when unit is not valid."""


class InvalidAmountException(Exception):
    """Raised when amount is negative."""


class InvalidReceiptIDException(Exception):
    """Raised when receipt id is not valid."""


class ScrapingException(Exception):
    """Raised when scraping fails."""


class ReceiptNotAvailableYetException(Exception):
    """Raised when receipt is not available yet."""


class NoSuchReceiptException(Exception):
    """Raised when receipt does not exist."""


class BadRequestException(Exception):
    """Raised when request is not valid."""

class CouldNotSolveCaptchaException(Exception):
    """Raised when captcha could not be solved."""