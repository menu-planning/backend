import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.meal.filter import \
    ApiMealFilter
from src.contexts.recipes_catalog.core.adapters.repositories.meal.meal import \
    MealRepo
from src.contexts.recipes_catalog.core.adapters.repositories.recipe.recipe import \
    RecipeRepo
from src.contexts.recipes_catalog.core.domain.entities.meal import Meal
from src.contexts.seedwork.shared.adapters.exceptions import \
    EntityNotFoundException
from src.contexts.shared_kernel.adapters.repositories.tags.tag_repository import TagRepo
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from tests.recipes_catalog.random_refs import random_meal, random_recipe
from tests.utils import build_dict_from_instance

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_can_add_meal_to_repo(
    async_pg_session: AsyncSession,
):
    domain = random_meal()
    repo = MealRepo(async_pg_session)
    await repo.add(domain)
    query = await repo.get(domain.id)
    assert domain == query
    domain_dict = build_dict_from_instance(domain)
    query_dict = build_dict_from_instance(query)
    assert domain_dict.pop("created_at") == None != query_dict.pop("created_at")
    assert domain_dict.pop("updated_at") == None != query_dict.pop("updated_at")
    for recipe in domain_dict["recipes"]:
        assert recipe.pop("created_at") == None
        assert recipe.pop("updated_at") == None
    for recipe in query_dict["recipes"]:
        assert recipe.pop("created_at") != None
        assert recipe.pop("updated_at") != None
    assert domain_dict == query_dict


async def test_persist_all_can_persist_a_discarded_meal(
    async_pg_session: AsyncSession,
):
    domain = random_meal()
    repo = MealRepo(async_pg_session)
    await repo.add(domain)
    query = await repo.get(domain.id)
    assert domain == query
    query._discard()
    await repo.persist_all([query])
    with pytest.raises(EntityNotFoundException):
        query = await repo.get(domain.id)


async def test_can_add_meal_to_repo_when_recipe_tag_already_exists(
    async_pg_session: AsyncSession,
):
    tag = Tag(key="key", value="value", author_id="author_id", type="recipe")
    recipe1 = random_recipe(tags=[tag])
    recipe2 = random_recipe(tags=[tag])
    domain = random_meal(author_id="author_id", recipes=[recipe1, recipe2])
    repo = MealRepo(async_pg_session)
    await repo.add(domain)


async def test_correctly_dissociate_tag_from_meal(
    async_pg_session: AsyncSession,
):
    tag = Tag(key="key", value="value", author_id="author_id", type="meal")
    domain = random_meal(tags=[tag])
    repo = MealRepo(async_pg_session)
    await repo.add(domain)
    assert len(domain.tags) == 1
    tag_repo = TagRepo(async_pg_session)
    tag_on_db = await tag_repo.query(
        filter={
            "key": "key",
            "value": "value",
            "type": "meal",
            "author_id": "author_id",
        }
    )
    assert len(tag_on_db) == 1
    query = await repo.get(domain.id)
    query.update_properties(tags=[])
    await repo.persist(query)
    query = await repo.get(domain.id)
    assert len(query.tags) == 0
    tag_on_db = await tag_repo.query(
        filter={
            "key": "key",
            "value": "value",
            "type": "meal",
            "author_id": "author_id",
        }
    )
    assert len(tag_on_db) == 1


# @pytest.mark.skip
async def test_adding_a_meal_correctly_adds_the_recipes(
    async_pg_session: AsyncSession,
):
    recipe = random_recipe(
        ratings=[],
    )
    recipe_repo = RecipeRepo(async_pg_session)
    await recipe_repo.add(recipe)
    meal_id = uuid.uuid4().hex
    meal = Meal.create_meal(
        meal_id=meal_id,
        name="meal_name",
        author_id="author_id",
        menu_id="menu_id",
    )
    meal.copy_recipes([recipe])
    assert len(meal.recipes) == 1
    meal_repo = MealRepo(async_pg_session)
    await meal_repo.add(meal)
    all_recipes = await recipe_repo.query()
    assert len(all_recipes) == 2
    meal_on_db = await meal_repo.get(meal.id)
    assert len(meal_on_db.recipes[0].tags) == 1
    recipe_1_dict = build_dict_from_instance(all_recipes[0])
    recipe_2_dict = build_dict_from_instance(all_recipes[1])
    assert recipe_1_dict.pop("created_at") != None != recipe_2_dict.pop("created_at")
    assert recipe_1_dict.pop("updated_at") != None != recipe_2_dict.pop("updated_at")
    assert recipe_1_dict.pop("id") != None != recipe_2_dict.pop("id")
    assert recipe_1_dict.pop("meal_id") == None != recipe_2_dict.pop("meal_id")
    assert (
        recipe_1_dict.pop("author_id")
        == recipe.author_id
        != meal_on_db.author_id
        == recipe_2_dict.pop("author_id")
    )
    for tag in recipe_1_dict["tags"]:
        assert tag.pop("author_id") == recipe.author_id != meal_on_db.author_id
    for tag in recipe_2_dict["tags"]:
        assert tag.pop("author_id") == meal_on_db.author_id
    assert len(recipe_1_dict["tags"]) == len(recipe_2_dict["tags"])
    for tag in recipe_1_dict["tags"]:
        assert tag in recipe_2_dict["tags"]
    assert recipe_1_dict == recipe_2_dict


