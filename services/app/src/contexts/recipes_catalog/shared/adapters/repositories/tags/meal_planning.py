from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.recipe.tags.meal_planning import (
    MealPlanningMapper,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.tags import (
    MealPlanningSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.repositories.tags.tag import TagRepo
from src.contexts.recipes_catalog.shared.domain.entities.tags import MealPlanning
from src.contexts.seedwork.shared.adapters.repository import FilterColumnMapper


class MealPlanningRepo(TagRepo[MealPlanning, MealPlanningSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=MealPlanningSaModel,
            filter_key_to_column_name={
                "id": "id",
                "name": "name",
                "author_id": "author_id",
                "privacy": "privacy",
            },
        ),
    ]

    def __init__(
        self,
        db_session: AsyncSession,
    ):
        super().__init__(
            db_session=db_session,
            data_mapper=MealPlanningMapper,
            domain_model_type=MealPlanning,
            sa_model_type=MealPlanningSaModel,
        )
