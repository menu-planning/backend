import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.recipes_catalog.shared.adapters.repositories.recipe import RecipeRepo
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
from src.contexts.shared_kernel.adapters.repositories.cuisine import CuisineRepo
from src.contexts.shared_kernel.adapters.repositories.diet_type import DietTypeRepo
from src.contexts.shared_kernel.adapters.repositories.flavor import FlavorRepo
from src.contexts.shared_kernel.adapters.repositories.texture import TextureRepo
from src.contexts.shared_kernel.domain.entities.diet_type import DietType
from src.contexts.shared_kernel.domain.enums import Month, Privacy
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

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def insert_recipe_foreign_keys(
    async_pg_session: AsyncSession,
    *,
    diet_type_names: list[str] = None,
    category_names: list[str] = None,
    cuisine_name: str = None,
    flavor_name: str = None,
    texture_name: str = None,
    meal_planning_names: list[str] = None,
):
    diet_type_repo = DietTypeRepo(async_pg_session)
    category_repo = CategoryRepo(async_pg_session)
    cuisine_repo = CuisineRepo(async_pg_session)
    flavor_repo = FlavorRepo(async_pg_session)
    texture_repo = TextureRepo(async_pg_session)
    meal_planning_repo = MealPlanningRepo(async_pg_session)
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
    return {
        "diet_types": diets,
        "categories": categories,
        "cuisine": cuisine,
        "flavor": flavor_profile,
        "texture": texture_profile,
        "meal_planning": meal_planning,
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
):
    foreign_keys = await insert_recipe_foreign_keys(
        async_pg_session=async_pg_session,
        diet_type_names=diet_types_names,
        category_names=categories_names,
        cuisine_name=cuisine_name,
        flavor_name=flavor_name,
        texture_name=texture_name,
        meal_planning_names=meal_planning_names,
    )

    return random_recipe(
        ratings=[],
        diet_types_ids=set([i.id for i in foreign_keys["diet_types"]]),
        categories_ids=set([i.id for i in foreign_keys["categories"]]),
        cuisine=foreign_keys["cuisine"],
        flavor=foreign_keys["flavor"],
        texture=foreign_keys["texture"],
        meal_planning_ids=set([i.id for i in foreign_keys["meal_planning"]]),
    )


async def test_can_add_recipe_to_repo(
    async_pg_session: AsyncSession,
):
    domain = await recipe_with_foreign_keys_added_to_db(async_pg_session)
    repo = RecipeRepo(async_pg_session)
    await repo.add(domain)
    query = await repo.get(domain.id)
    assert domain == query
    assert len(domain.diet_types_ids) == 1
    assert len(domain.categories_ids) == 1
    assert len(domain.meal_planning_ids) == 1
    assert domain.cuisine is not None
    assert domain.flavor is not None
    assert domain.texture is not None


async def test_doesNOT_persist_tags_IDs_if_there_are_no_tags(
    async_pg_session: AsyncSession,
):
    domain = await recipe_with_foreign_keys_added_to_db(async_pg_session)
    repo = RecipeRepo(async_pg_session)
    user = random_user()
    new_dt = DietType.create(name="new_diet_type", author_id=user.id)
    new_category = Category.create_tag(name="new_name", author_id=user.id)
    new_meal_planning = MealPlanning.create_tag(name="new_ml", author_id=user.id)
    domain.add_diet_type_id(new_dt.id)
    domain.add_category_id(new_category.id)
    domain.add_meal_planning_id(new_meal_planning.id)
    await repo.add(domain)
    query = await repo.get(domain.id)
    assert domain == query
    assert len(domain.diet_types_ids) == 2
    assert len(domain.categories_ids) == 2
    assert len(domain.meal_planning_ids) == 2
    assert domain.cuisine is not None
    assert domain.flavor is not None
    assert domain.texture is not None
    assert len(query.diet_types_ids) == 1
    assert len(query.categories_ids) == 1
    assert len(query.meal_planning_ids) == 1


async def test_can_persist_tags_IDs_if_tag_exists(
    async_pg_session: AsyncSession,
):
    domain = await recipe_with_foreign_keys_added_to_db(async_pg_session)
    recipe_repo = RecipeRepo(async_pg_session)
    await recipe_repo.add(domain)
    query = await recipe_repo.get(domain.id)
    assert domain == query
    assert domain.diet_types_ids == query.diet_types_ids
    assert domain.categories_ids == query.categories_ids
    assert domain.meal_planning_ids == query.meal_planning_ids
    assert domain.cuisine == query.cuisine
    assert domain.flavor == query.flavor
    assert domain.texture == query.texture


@pytest.mark.parametrize(
    "attribute,attribute_instance_name",
    [
        ("diet_types_ids", "diet_type_name"),
        ("categories_ids", "category_name"),
        ("meal_planning_ids", "meal_planning_name"),
        ("cuisine", "cuisine_name"),
        ("flavor", "flavor_name"),
        ("texture", "texture_name"),
    ],
)
async def test_query_by_tag(
    async_pg_session: AsyncSession, attribute, attribute_instance_name
):
    target_domain = await recipe_with_foreign_keys_added_to_db(
        async_pg_session,
        diet_types_names=["diet_type_name"],
        categories_names=["category_name"],
        cuisine_name="cuisine_name",
        flavor_name="flavor_name",
        texture_name="texture_name",
        meal_planning_names=["meal_planning_name"],
    )
    domain_not_in = random_recipe(
        ratings=[],
        diet_types_ids=[],
        categories_ids=[],
        cuisine=None,
        flavor=None,
        texture=None,
        meal_planning_ids=[],
    )
    recipe_repo = RecipeRepo(async_pg_session)
    await recipe_repo.add(target_domain)
    await recipe_repo.add(domain_not_in)
    query = await recipe_repo.query(
        {attribute.replace("_ids", "").replace("_id", ""): attribute_instance_name}
    )

    assert len(query) == 1
    assert target_domain == query[0]
    assert getattr(target_domain, attribute) == getattr(query[0], attribute)
    query_all = await recipe_repo.query()
    assert len(query_all) == 2


@pytest.mark.parametrize(
    "attribute_value,filter_key,filter_values_in,filter_values_not_in",
    [
        (100, "total_time_lte", [100], [99]),
        (100, "total_time_gte", [100], [101]),
        (Privacy.PRIVATE, "privacy", ["private"], ["public"]),
        ([Month(1), Month(2)], "season", [1, [1, 2]], [3]),
    ],
)
async def test_can_query(
    async_pg_session: AsyncSession,
    attribute_value,
    filter_key,
    filter_values_in,
    filter_values_not_in,
):
    repo = RecipeRepo(async_pg_session)
    domain = await recipe_with_foreign_keys_added_to_db(async_pg_session)
    setattr(domain, filter_key.replace("_lte", "").replace("_gte", ""), attribute_value)
    await repo.add(domain)
    for value in filter_values_in:
        query = await repo.query({filter_key: value})
        assert len(query) == 1
        assert query[0] == domain
    for value in filter_values_not_in:
        query = await repo.query({filter_key: value})
        assert len(query) == 0
