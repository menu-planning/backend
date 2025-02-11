from src.contexts.recipes_catalog.shared.domain.commands.tags.create import CreateTag
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


async def create_recipe_tag(cmd: CreateTag, uow: UnitOfWork) -> None:
    async with uow:
        tag = Tag(key=cmd.key, value=cmd.value, author_id=cmd.author_id, type="recipe")
        await uow.recipe_tags.add(tag)
        await uow.commit()
