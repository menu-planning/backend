from src.contexts.recipes_catalog.shared.domain.commands.tag.delete import DeleteTag
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def delete_recipe_tag(cmd: DeleteTag, uow: UnitOfWork) -> None:
    async with uow:
        await uow.recipe_tags.delete_recipe_tag(cmd.id)
        await uow.commit()
