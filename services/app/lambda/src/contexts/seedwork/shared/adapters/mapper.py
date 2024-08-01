from typing import Protocol

from src.contexts.seedwork.shared.domain.entitie import Entity
from src.db.base import SaBase


class ModelMapper(Protocol):
    @staticmethod
    def map_domain_to_sa(self, domain_obj: Entity) -> SaBase: ...

    @staticmethod
    def map_sa_to_domain(self, sa_obj: SaBase) -> Entity: ...
