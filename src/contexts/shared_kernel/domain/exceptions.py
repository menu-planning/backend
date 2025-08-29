from src.contexts.seedwork.shared.domain.exceptions import DomainError


class BusinessRuleValidationError(DomainError):
    def __init__(self, rule):
        self.rule = rule

    def __str__(self):
        return str(self.rule)


class DiscardedEntityError(Exception):
    """Raised when an attempt is made to use a discarded entity"""
