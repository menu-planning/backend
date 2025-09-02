from typing import Any

from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class CreateClassification(Command):
    """Base command for creating classification entities.
    
    Attributes:
        name: Name of the classification entity.
        author_id: Identifier of the user creating the entity.
        description: Optional description of the classification.
    
    Notes:
        Base class for all classification creation commands (sources, brands,
        categories, food groups, process types, parent categories).
    """
    name: str
    author_id: str
    description: str | None = None


@frozen(kw_only=True)
class DeleteClassification(Command):
    """Base command for deleting classification entities.
    
    Attributes:
        id: Unique identifier of the classification entity to delete.
    
    Notes:
        Base class for all classification deletion commands. Performs
        soft or hard delete based on entity type and business rules.
    """
    id: str


@frozen(kw_only=True)
class UpdateClassification(Command):
    """Base command for updating classification entities.
    
    Attributes:
        id: Unique identifier of the classification entity to update.
        updates: Dictionary of field names to new values.
    
    Notes:
        Base class for all classification update commands. Updates are
        applied atomically within a single transaction.
    """
    id: str
    updates: dict[str, Any]
