import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipes.filter import (
    ApiRecipeFilter,
)
from src.contexts.recipes_catalog.shared.adapters.repositories.recipe.recipe import (
    RecipeRepo,
)
from src.contexts.recipes_catalog.shared.domain.entities.tags import (
    Category,
    MealPlanning,
)
from src.contexts.shared_kernel.domain.entities.diet_type import DietType
from src.contexts.shared_kernel.domain.enums import Month, Privacy
from tests.recipes_catalog.integration.utils import recipe_with_foreign_keys_added_to_db
from tests.recipes_catalog.random_refs import random_user

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_can_add_recipe_to_repo(
    async_pg_session: AsyncSession,
):
    domain = await recipe_with_foreign_keys_added_to_db(
        async_pg_session, allergens_names=["first_allergen", "second_allergen"]
    )
    repo = RecipeRepo(async_pg_session)
    await repo.add(domain)
    query = await repo.get(domain.id)
    assert domain == query
    assert len(query.diet_types_ids) == 1
    assert len(query.categories_ids) == 1
    assert len(query.meal_planning_ids) == 1
    assert len(query.allergens) == 2
    assert query.cuisine is not None
    assert query.flavor is not None
    assert query.texture is not None


async def test_doesNOT_persist_tags_IDs_if_there_are_no_tags(
    async_pg_session: AsyncSession,
):
    domain = await recipe_with_foreign_keys_added_to_db(async_pg_session)
    repo = RecipeRepo(async_pg_session)
    user = random_user()
    new_dt = DietType.create(name="new_diet_type", author_id=user.id)
    new_category = Category.create_tag(name="new_name", author_id=user.id)
    new_meal_planning = MealPlanning.create_tag(name="new_ml", author_id=user.id)
    domain.update_properties(
        diet_types_ids=[i for i in domain.diet_types_ids] + [new_dt.id],
        categories_ids=[i for i in domain.categories_ids] + [new_category.id],
        meal_planning_ids=[i for i in domain.meal_planning_ids]
        + [new_meal_planning.id],
    )
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
    "attribute,filter_key,filter_value",
    [
        ("diet_types_ids", "diet_types", ["diet_type_name", "another_name"]),
        ("categories_ids", "categories", ["category_name", "another_name"]),
        ("meal_planning_ids", "meal_planning", ["meal_planning_name", "another_name"]),
        ("cuisine", "cuisines", ["cuisine_name", "another_name"]),
        ("flavor", "flavors", ["flavor_name", "another_name"]),
        ("texture", "textures", ["texture_name", "another_name"]),
        ("allergens", "allergens_not_exists", ["allergen_name", "another_name"]),
    ],
)
async def test_query_by_tag(
    async_pg_session: AsyncSession, attribute, filter_key, filter_value
):
    target_domain = await recipe_with_foreign_keys_added_to_db(
        async_pg_session,
        diet_types_names=["diet_type_name"],
        categories_names=["category_name"],
        cuisine_name="cuisine_name",
        flavor_name="flavor_name",
        texture_name="texture_name",
        meal_planning_names=["meal_planning_name"],
        # allergen_names=["allergen_name"],
    )
    domain_not_in = await recipe_with_foreign_keys_added_to_db(
        async_pg_session,
        diet_types_names=["diet_type_not_in"],
        categories_names=["category_not_in"],
        cuisine_name="cuisine_not_in",
        flavor_name="flavor_not_in",
        texture_name="texture_not_in",
        meal_planning_names=["meal_planning_not_in"],
        allergens_names=["allergen_name"],
    )

    recipe_repo = RecipeRepo(async_pg_session)
    await recipe_repo.add(target_domain)
    await recipe_repo.add(domain_not_in)
    filter = {filter_key: filter_value}
    query = await recipe_repo.query(filter)

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
        ([Month(1), Month(2)], "season", ["1", ["1", "2"]], ["3"]),
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
        api_in = ApiRecipeFilter(**{filter_key: value})
        filters_in = api_in.model_dump(exclude_none=True)
        values_in = await repo.query(filters_in)
        assert len(values_in) == 1
        assert values_in[0] == domain
    for value in filter_values_not_in:
        api_not_in = ApiRecipeFilter(**{filter_key: value})
        filters_not_in = api_not_in.model_dump(exclude_none=True)
        values_in = await repo.query(filters_not_in)
        assert len(values_in) == 0
