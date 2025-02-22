import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipe.filter import (
    ApiRecipeFilter,
)
from src.contexts.recipes_catalog.shared.adapters.repositories.recipe.recipe import (
    RecipeRepo,
)
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from tests.recipes_catalog.random_refs import random_recipe
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
            ["key_in:value|another_value_in,another_key_in:value"],
            [
                "key_in:value_not_in|another_value_in,another_key_in:value",
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
                "key_in:value_not_in|another_value_in,another_key_in:value",
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
            for key, value in filters_in["tags"].items():
                for v in value:
                    tags.append((key, v, domain.author_id))
            filters_in["tags"] = tags
        if filter_key == "tags_not_exists":
            tags = []
            for key, value in filters_in["tags_not_exists"].items():
                for v in value:
                    tags.append((key, v, domain.author_id))
            filters_in["tags_not_exists"] = tags
        values_in = await repo.query(filters_in)
        assert len(values_in) == 1
        assert values_in[0] == domain
    for value in filter_values_not_in:
        api_not_in = ApiRecipeFilter(**{filter_key: value})
        filters_not_in = api_not_in.model_dump(exclude_none=True)
        if filter_key == "tags":
            tags = []
            for key, value in filters_not_in["tags"].items():
                for v in value:
                    tags.append((key, v, domain.author_id))
            filters_not_in["tags"] = tags
        if filter_key == "tags_not_exists":
            tags = []
            for key, value in filters_not_in["tags_not_exists"].items():
                for v in value:
                    tags.append((key, v, domain.author_id))
            filters_not_in["tags_not_exists"] = tags
        values_in = await repo.query(filters_not_in)
        assert len(values_in) == 0
