from dataclasses import asdict as dataclass_asdict

from attrs import asdict as attrs_asdict
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts import (
    NutriFactsSaModel,
)
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


class NutriFactsMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(
        domain_obj: NutriFacts | None,
    ) -> NutriFactsSaModel:
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
        except:
            return NutriFacts(**dataclass_asdict(sa_obj))
