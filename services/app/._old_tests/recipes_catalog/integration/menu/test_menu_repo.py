import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.recipes_catalog.core.adapters.repositories.client.menu import MenuRepo

from src.contexts.recipes_catalog.core.domain.value_objects.menu_meal import MenuMeal
from src.contexts.shared_kernel.adapters.repositories.tags.tag_repository import TagRepo

from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from tests.recipes_catalog.random_refs import random_menu
from tests.utils import build_dict_from_instance

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_can_add_menu_to_repo(
    async_pg_session: AsyncSession,
):
    domain = random_menu()
    repo = MenuRepo(async_pg_session)
    await repo.add(domain)
    query = await repo.get(domain.id)
    assert domain == query
    domain_dict = build_dict_from_instance(domain)
    query_dict = build_dict_from_instance(query)
    assert domain_dict.pop("created_at") == None != query_dict.pop("created_at")
    assert domain_dict.pop("updated_at") == None != query_dict.pop("updated_at")
    assert domain_dict == query_dict


async def test_queried_menus_are_added_to_seen_attribute(
    async_pg_session: AsyncSession,
):
    domain = random_menu()
    domain_1 = random_menu()
    domain_2 = random_menu()
    repo = MenuRepo(async_pg_session)
    await repo.add(domain)
    await repo.add(domain_1)
    await repo.add(domain_2)
    repo.seen.remove(domain)
    repo.seen.remove(domain_1)
    repo.seen.remove(domain_2)
    query = await repo.query(filter={"author_id": "author_not_in"})
    assert len(query) == 0
    assert repo.seen == set()
    query = await repo.query(filter={"id": [domain.id, domain_1.id]})
    assert len(query) == 2
    assert domain in query
    assert domain_1 in query


async def test_correctly_dissociate_tag_from_menu(
    async_pg_session: AsyncSession,
):
    tag = Tag(key="key", value="value", author_id="author_id", type="menu")
    domain = random_menu(tags=[tag])
    repo = MenuRepo(async_pg_session)
    await repo.add(domain)
    assert len(domain.tags) == 1
    tag_repo = TagRepo(async_pg_session)
    tag_on_db = await tag_repo.query(
        filter={
            "key": "key",
            "value": "value",
            "type": "menu",
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
            "type": "menu",
            "author_id": "author_id",
        }
    )
    assert len(tag_on_db) == 1


async def test_cannot_add_a_menu_with_a_meal_that_does_NOT_exists(
    async_pg_session: AsyncSession,
):
    menu = random_menu()
    menu.meals = set([
        MenuMeal(
            meal_id="non existing meal id",
            meal_name="name",
            week=1,
            weekday="Monday",
            meal_type="Lunch",
        )
    ])
    repo = MenuRepo(async_pg_session)
    with pytest.raises(IntegrityError, match="violates foreign key constraint"):
        await repo.add(menu)
