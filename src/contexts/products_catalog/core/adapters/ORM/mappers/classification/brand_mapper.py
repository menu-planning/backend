"""Mapper between classification `Brand` and `BrandSaModel`."""

from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_brand import (
    ApiBrand,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.brand import (
    BrandSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification.brand import (
    Brand,
)
from src.contexts.seedwork.adapters.ORM.mappers import helpers
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper


class BrandMapper(ModelMapper):
    """Map Brand domain entity to/from BrandSaModel."""

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Brand
    ) -> BrandSaModel:
        """Map domain Brand to existing SQLAlchemy BrandSaModel.

        Args:
            session: Database session.
            domain_obj: Domain Brand object.

        Returns:
            Existing BrandSaModel instance from database.
        """
        existing_sa_obj = await helpers.get_sa_entity(
            session=session,
            sa_model_type=BrandSaModel,
            filters={"id": domain_obj.name},
        )
        return existing_sa_obj

    @staticmethod
    def map_sa_to_domain(sa_obj: BrandSaModel) -> Brand:
        """Map SQLAlchemy BrandSaModel to domain Brand.

        Args:
            sa_obj: SQLAlchemy BrandSaModel instance.

        Returns:
            Domain Brand object.
        """
        return Brand(
            id=sa_obj.id,
            name=sa_obj.name,
            author_id=sa_obj.author_id,
            description=sa_obj.description,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )
