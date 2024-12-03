from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.db.base import SaBase


class ModelMapper(Protocol):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Entity, **kwargs
    ) -> SaBase: ...

    @staticmethod
    def map_sa_to_domain(sa_obj: SaBase) -> Entity: ...
