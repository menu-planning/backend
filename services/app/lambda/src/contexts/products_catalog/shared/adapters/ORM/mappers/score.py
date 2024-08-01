from dataclasses import asdict as dataclass_asdict

from src.contexts.products_catalog.shared.adapters.ORM.sa_models.product import (
    ScoreSaModel,
)
from src.contexts.products_catalog.shared.domain.value_objects.score import Score
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper


class ScoreMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: Score | None) -> ScoreSaModel:
        return (
            ScoreSaModel(
                final_score=domain_obj.final,
                ingredients_score=domain_obj.ingredients,
                nutrients_score=domain_obj.nutrients,
            )
            if domain_obj
            else ScoreSaModel()
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: ScoreSaModel) -> Score | None:
        scores = set(dataclass_asdict(sa_obj).values())
        return (
            Score(
                final=sa_obj.final_score,
                ingredients=sa_obj.ingredients_score,
                nutrients=sa_obj.nutrients_score,
            )
            if scores != {None}
            else None
        )
