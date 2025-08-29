from typing import Protocol, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.seedwork.shared.domain.entity import Entity
from src.db.base import SaBase

E = TypeVar("E", bound=Entity)
S = TypeVar("S", bound=SaBase)


class ModelMapper(Protocol[E, S]):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: E, **kwargs: object
    ) -> S: ...

    @staticmethod
    def map_sa_to_domain(sa_obj: S) -> E: ...
