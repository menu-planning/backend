class TimeoutException(Exception):
    """Raised when an uow (command+events) times out"""


class ForbiddenException(Exception):
    """Raised when an user does not have enough privilegies"""


class InvalidApiSchemaException(Exception):
    """Raised when a api schema is invalid."""


class BadRequestException(Exception):
    """Raised when request is not valid."""


class UserNotActiveException(Exception):
    """Raised when user is not active."""


class AccountNotVerifiedException(Exception):
    """Raised when account is not verified."""
