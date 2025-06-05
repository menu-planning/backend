from copy import deepcopy
import pytest
from src.contexts.recipes_catalog.core.domain.commands import (
    CreateRecipe,
    DeleteRecipe,
    RateRecipe,
    UpdateRecipe,
)
from src.contexts.recipes_catalog.core.services.command_handlers.meal.recipe import (
    create_recipe_handler,
    delete_recipe_handler,
    update_recipe_handler,
    rate_recipe_handler,
)
from src.contexts.recipes_catalog.core.domain.value_objects.rating import Rating
from tests.recipes_catalog.random_refs import (
    random_create_recipe_cmd_kwargs,
    random_user,
)
from tests.recipes_catalog.unit.fakes import FakeUnitOfWork

pytestmark = pytest.mark.anyio


async def test_create_recipe_handler():
    uow = FakeUnitOfWork()
    kwargs = random_create_recipe_cmd_kwargs()
    cmd = CreateRecipe(**kwargs)
    
    async with uow:
        recipe = await uow.recipes.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(recipe) == 0
        
        await create_recipe_handler(cmd, uow) # type: ignore
        
        recipe = await uow.recipes.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(recipe) == 1
        assert recipe[0].name == cmd.name
        assert recipe[0].author_id == cmd.author_id


async def test_delete_recipe_handler():
    uow = FakeUnitOfWork()
    kwargs = random_create_recipe_cmd_kwargs()
    cmd = CreateRecipe(**kwargs)
    
    async with uow:
        await create_recipe_handler(cmd, uow) # type: ignore
        
        recipe = await uow.recipes.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(recipe) == 1
        
        delete_cmd = DeleteRecipe(recipe_id=recipe[0].id)
        await delete_recipe_handler(delete_cmd, uow) # type: ignore
        
        recipe = await uow.recipes.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(recipe) == 0


async def test_rate_a_recipe_handler():
    uow = FakeUnitOfWork()
    kwargs = random_create_recipe_cmd_kwargs()
    cmd = CreateRecipe(**kwargs)
    
    async with uow:
        await create_recipe_handler(cmd, uow) # type: ignore
        
        recipe = await uow.recipes.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(recipe) == 1
        
        rating = Rating(
            user_id=random_user().id,
            recipe_id=recipe[0].id,
            taste=4,
            convenience=5,
            comment="Great recipe!"
        )
        rate_cmd = RateRecipe(rating=rating)
        await rate_recipe_handler(rate_cmd, uow) # type: ignore
        
        recipe = await uow.recipes.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(recipe) == 1
        assert recipe[0].average_taste_rating == 4
        assert recipe[0].average_convenience_rating == 5


class TestUpdateRecipeHandler:
    async def test_update_recipe_handler(self):
        uow = FakeUnitOfWork()
        kwargs = random_create_recipe_cmd_kwargs()
        cmd = CreateRecipe(**kwargs)
        
        async with uow:
            await create_recipe_handler(cmd, uow) # type: ignore
            
            recipe = await uow.recipes.query({"name": cmd.name, "author_id": cmd.author_id})
            assert len(recipe) == 1
            
            update_kwargs = deepcopy(kwargs)
            update_kwargs["name"] = "Updated Name"
            update_cmd = UpdateRecipe(recipe_id=recipe[0].id, **update_kwargs)
            await update_recipe_handler(update_cmd, uow) # type: ignore
            
            recipe = await uow.recipes.query({"name": update_kwargs["name"], "author_id": cmd.author_id})
            assert len(recipe) == 1
            assert recipe[0].name == update_kwargs["name"]
            assert recipe[0].author_id == cmd.author_id
