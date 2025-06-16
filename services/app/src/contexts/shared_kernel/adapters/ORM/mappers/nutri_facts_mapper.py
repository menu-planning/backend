from dataclasses import asdict as dataclass_asdict

from attrs import asdict as attrs_asdict
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.seedwork.shared.adapters.ORM.mappers.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import (
    NutriFactsSaModel,
)
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


class NutriFactsMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession,
        domain_obj: NutriFacts | None,
    ) -> NutriFactsSaModel:
        """
        Maps a domain object to a SQLAlchemy model object. NutriFactsSaModel
        is simple a dataclass that is used for composites attributes so
        it just returns a new instance.

        """
        return (
            NutriFactsSaModel(
                **{k: v["value"] for k, v in attrs_asdict(domain_obj).items()}
            )
            if domain_obj
            else NutriFactsSaModel()
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: NutriFactsSaModel) -> NutriFacts | None:
        try:
            nutri_facts = set(dataclass_asdict(sa_obj).values())
            return (
                NutriFacts(**dataclass_asdict(sa_obj))
                if nutri_facts != {None}
                else None
            )
        except Exception:
            return NutriFacts(**dataclass_asdict(sa_obj))
