import src.contexts.seedwork.shared.adapters.utils as utils
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.source import (
    SourceSaModel,
)
from src.contexts.products_catalog.shared.domain.entities.classification import Source
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper


class SourceMapper(ModelMapper):

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Source
    ) -> SourceSaModel:
        """
        Maps a domain object to a SQLAlchemy model object. Since
        the user can only choose a source from a list of predefined
        sources, we can assume that the source already exists in
        the database. Therefore, we just need to return the existing
        SQLAlchemy object.

        """
        existing_sa_obj = await utils.get_sa_entity(
            session=session,
            sa_model_type=SourceSaModel,
            filter={"id": domain_obj.name},
        )
        return existing_sa_obj

    @staticmethod
    def map_sa_to_domain(sa_obj: SourceSaModel) -> Source:
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
