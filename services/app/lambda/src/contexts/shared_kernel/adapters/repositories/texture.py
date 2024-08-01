from typing import Any

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)
from src.contexts.shared_kernel.adapters.ORM.mappers.texture import TextureMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.texture import TextureSaModel
from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture


class TextureRepo(CompositeRepository[Texture, TextureSaModel]):
    def __init__(
        self,
        db_session: AsyncSession,
    ):
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=TextureMapper,
            domain_model_type=Texture,
            sa_model_type=TextureSaModel,
            filter_to_column_mappers=[
                FilterColumnMapper(
                    sa_model_type=TextureSaModel,
                    filter_key_to_column_name={
                        "name": "id",
                    },
                ),
            ],
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Texture):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Texture:
        model_obj = await self._generic_repo.get(id)
        return model_obj

    async def get_sa_instance(self, id: str) -> TextureSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
    ) -> list[Texture]:
        model_objs: list[self.domain_model_type] = await self._generic_repo.query(
            filter=filter, starting_stmt=starting_stmt
        )
        return model_objs

    async def persist(self, domain_obj: Texture) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self) -> None:
        await self._generic_repo.persist_all()
