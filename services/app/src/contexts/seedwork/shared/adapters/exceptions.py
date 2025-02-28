from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.contexts.seedwork.shared.adapters.repository import SaGenericRepository


class FilterNotAllowedError(Exception):
    """Raised when an attempt to filter by a field is made that is not allowed."""


class RepositoryException(Exception):
    def __init__(
        self, message: str, entity_id: str, repository: "SaGenericRepository"
    ) -> None:
        super().__init__(message)
        self.message = message
        self.repository = repository
        self.entity_id = entity_id


class EntityNotFoundException(RepositoryException):
    def __init__(self, entity_id: str, repository: "SaGenericRepository"):
        message = f"Entity {entity_id} not found on repository {repository}"
        super().__init__(message, entity_id, repository)


class MultipleEntitiesFoundException(RepositoryException):
    def __init__(self, entity_id: str, repository: "SaGenericRepository"):
        message = f"Entity {entity_id} already exists on repository {repository}"
        super().__init__(message, entity_id, repository)
