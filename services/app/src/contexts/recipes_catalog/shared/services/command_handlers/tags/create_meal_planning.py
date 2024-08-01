from attrs import asdict
from src.contexts.recipes_catalog.shared.domain.commands import CreateMealPlanning
from src.contexts.recipes_catalog.shared.domain.entities.tags import MealPlanning
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def create_meal_planning(cmd: CreateMealPlanning, uow: UnitOfWork) -> None:
    async with uow:
        tag = MealPlanning.create_tag(**asdict(cmd, recurse=False))
        await uow.meal_plannings.add(tag)
        await uow.commit()
