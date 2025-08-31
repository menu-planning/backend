from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.seedwork.shared.domain.entity import Entity
from src.db.base import SaBase


class ModelMapper[E: Entity, S: SaBase](Protocol):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: E, **kwargs: object
    ) -> S: ...

    @staticmethod
    def map_sa_to_domain(sa_obj: S) -> E: ...
