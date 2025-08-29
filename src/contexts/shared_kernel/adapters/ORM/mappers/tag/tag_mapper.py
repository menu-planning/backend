from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.seedwork.shared import utils
from src.contexts.seedwork.shared.adapters.ORM.mappers.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class TagMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: Tag) -> TagSaModel:
        tag_on_db = await utils.get_sa_entity(
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
        return Tag(
            key=sa_obj.key,
            value=sa_obj.value,
            author_id=sa_obj.author_id,
            type=sa_obj.type,
        )
