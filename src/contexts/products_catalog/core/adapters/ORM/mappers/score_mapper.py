from dataclasses import asdict as dataclass_asdict

from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.sa_models.product import (
    ScoreSaModel,
)
from src.contexts.products_catalog.core.domain.value_objects.score import Score
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper


class ScoreMapper(ModelMapper):
    """Map Score value object to/from ScoreSaModel dataclass."""

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Score | None
    ) -> ScoreSaModel:
        """Map domain Score to SQLAlchemy ScoreSaModel.

        Args:
            session: Database session (unused for this mapper).
            domain_obj: Domain Score object or None.

        Returns:
            ScoreSaModel instance or empty instance if domain_obj is None.
        """
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
        """Map SQLAlchemy ScoreSaModel to domain Score.

        Args:
            sa_obj: SQLAlchemy ScoreSaModel instance.

        Returns:
            Domain Score object or None if all scores are None.
        """
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
