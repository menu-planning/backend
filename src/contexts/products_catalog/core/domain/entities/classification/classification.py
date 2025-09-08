"""Base classification entity for product catalog taxonomy.

Provides common functionality for all classification entities (brands, categories,
food groups, etc.) including creation, updates, and domain event emission.
"""

from abc import abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Self

from src.contexts.products_catalog.core.domain.events.classification.classification_created import (
    ClassificationCreated,
)
from src.contexts.seedwork.domain.entity import Entity

if TYPE_CHECKING:
    from src.contexts.seedwork.domain.event import Event


class Classification(Entity):
    """Base classification entity for product catalog taxonomy.

    Invariants:
        - name must be non-empty
        - author_id must be valid user identifier
        - version increments on each modification

    Attributes:
        name: Classification name (e.g., "Organic", "Dairy")
        author_id: User who created this classification
        description: Optional detailed description
        created_at: Timestamp of creation
        updated_at: Timestamp of last modification

    Notes:
        Allowed transitions: CREATED -> UPDATED -> DELETED
        Use factory methods for creation; direct instantiation not recommended.
    """

    def __init__(
        self,
        *,
        id: str,
        name: str,
        author_id: str,
        description: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Initialize classification entity.

        Args:
            id: Unique identifier for the classification.
            name: Classification name.
            author_id: User who created this classification.
            description: Optional description.
            created_at: Creation timestamp.
            updated_at: Last update timestamp.
            discarded: Whether entity is soft-deleted.
            version: Entity version for optimistic locking.
        """
        super().__init__(id=id, discarded=discarded, version=version)
        self._name = name
        self._author_id = author_id
        self._description = description
        self._created_at = created_at
        self._updated_at = updated_at
        self.events: list[Event] = []

    @classmethod
    def _create_classification(
        cls,
        *,
        name: str,
        author_id: str,
        event_type: type[ClassificationCreated],
        description: str | None = None,
    ) -> Self:
        """Create a new classification entity with domain event.

        Args:
            name: Classification name.
            author_id: User creating the classification.
            event_type: Specific event type to emit.
            description: Optional description.

        Returns:
            New classification instance with creation event.
        """
        event = event_type(
            name=name,
            author_id=author_id,
            description=description,
        )
        classification = cls(
            id=event.classification_id,
            name=event.name,
            author_id=event.author_id,
            description=event.description,
        )
        classification.events.append(event)
        return classification

    @classmethod
    @abstractmethod
    def create_classification[C: "Classification"](
        cls: type[C],
        *,
        name: str,
        author_id: str,
        event_type: type[ClassificationCreated],
        description: str | None = None,
    ) -> C:
        """Abstract factory method for creating classification entities.

        Args:
            name: Classification name.
            author_id: User creating the classification.
            event_type: Specific event type to emit.
            description: Optional description.

        Returns:
            New classification instance.
        """
        pass

    @property
    def name(self) -> str:
        self._check_not_discarded()
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._check_not_discarded()
        if self._name != value:
            self._name = value
            self._increment_version()

    @property
    def author_id(self) -> str:
        self._check_not_discarded()
        return self._author_id

    @property
    def description(self) -> str | None:
        self._check_not_discarded()
        return self._description

    @description.setter
    def description(self, value: str | None) -> None:
        self._check_not_discarded()
        if self._description != value:
            self._description = value
            self._increment_version()

    @property
    def created_at(self) -> datetime | None:
        self._check_not_discarded()
        return self._created_at

    @property
    def updated_at(self) -> datetime | None:
        self._check_not_discarded()
        return self._updated_at

    def delete(self) -> None:
        """Soft delete the classification entity.

        Marks the entity as discarded and increments version.
        Does not physically remove from storage.
        """
        self._check_not_discarded()
        self._discard()
        self._increment_version()

    def __repr__(self) -> str:
        """Return string representation of the classification.

        Returns:
            String containing class name, id, name, and author.
        """
        self._check_not_discarded()
        return (
            f"{self.__class__.__name__}"
            f"(id={self.id!r}, name={self.name!r}, author={self.author_id!r})"
        )

    def __hash__(self) -> int:
        """Return hash based on entity ID.

        Returns:
            Hash of the entity ID.
        """
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        """Check equality based on entity ID.

        Args:
            other: Object to compare with.

        Returns:
            True if other is a Classification with same ID.
        """
        if not isinstance(other, Classification):
            return NotImplemented
        return self.id == other.id

    def _update_properties(self, **kwargs) -> None:
        """Update multiple properties atomically.

        Args:
            **kwargs: Property names and values to update.
        """
        self._check_not_discarded()
        super()._update_properties(**kwargs)

    def update_properties(self, **kwargs) -> None:
        """Update multiple properties atomically.

        Args:
            **kwargs: Property names and values to update.
        """
        self._check_not_discarded()
        self._update_properties(**kwargs)
