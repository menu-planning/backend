from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import (
        SaGenericRepository,
    )

RepositoryType: TypeAlias = "SaGenericRepository"

class FilterNotAllowedError(Exception):
    """Raised when an attempt to filter by a field is made that is not allowed."""


class RepositoryError[R: RepositoryType](Exception):
    def __init__(self, message: str, entity_id: str, repository: R) -> None:
        super().__init__(message)
        self.message = message
        self.entity_id = entity_id
        self.repository = repository


class EntityNotFoundError[R: RepositoryType](RepositoryError[R]):
    def __init__(self, entity_id: str, repository: R):
        msg = f"Entity {entity_id} not found on repository {repository}"
        super().__init__(msg, entity_id, repository)


class MultipleEntitiesFoundError[R: RepositoryType](RepositoryError[R]):
    def __init__(self, entity_id: str, repository: R):
        msg = f"Entity {entity_id} already exists on repository {repository}"
        super().__init__(msg, entity_id, repository)
