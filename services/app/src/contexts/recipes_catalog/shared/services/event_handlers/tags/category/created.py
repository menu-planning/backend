from src.contexts.recipes_catalog.shared.domain.events import CategoryCreated
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def category_created_place_holder(evt: CategoryCreated, uow: UnitOfWork) -> None:
    pass
