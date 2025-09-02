from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.seedwork.domain.entity import Entity
from src.db.base import SaBase


class ModelMapper[E: Entity, S: SaBase](Protocol):
    """Protocol for mapping between domain entities and SQLAlchemy models.

    This protocol defines the interface for bidirectional mapping between domain
    layer entities and persistence layer SQLAlchemy models. It ensures consistent
    behavior across all mapper implementations and provides type safety through
    generic type parameters.

    Type Parameters:
        E: Domain entity type that inherits from Entity
        S: SQLAlchemy model type that inherits from SaBase

    Key Responsibilities:
        - Convert domain entities to ORM models for persistence
        - Convert ORM models to domain entities for business logic
        - Handle complex relationships and nested object mapping
        - Maintain data integrity during conversions
        - Provide clear error messages for mapping failures

    Usage:
        ```python
        class UserMapper(ModelMapper[User, UserSaModel]):
            @staticmethod
            async def map_domain_to_sa(session, domain_obj, **kwargs):
                # Implementation for domain → ORM conversion
                pass

            @staticmethod
            def map_sa_to_domain(sa_obj):
                # Implementation for ORM → domain conversion
                pass
        ```
    """

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: E, **kwargs: object
    ) -> S:
        """Map domain entity to SQLAlchemy model.

        This method converts a domain entity to its corresponding ORM model
        for persistence operations. It may require database queries to resolve
        relationships and ensure referential integrity.

        Args:
            session: Database session for any required queries or relationship
                resolution
            domain_obj: Domain entity to convert
            **kwargs: Additional mapping parameters (e.g., update vs. create flags)

        Returns:
            SQLAlchemy model instance ready for persistence

        Raises:
            EntityMappingError: If mapping fails due to invalid data or
                relationship issues
            ValueError: If required domain data is missing or invalid
        """
        ...

    @staticmethod
    def map_sa_to_domain(sa_obj: S) -> E:
        """Map SQLAlchemy model to domain entity.

        This method converts an ORM model to its corresponding domain entity
        for use in business logic. It handles type conversions and ensures
        domain invariants are maintained.

        Args:
            sa_obj: SQLAlchemy model instance to convert

        Returns:
            Domain entity instance with all business rules enforced

        Raises:
            EntityMappingError: If mapping fails due to invalid ORM data
            ValueError: If ORM data violates domain constraints
        """
        ...
