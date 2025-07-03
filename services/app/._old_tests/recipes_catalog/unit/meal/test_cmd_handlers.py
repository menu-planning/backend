from copy import deepcopy
import pytest
from typing import Any, Protocol, TypeVar

from src.contexts.recipes_catalog.core.domain.commands.commands.copy_meal import CopyMeal
from src.contexts.recipes_catalog.core.domain.commands.commands.create_meal import CreateMeal
from src.contexts.recipes_catalog.core.domain.commands.commands.delete_meal import DeleteMeal
from src.contexts.recipes_catalog.core.domain.commands.commands.update_meal import UpdateMeal
from src.contexts.recipes_catalog.core.domain.commands.recipe.copy_recipe import CopyRecipe
from src.contexts.recipes_catalog.core.domain.commands.recipe.create_recipe import CreateRecipe
from src.contexts.recipes_catalog.core.domain.commands.recipe.delete_recipe import DeleteRecipe
from src.contexts.recipes_catalog.core.domain.commands.recipe.update_recipe import UpdateRecipe
from src.contexts.recipes_catalog.core.domain.entities.meal import Meal
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from tests.recipes_catalog.random_refs import (
    random_create_meal_cmd_kwargs,
    random_create_recipe_classmethod_kwargs,
    random_create_recipe_cmd_kwargs,
    random_recipe,
    random_user,
)
from tests.recipes_catalog.unit.fakes import FakeUnitOfWork
from src.contexts.recipes_catalog.core.services.command_handlers.meal.create_meal import create_meal_handler
from src.contexts.recipes_catalog.core.services.command_handlers.meal.delete_meal import delete_meal_handler
from src.contexts.recipes_catalog.core.services.command_handlers.meal.update_meal import update_meal_handler
from src.contexts.recipes_catalog.core.services.command_handlers.meal.copy_meal import copy_meal_handler
from src.contexts.recipes_catalog.core.services.command_handlers.meal.recipe.create_recipe import create_recipe_handler
from src.contexts.recipes_catalog.core.services.command_handlers.meal.recipe.copy_recipe import copy_recipe_handler
from src.contexts.recipes_catalog.core.services.command_handlers.meal.recipe.delete_recipe import delete_recipe_handler
from src.contexts.recipes_catalog.core.services.command_handlers.meal.recipe.update_recipe import update_recipe_handler

pytestmark = pytest.mark.anyio


async def test_can_create_meal_handler():
    uow = FakeUnitOfWork()
    kwargs = random_create_meal_cmd_kwargs()
    cmd = CreateMeal(**kwargs)
    
    async with uow:
        meal = await uow.meals.query()
        assert len(meal) == 0
    
    await create_meal_handler(cmd, uow)
    
    async with uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.name == cmd.name
        assert uow.committed


async def test_can_delete_meal_handler():
    uow = FakeUnitOfWork()
    kwargs = random_create_meal_cmd_kwargs()
    cmd = CreateMeal(**kwargs)
    
    async with uow:
        meal = await uow.meals.query()
        assert len(meal) == 0
    
    await create_meal_handler(cmd, uow)
    
    async with uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.name == cmd.name
        assert uow.committed
    
    delete_cmd = DeleteMeal(meal_id=meal.id)
    await delete_meal_handler(delete_cmd, uow)
    
    async with uow:
        query = await uow.meals.query()
        assert len(query) == 0
        assert uow.committed


async def test_can_add_recipe_to_meal_handler():
    uow = FakeUnitOfWork()
    kwargs = random_create_meal_cmd_kwargs(recipes=[])
    cmd = CreateMeal(**kwargs)
    
    async with uow:
        meal = await uow.meals.query()
        assert len(meal) == 0
    
    await create_meal_handler(cmd, uow)
    
    async with uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.name == cmd.name
        assert len(meal.recipes) == 0
        assert uow.committed
    
    create_recipe_cmd = CreateRecipe(**random_create_recipe_classmethod_kwargs(**kwargs))
    await create_recipe_handler(create_recipe_cmd, uow)
    
    async with uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert len(meal.recipes) == 1
        assert uow.committed


async def test_can_copy_and_existing_recipe_to_meal():
    uow = FakeUnitOfWork()
    kwargs = random_create_meal_cmd_kwargs(recipes=[])
    cmd = CreateMeal(**kwargs)
    
    async with uow:
        meal = await uow.meals.query()
        assert len(meal) == 0
    
    await create_meal_handler(cmd, uow)
    
    async with uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.name == cmd.name
        assert len(meal.recipes) == 0
        assert uow.committed
    
    recipe = random_recipe()
    async with uow:
        await uow.recipes.add(recipe)
        assert uow.committed
    
    copy_existing_recipe_cmd = CopyRecipe(user_id=meal.author_id, meal_id=meal.id, recipe_id=recipe.id)
    await copy_recipe_handler(copy_existing_recipe_cmd, uow)
    
    async with uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert len(meal.recipes) == 1
        assert meal.recipes[0].meal_id == meal.id != recipe.meal_id
        assert meal.recipes[0].author_id == meal.author_id != recipe.author_id


async def test_can_copy_an_meal():
    uow = FakeUnitOfWork()
    kwargs = random_create_meal_cmd_kwargs(recipes=[])
    cmd = CreateMeal(**kwargs)
    
    async with uow:
        meal = await uow.meals.query()
        assert len(meal) == 0
    
    await create_meal_handler(cmd, uow)
    
    async with uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.name == cmd.name
        assert len(meal.recipes) == 0
        assert uow.committed
    
    copy_cmd = CopyMeal(
        id_of_user_coping_meal="new_user",
        meal_id=meal.id,
    )
    await copy_meal_handler(copy_cmd, uow)
    
    async with uow:
        query = await uow.meals.query()
        assert len(query) == 2
        assert query[0].name == query[1].name
        assert query[0].author_id != query[1].author_id
        assert query[0].id != query[1].id