# @pytest.mark.skip
async def test_coping_a_whole_meal(
    async_pg_session: AsyncSession,
):
    recipe_1 = random_recipe(
        ratings=[],
    )
    recipe_repo = RecipeRepo(async_pg_session)
    await recipe_repo.add(recipe_1)
    recipe_1_2 = random_recipe(
        ratings=[],
    )
    await recipe_repo.add(recipe_1_2)
    meal_id = uuid.uuid4().hex
    meal_1 = Meal.create_meal(
        meal_id=meal_id,
        name="meal_name",
        author_id="author_id",
        menu_id="menu_id",
    )
    meal_1.copy_recipes([recipe_1, recipe_1_2])
    assert len(meal_1.recipes) == 2
    meal_repo = MealRepo(async_pg_session)
    await meal_repo.add(meal_1)
    meal_2 = Meal.copy_meal(meal_1, "another_user_id")
    await meal_repo.add(meal_2)
    all_meals = await meal_repo.query()
    assert len(all_meals) == 2
    for meal in all_meals:
        if meal.author_id == "author_id":
            meal_1_dict = build_dict_from_instance(meal)
        if meal.author_id == "another_user_id":
            meal_2_dict = build_dict_from_instance(meal)
    assert meal_1_dict.pop("created_at") != None != meal_2_dict.pop("created_at")
    assert meal_1_dict.pop("updated_at") != None != meal_2_dict.pop("updated_at")
    assert meal_1_dict.pop("id") != None != meal_2_dict.pop("id")
    assert meal_1_dict.pop("author_id") != None != meal_2_dict.pop("author_id")
    recipes_in_meal_1 = meal_1_dict.pop("recipes")
    recipes_in_meal_2 = meal_2_dict.pop("recipes")
    assert meal_1_dict.pop("version") == 2
    assert meal_2_dict.pop("version") == 1
    assert meal_1_dict == meal_2_dict
    for r1 in recipes_in_meal_1:
        for r2 in recipes_in_meal_2:
            if r1["name"] == r2["name"]:
                assert r1.pop("created_at") != None != r2.pop("created_at")
                assert r1.pop("updated_at") != None != r2.pop("updated_at")
                assert r1.pop("id") != None != r2.pop("id")
                assert r1.pop("meal_id") == meal_1.id
                assert r2.pop("meal_id") == meal_2.id
                assert r1.pop("author_id") == "author_id"
                assert r2.pop("author_id") == "another_user_id"
                for tag in r1["tags"]:
                    assert tag.pop("author_id") == "author_id"
                for tag in r2["tags"]:
                    assert tag.pop("author_id") == "another_user_id"
                assert len(r1["tags"]) == len(r2["tags"])
                for tag in r1["tags"]:
                    assert tag in r2["tags"]
                assert r1 == r2
    all_recipes = await recipe_repo.query()
    assert len(all_recipes) == 6


async def test_can_query_list_of_ids(
    async_pg_session: AsyncSession,
):
    meal_1 = random_meal()
    meal_2 = random_meal()
    meal_3 = random_meal()
    repo = MealRepo(async_pg_session)
    await repo.add(meal_1)
    await repo.add(meal_2)
    await repo.add(meal_3)
    meals = await repo.query(filter={"id": [meal_1.id, meal_2.id]})
    assert meal_1 in meals
    assert meal_2 in meals
    assert meal_3 not in meals

# @pytest.mark.skip
@pytest.mark.parametrize(
    "attribute_value,filter_key,filter_values_in,filter_values_not_in",
    [
        (100, "total_time_lte", [100], [99]),
        (100, "total_time_gte", [100], [101]),
        (
            set(
                [
                    Tag(
                        key="key_in",
                        value="value",
                        author_id="author_id",
                        type="meal",
                    ),
                    Tag(
                        key="key_in",
                        value="another_value_in",
                        author_id="author_id",
                        type="meal",
                    ),
                    Tag(
                        key="another_key_in",
                        value="value",
                        author_id="author_id",
                        type="meal",
                    ),
                    Tag(
                        key="another_key_in",
                        value="another_value",
                        author_id="author_id",
                        type="meal",
                    ),
                ]
            ),
            "tags",
            ["key_in:value|key_in:another_value_in|another_key_in:value"],
            [
                "key_in:value_not_in|key_in:another_value_in|another_key_in:value",
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
                        type="meal",
                    ),
                    Tag(
                        key="key_in",
                        value="another_value_in",
                        author_id="author_id",
                        type="meal",
                    ),
                    Tag(
                        key="another_key_in",
                        value="value",
                        author_id="author_id",
                        type="meal",
                    ),
                    Tag(
                        key="another_key_in",
                        value="another_value",
                        author_id="author_id",
                        type="meal",
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
    repo = MealRepo(async_pg_session)
    key = filter_key.replace("_lte", "").replace("_gte", "").replace("_not_exists", "")
    kwargs = {
        key: attribute_value,
        "author_id": "author_id",
    }
    if key == "total_time":
        recipes = [random_recipe(total_time=attribute_value) for _ in range(3)]
        kwargs.update({"recipes": recipes})
    domain = random_meal(**kwargs)
    await repo.add(domain)
    for value in filter_values_in:
        api_in = ApiMealFilter(**{filter_key: value})
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
        api_not_in = ApiMealFilter(**{filter_key: value})
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
        assert len(values_in) == 0
        assert len(values_in) == 0
