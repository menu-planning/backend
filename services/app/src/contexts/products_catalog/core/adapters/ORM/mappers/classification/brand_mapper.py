import src.contexts.seedwork.shared.utils as utils
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.sa_models.brand import (
    BrandSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification import Brand
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper


class BrandMapper(ModelMapper):

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Brand
    ) -> BrandSaModel:
        """
        Maps a domain object to a SQLAlchemy model object. Since
        the user can only choose a Brand from a list of predefined
        Brands, we can assume that the Brand already exists in
        the database. Therefore, we just need to return the existing
        SQLAlchemy object.

        """
        existing_sa_obj = await utils.get_sa_entity(
            session=session,
            sa_model_type=BrandSaModel,
            filter={"id": domain_obj.name},
        )
        return existing_sa_obj

    @staticmethod
    def map_sa_to_domain(sa_obj: BrandSaModel) -> Brand:
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
