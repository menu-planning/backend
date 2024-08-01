from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.tags.meal_planning import (
    MealPlanningMapper,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.tags import (
    MealPlanningSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.repositories.tags.tag import TagRepo
from src.contexts.recipes_catalog.shared.domain.entities.tags import MealPlanning


class MealPlanningRepo(TagRepo[MealPlanning, MealPlanningSaModel]):
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
