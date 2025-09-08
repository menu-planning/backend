"""Mapper between classification `Source` and `SourceSaModel`."""

from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.sa_models.source import (
    SourceSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification.source import (
    Source,
)
from src.contexts.seedwork.adapters.ORM.mappers import helpers
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper


class SourceMapper(ModelMapper):
    """Map Source domain entity to/from SourceSaModel."""

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Source
    ) -> SourceSaModel:
        """Map domain Source to existing SQLAlchemy SourceSaModel.

        Args:
            session: Database session.
            domain_obj: Domain Source object.

        Returns:
            Existing SourceSaModel instance from database.
        """
        existing_sa_obj = await helpers.get_sa_entity(
            session=session,
            sa_model_type=SourceSaModel,
            filters={"id": domain_obj.name},
        )
        return existing_sa_obj

    @staticmethod
    def map_sa_to_domain(sa_obj: SourceSaModel) -> Source:
        """Map SQLAlchemy SourceSaModel to domain Source.

        Args:
            sa_obj: SQLAlchemy SourceSaModel instance.

        Returns:
            Domain Source object.
        """
        return Source(
            id=sa_obj.id,
            name=sa_obj.name,
            author_id=sa_obj.author_id,
            description=sa_obj.description,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )
