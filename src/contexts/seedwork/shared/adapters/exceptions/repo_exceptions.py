from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import (
        SaGenericRepository,
    )

    R = TypeVar("R", bound=SaGenericRepository)
else:
    # Fallback at runtime; you will not get bound-checking without the real class,
    # but this keeps your code importable.
    R = TypeVar("R")


class FilterNotAllowedError(Exception):
    """Raised when an attempt to filter by a field is made that is not allowed."""


class RepositoryError(Generic[R], Exception):
    def __init__(self, message: str, entity_id: str, repository: R) -> None:
        super().__init__(message)
        self.message = message
        self.entity_id = entity_id
        self.repository = repository


class EntityNotFoundError(RepositoryError[R]):
    def __init__(self, entity_id: str, repository: R):
        msg = f"Entity {entity_id} not found on repository {repository}"
        super().__init__(msg, entity_id, repository)


class MultipleEntitiesFoundError(RepositoryError[R]):
    def __init__(self, entity_id: str, repository: R):
        msg = f"Entity {entity_id} already exists on repository {repository}"
        super().__init__(msg, entity_id, repository)
