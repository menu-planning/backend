import src.contexts.seedwork.shared.adapters.utils as utils
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.texture import TextureSaModel
from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture


class TextureMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Texture
    ) -> TextureSaModel:
        """
        Maps a domain object to a SQLAlchemy model object. Since
        the user can only choose a texture from a list of predefined
        textures, we can assume that the texture already exists in
        the database. Therefore, we just need to return the existing
        SQLAlchemy object.

        """
        existing_sa_obj = await utils.get_sa_entity(
            session=session,
            sa_model_type=TextureSaModel,
            filter={"id": domain_obj.name},
        )
        return existing_sa_obj

    @staticmethod
    def map_sa_to_domain(sa_obj: TextureSaModel) -> Texture:
        return Texture(
            name=sa_obj.id,
        )
