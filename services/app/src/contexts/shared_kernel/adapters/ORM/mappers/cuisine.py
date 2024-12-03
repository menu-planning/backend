import src.contexts.seedwork.shared.adapters.utils as utils
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.cuisine import CuisineSaModel
from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine


class CuisineMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Cuisine
    ) -> CuisineSaModel:
        """
        Maps a domain object to a SQLAlchemy model object. Since
        the user can only choose a cuisine from a list of predefined
        cuisines, we can assume that the cuisine already exists in
        the database. Therefore, we just need to return the existing
        SQLAlchemy object.

        """
        existing_sa_obj = await utils.get_sa_entity(
            session=session,
            sa_model_type=CuisineSaModel,
            filter={"id": domain_obj.name},
        )
        return existing_sa_obj

    @staticmethod
    def map_sa_to_domain(sa_obj: CuisineSaModel) -> Cuisine:
        return Cuisine(
            name=sa_obj.id,
        )