class TestUpdateMealHandler:
    async def test_happy_update_meal_handler(self):
        uow = FakeUnitOfWork()
        create_kwargs = random_create_meal_cmd_kwargs()
        cmd = CreateMeal(**create_kwargs)
        
        async with uow:
            meal = await uow.meals.query()
            assert len(meal) == 0
        
        await create_meal_handler(cmd, uow)
        
        async with uow:
            query = await uow.meals.query(
                {"name": cmd.name, "author_id": cmd.author_id}
            )
            meal = query[0]
            assert meal is not None
            assert uow.committed
        
        meal = deepcopy(meal)
        update_kwargs = random_create_meal_cmd_kwargs(
            author_id=cmd.author_id,
            recipes=[random_recipe(author_id=cmd.author_id, meal_id=meal.id)],
        )
        update_kwargs.pop("author_id")
        update_cmd = UpdateMeal(meal_id=meal.id, updates=update_kwargs)
        await update_meal_handler(update_cmd, uow)
        
        async with uow:
            query = await uow.meals.query(
                {"name": update_cmd.updates["name"], "author_id": cmd.author_id}
            )
            updated_meal: Meal = query[0]
            assert meal == updated_meal
            
            for k, v in update_cmd.updates.items():
                if k == "recipes":
                    continue
                else:
                    assert getattr(updated_meal, k) == v
                    assert getattr(meal, k) == create_kwargs[k]
                    if k != "menu_id":
                        assert create_kwargs[k] != v
            
            for recipe in update_cmd.updates.get("recipes", []):
                assert recipe.name in [r.name for r in updated_meal.recipes]
                assert recipe.author_id == updated_meal.author_id
                for tag in recipe.tags:
                    assert tag in updated_meal.recipes_tags
            
            for recipe in create_kwargs.get("recipes", []):
                assert recipe.name in [r.name for r in meal.recipes]
                assert recipe.author_id == meal.author_id
                for tag in recipe.tags:
                    assert tag in meal.recipes_tags
                    assert tag not in updated_meal.recipes_tags

    async def test_canNOT_change_meal_author(self):
        uow = FakeUnitOfWork()
        kwargs = random_create_meal_cmd_kwargs()
        cmd = CreateMeal(**kwargs)
        
        async with uow:
            meal = await uow.meals.query()
            assert len(meal) == 0
        
        await create_meal_handler(cmd, uow)
        
        async with uow:
            query = await uow.meals.query(
                {"name": cmd.name, "author_id": cmd.author_id}
            )
            meal = query[0]
            assert meal is not None
            assert uow.committed
        
        new_author = random_user()
        update_cmd = UpdateMeal(meal_id=meal.id, updates={"author_id": new_author.id})
        with pytest.raises(AttributeError):
            await update_meal_handler(update_cmd, uow)


async def test_can_remove_a_recipe_from_a_meal():
    uow = FakeUnitOfWork()
    kwargs = random_create_meal_cmd_kwargs(recipes=[])
    cmd = CreateMeal(**kwargs)
    
    async with uow:
        meal = await uow.meals.query({"name": cmd.name, "author_id": cmd.author_id})
        assert len(meal) == 0
    
    await create_meal_handler(cmd, uow)
    
    async with uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.name == cmd.name
        assert len(meal.recipes) == 0
        assert uow.committed
    
    kwargs = random_create_recipe_cmd_kwargs(
        author_id=meal.author_id, meal_id=meal.id
    )
    add_recipe_cmd = CreateRecipe(**kwargs)
    await create_recipe_handler(add_recipe_cmd, uow)
    
    async with uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert len(meal.recipes) == 1
        recipe_id = meal.recipes[0].id
        assert uow.committed
    
    remove_recipe_cmd = DeleteRecipe(recipe_id=recipe_id)
    await delete_recipe_handler(remove_recipe_cmd, uow)
    
    async with uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert len(meal.recipes) == 0
        assert uow.committed


async def test_can_update_a_recipe_on_a_meal():
    uow = FakeUnitOfWork()
    kwargs = random_create_meal_cmd_kwargs()
    cmd = CreateMeal(**kwargs)
    
    async with uow:
        meal = await uow.meals.query()
        assert len(meal) == 0
    
    await create_meal_handler(cmd, uow)
    
    async with uow:
        query = await uow.meals.query()
        assert len(query) == 1
        meal = query[0]
        assert meal is not None
        assert meal.name == cmd.name
        assert len(meal.recipes) == 3
        assert uow.committed
    
    recipe = deepcopy(meal.recipes[0])
    update_kwargs = random_create_recipe_cmd_kwargs(author_id=meal.author_id)
    update_kwargs.pop("author_id")
    update_kwargs.pop("meal_id")
    update_cmd = UpdateRecipe(
        recipe_id=recipe.id, updates={recipe.id: update_kwargs}
    )
    await update_recipe_handler(update_cmd, uow)
    
    async with uow:
        query = await uow.meals.query()
        updated_meal: Meal = query[0]
        for r in updated_meal.recipes:
            if r.id == recipe.id:
                for k, v in update_cmd.updates[r.id].items():
                    assert getattr(r, k) == v
