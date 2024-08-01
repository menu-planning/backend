from src.contexts.recipes_catalog.shared.domain.events.recipes.created import (
    RecipeCreated,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def recipe_created_place_holder(evt: RecipeCreated, uow: UnitOfWork) -> None:
    pass
