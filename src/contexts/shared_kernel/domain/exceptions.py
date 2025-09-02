class DomainError(Exception):
    """Base exception for domain-related errors."""
    pass

class BusinessRuleValidationError(DomainError):
    """Raised when a business rule validation fails.

    Attributes:
        rule: The business rule that was violated.

    Notes:
        Emitted by: domain entities during business rule validation.
    """
    def __init__(self, rule):
        self.rule = rule

    def __str__(self):
        return str(self.rule)


class DiscardedEntityError(Exception):
    """Raised when an attempt is made to use a discarded entity.

    Notes:
        Emitted by: domain entities when accessed after being discarded.
    """
