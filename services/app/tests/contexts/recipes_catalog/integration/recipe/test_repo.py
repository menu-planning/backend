import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.products_catalog.core.adapters.repositories.product_repository import ProductRepo
from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.recipe.filter import (
    ApiRecipeFilter,
)
from src.contexts.recipes_catalog.core.adapters.repositories.recipe.recipe import (
    RecipeRepo,
)
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from tests.products_catalog.random_refs import random_food_product
from tests.products_catalog.utils import insert_food_product
from tests.recipes_catalog.random_refs import random_attr, random_ingredient, random_recipe
from tests.utils import build_dict_from_instance

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_can_add_recipe_to_repo(
    async_pg_session: AsyncSession,
):
    domain = random_recipe()
    repo = RecipeRepo(async_pg_session)
    await repo.add(domain)
    query = await repo.get(domain.id)
    assert domain == query
    domain_dict = build_dict_from_instance(domain)
    query_dict = build_dict_from_instance(query)
    assert domain_dict.pop("created_at") == None != query_dict.pop("created_at")
    assert domain_dict.pop("updated_at") == None != query_dict.pop("updated_at")
    assert domain_dict == query_dict


async def test_new_tags_are_persisted(
    async_pg_session: AsyncSession,
):
    domain = random_recipe()
    repo = RecipeRepo(async_pg_session)
    await repo.add(domain)
    query = await repo.get(domain.id)
    assert domain == query
    assert len(domain.tags) == 1
    assert domain.tags.pop() == query.tags.pop()


@pytest.mark.parametrize(
    "attribute_value,filter_key,filter_values_in,filter_values_not_in",
    [
        (100, "total_time_lte", [100], [99]),
        (100, "total_time_gte", [100], [101]),
        (Privacy.PRIVATE, "privacy", ["private"], ["public"]),
        (
            set(
                [
                    Tag(
                        key="key_in",
                        value="value",
                        author_id="author_id",
                        type="recipe",
                    ),
                    Tag(
                        key="key_in",
                        value="another_value_in",
                        author_id="author_id",
                        type="recipe",
                    ),
                    Tag(
                        key="another_key_in",
                        value="value",
                        author_id="author_id",
                        type="recipe",
                    ),
                    Tag(
                        key="another_key_in",
                        value="another_value",
                        author_id="author_id",
                        type="recipe",
                    ),
                ]
            ),
            "tags",
            ["key_in:value|key_in:another_value_in|another_key_in:value"],
            [
                "key_in:value_not_in|key_in:another_value_not_in|another_key_in:value",
                "key_not_in:value",
            ],
        ),
        (
            set(
                [
                    Tag(
                        key="key_in",
                        value="value",
                        author_id="author_id",
                        type="recipe",
                    ),
                    Tag(
                        key="key_in",
                        value="another_value_in",
                        author_id="author_id",
                        type="recipe",
                    ),
                    Tag(
                        key="another_key_in",
                        value="value",
                        author_id="author_id",
                        type="recipe",
                    ),
                    Tag(
                        key="another_key_in",
                        value="another_value",
                        author_id="author_id",
                        type="recipe",
                    ),
                ]
            ),
            "tags_not_exists",
            ["key_not_in:value"],
            [
                "key_in:value_not_in|key_in:another_value_in|another_key_in:value",
                "another_key_in:value",
            ],
        ),
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
    kwargs = {
        filter_key.replace("_lte", "")
        .replace("_gte", "")
        .replace("_not_exists", ""): attribute_value,
        "author_id": "author_id",
    }
    domain = random_recipe(**kwargs)
    # setattr(domain, filter_key.replace("_lte", "").replace("_gte", ""), attribute_value)
    await repo.add(domain)
    for value in filter_values_in:
        api_in = ApiRecipeFilter(**{filter_key: value})
        filters_in = api_in.model_dump(exclude_none=True)
        if filter_key == "tags":
            tags = []
            for t in filters_in["tags"]:
                tags.append((t[0], t[1], domain.author_id))
            filters_in["tags"] = tags
        if filter_key == "tags_not_exists":
            tags = []
            for t in filters_in["tags_not_exists"]:
                tags.append((t[0], t[1], domain.author_id))
            filters_in["tags_not_exists"] = tags
        values_in = await repo.query(filters_in)
        assert len(values_in) == 1
        assert values_in[0] == domain
    for value in filter_values_not_in:
        api_not_in = ApiRecipeFilter(**{filter_key: value})
        filters_not_in = api_not_in.model_dump(exclude_none=True)
        if filter_key == "tags":
            tags = []
            for t in filters_not_in["tags"]:
                tags.append((t[0], t[1], domain.author_id))
            filters_not_in["tags"] = tags
        if filter_key == "tags_not_exists":
            tags = []
            for t in filters_not_in["tags_not_exists"]:
                tags.append((t[0], t[1], domain.author_id))
            filters_not_in["tags_not_exists"] = tags
        values_in = await repo.query(filters_not_in)
        assert len(values_in) == 0

async def test_can_replace_ingredients(
    async_pg_session
    ):
        domain_instance = random_recipe()
        repo = RecipeRepo(async_pg_session)
        await repo.add(domain_instance)
        await async_pg_session.commit()
        domain_instance = await repo.get(domain_instance.id)
        assert len(domain_instance.ingredients) == 3
        new_ingredient = random_ingredient()
        domain_instance.update_properties(
            ingredients=[
               new_ingredient
            ]
        )
        await repo.persist(domain_instance)
        await async_pg_session.commit()
        domain_instance = await repo.get(domain_instance.id)
        assert len(domain_instance.ingredients) == 1
        assert domain_instance.ingredients[0] == new_ingredient

async def test_querying_on_relationship_do_NOT_duplicate_row(clean_async_pg_session: AsyncSession):
    product1_id = random_attr("id")
    await insert_food_product(clean_async_pg_session, product1_id)
    product2_id = random_attr("id")
    await insert_food_product(clean_async_pg_session, product2_id)
    recipe = random_recipe(
        name="recipe1",
        ingredients=[
            random_ingredient(position=0, product_id=product1_id),
            random_ingredient(position=1, product_id=product2_id),
        ]
    )
    recipe_repo = RecipeRepo(clean_async_pg_session)
    await recipe_repo._generic_repo.add(recipe)
    await clean_async_pg_session.commit()
    recipes = await recipe_repo.query()
    assert len(recipes) == 1
    recipes = await recipe_repo.query({"products": [product1_id, product2_id],"name": "recipe1"})
    assert len(recipes) == 1
    