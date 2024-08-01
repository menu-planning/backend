from src.contexts.seedwork.shared.domain.exceptions import DomainException


class BusinessRuleValidationException(DomainException):
    def __init__(self, rule):
        self.rule = rule

    def __str__(self):
        return str(self.rule)


class DiscardedEntityException(Exception):
    """Raised when an attempt is made to use a discarded entity"""
