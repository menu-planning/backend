"""Command to update product attributes atomically."""
from typing import Any

from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen
class UpdateProduct(Command):
    """Command to update product attributes atomically.
    
    Attributes:
        product_id: Unique identifier of the product to update.
        updates: Dictionary of field names to new values.
    
    Notes:
        Updates product attributes within a single transaction. All updates
        are applied atomically - either all succeed or all fail.
    """
    product_id: str
    updates: dict[str, Any]
