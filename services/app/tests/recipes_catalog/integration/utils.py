from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.recipes_catalog.shared.adapters.repositories.tags.category import (
    CategoryRepo,
)
from src.contexts.recipes_catalog.shared.adapters.repositories.tags.meal_planning import (
    MealPlanningRepo,
)
from src.contexts.recipes_catalog.shared.domain.entities.tags import (
    Category,
    MealPlanning,
)
from src.contexts.shared_kernel.adapters.repositories.allergen import AllergenRepo
from src.contexts.shared_kernel.adapters.repositories.cuisine import CuisineRepo
from src.contexts.shared_kernel.adapters.repositories.diet_type import DietTypeRepo
from src.contexts.shared_kernel.adapters.repositories.flavor import FlavorRepo
from src.contexts.shared_kernel.adapters.repositories.texture import TextureRepo
from src.contexts.shared_kernel.domain.entities.diet_type import DietType
from src.contexts.shared_kernel.domain.value_objects.name_tag.allergen import Allergen
from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine
from src.contexts.shared_kernel.domain.value_objects.name_tag.flavor import Flavor
from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture
from tests.recipes_catalog.random_refs import (
    CategoryRandomEnum,
    CuisineRandomEnum,
    DietTypeRandomEnum,
    FlavorRandomEnum,
    MealPlanningRandomEnum,
    TextureRandomEnum,
    random_recipe,
    random_tag_id,
    random_user,
)


async def insert_recipe_foreign_keys(
    async_pg_session: AsyncSession,
    *,
    diet_type_names: list[str] = None,
    category_names: list[str] = None,
    cuisine_name: str = None,
    flavor_name: str = None,
    texture_name: str = None,
    meal_planning_names: list[str] = None,
    allergens_names: list[str] = None,
):
    diet_type_repo = DietTypeRepo(async_pg_session)
    category_repo = CategoryRepo(async_pg_session)
    cuisine_repo = CuisineRepo(async_pg_session)
    flavor_repo = FlavorRepo(async_pg_session)
    texture_repo = TextureRepo(async_pg_session)
    meal_planning_repo = MealPlanningRepo(async_pg_session)
    allergen_repo = AllergenRepo(async_pg_session)
    user = random_user()
    try:
        diets = (
            [DietType.create(name=name, author_id=user.id) for name in diet_type_names]
            if diet_type_names
            else [
                DietType.create(
                    name=random_tag_id(DietTypeRandomEnum), author_id=user.id
                )
            ]
        )
        for diet in diets:
            await diet_type_repo.add(diet)
    except TypeError:
        diets = DietType.create(name=diet_type_names, author_id=user.id)
        await diet_type_repo.add(diets)
    try:
        categories = (
            [
                Category.create_tag(name=name, author_id=user.id)
                for name in category_names
            ]
            if category_names
            else [
                Category.create_tag(
                    name=random_tag_id(CategoryRandomEnum), author_id=user.id
                )
            ]
        )
        for category in categories:
            await category_repo.add(category)
    except TypeError:
        categories = Category.create_tag(name=category_names, author_id=user.id)
        await category_repo.add(categories)
    cuisine = Cuisine(
        name=cuisine_name if cuisine_name else random_tag_id(CuisineRandomEnum)
    )
    await cuisine_repo.add(cuisine)
    flavor_profile = Flavor(
        name=flavor_name if flavor_name else random_tag_id(FlavorRandomEnum)
    )
    await flavor_repo.add(flavor_profile)
    texture_profile = Texture(
        name=texture_name if texture_name else random_tag_id(TextureRandomEnum)
    )
    await texture_repo.add(texture_profile)
    try:
        meal_planning = (
            [
                MealPlanning.create_tag(name=name, author_id=user.id)
                for name in meal_planning_names
            ]
            if meal_planning_names
            else [
                MealPlanning.create_tag(
                    name=random_tag_id(MealPlanningRandomEnum), author_id=user.id
                )
            ]
        )
        for meal in meal_planning:
            await meal_planning_repo.add(meal)
    except TypeError:
        meal_planning = MealPlanning.create_tag(
            name=meal_planning_names, author_id=user.id
        )
        await meal_planning_repo.add(meal_planning)
    allergens = []
    if allergens_names:
        for name in allergens_names:
            allergen = Allergen(name=name)
            await allergen_repo.add(allergen)
            allergens.append(allergen)
    # else:
    #     for _ in range(3):
    #         allergen = Allergen(name=random_tag_id(AllergenRandomEnum))
    #         await allergen_repo.add(allergen)
    #         allergens.append(allergen)
    return {
        "diet_types": diets,
        "categories": categories,
        "cuisine": cuisine,
        "flavor": flavor_profile,
        "texture": texture_profile,
        "meal_planning": meal_planning,
        "allergens": allergens,
    }


async def recipe_with_foreign_keys_added_to_db(
    async_pg_session: AsyncSession,
    *,
    diet_types_names: list[str] = None,
    categories_names: list[str] = None,
    cuisine_name: str = None,
    flavor_name: str = None,
    texture_name: str = None,
    meal_planning_names: list[str] = None,
    allergens_names: list[str] = None,
):
    foreign_keys = await insert_recipe_foreign_keys(
        async_pg_session=async_pg_session,
        diet_type_names=diet_types_names,
        category_names=categories_names,
        cuisine_name=cuisine_name,
        flavor_name=flavor_name,
        texture_name=texture_name,
        meal_planning_names=meal_planning_names,
        allergens_names=allergens_names,
    )
    recipe = random_recipe(
        ratings=[],
        diet_types_ids=set([i.id for i in foreign_keys["diet_types"]]),
        categories_ids=set([i.id for i in foreign_keys["categories"]]),
        cuisine=foreign_keys["cuisine"],
        flavor=foreign_keys["flavor"],
        texture=foreign_keys["texture"],
        meal_planning_ids=set([i.id for i in foreign_keys["meal_planning"]]),
        allergens=set(foreign_keys["allergens"]),
    )
    return recipe
