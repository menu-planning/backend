"""Mappers for converting Tag between domain and SQLAlchemy models.

This module provides translation between the `Tag` domain value object and the
corresponding SQLAlchemy model `TagSaModel`.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.seedwork.adapters.ORM.mappers import helpers
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class TagMapper(ModelMapper):
    """Mapper between Tag domain object and TagSaModel.

    Notes:
        Adheres to ModelMapper interface. Lossless mapping with proper type conversion.
        Performance: Efficient conversion between domain and ORM representations.
        Transactions: methods require active UnitOfWork session.
    """
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: Tag) -> TagSaModel:
        """Find or create the SQLAlchemy entity that represents a domain tag.

        Args:
            session: Async SQLAlchemy session used for lookup/creation.
            domain_obj: Domain tag to map into the persistence model.

        Returns:
            The existing or newly created `TagSaModel` that matches the domain
            tag fields.
        """
        tag_on_db = await helpers.get_sa_entity(
            session=session,
            sa_model_type=TagSaModel,
            filters={
                "key": domain_obj.key,
                "value": domain_obj.value,
                "author_id": domain_obj.author_id,
                "type": domain_obj.type,
            },
        )
        if tag_on_db is None:
            tag_on_db = TagSaModel(
                key=domain_obj.key,
                value=domain_obj.value,
                author_id=domain_obj.author_id,
                type=domain_obj.type,
            )
        return tag_on_db

    @staticmethod
    def map_sa_to_domain(sa_obj: TagSaModel) -> Tag:
        """Convert a SQLAlchemy tag entity into the domain value object.

        Args:
            sa_obj: SQLAlchemy model instance to convert.

        Returns:
            A `Tag` domain value object with fields copied from the model.
        """
        return Tag(
            key=sa_obj.key,
            value=sa_obj.value,
            author_id=sa_obj.author_id,
            type=sa_obj.type,
        )
