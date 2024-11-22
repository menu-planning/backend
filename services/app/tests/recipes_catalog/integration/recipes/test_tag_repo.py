import pytest
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
from src.contexts.shared_kernel.adapters.repositories.cuisine import CuisineRepo
from src.contexts.shared_kernel.adapters.repositories.flavor import FlavorRepo
from src.contexts.shared_kernel.adapters.repositories.texture import TextureRepo
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine
from src.contexts.shared_kernel.domain.value_objects.name_tag.flavor import Flavor
from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture
from tests.recipes_catalog.random_refs import (
    CategoryRandomEnum,
    CuisineRandomEnum,
    FlavorRandomEnum,
    MealPlanningRandomEnum,
    TextureRandomEnum,
    random_tag_id,
    random_user,
)

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


@pytest.mark.parametrize(
    "tag_repo,tag,random_enum",
    [
        (CategoryRepo, Category, CategoryRandomEnum),
        (MealPlanningRepo, MealPlanning, MealPlanningRandomEnum),
    ],
)
async def test_can_add_tag_to_repo(
    async_pg_session: AsyncSession,
    tag_repo,
    tag,
    random_enum,
):
    repo = tag_repo(async_pg_session)
    user = random_user()
    domain = tag.create_tag(
        name=random_tag_id(random_enum=random_enum), author_id=user.id
    )
    await repo.add(domain)
    query = await repo.get(domain.id)
    assert query == domain


@pytest.mark.parametrize(
    "tag_repo,tag,random_enum",
    [
        (FlavorRepo, Flavor, FlavorRandomEnum),
        (TextureRepo, Texture, TextureRandomEnum),
        (CuisineRepo, Cuisine, CuisineRandomEnum),
    ],
)
async def test_can_add_shared_tag_to_repo(
    async_pg_session: AsyncSession,
    tag_repo,
    tag,
    random_enum,
):
    repo = tag_repo(async_pg_session)
    domain = tag(name=random_tag_id(random_enum=random_enum))
    await repo.add(domain)
    query = await repo.get(domain.name)
    assert query == domain


@pytest.mark.parametrize(
    "tag_repo,tag,random_enum,attribute_value,filter_key,filter_values_in, filter_values_not_in",
    [
        (
            CategoryRepo,
            Category,
            CategoryRandomEnum,
            "random_name",
            "name",
            ["random_name"],
            ["random_name_2"],
        ),
        (
            CategoryRepo,
            Category,
            CategoryRandomEnum,
            "random_author_id",
            "author_id",
            ["random_author_id"],
            ["random_author_id_2"],
        ),
        (
            CategoryRepo,
            Category,
            CategoryRandomEnum,
            Privacy.PRIVATE,
            "privacy",
            ["private"],
            ["public"],
        ),
    ],
)
async def test_can_query(
    async_pg_session: AsyncSession,
    tag_repo,
    tag,
    random_enum,
    attribute_value,
    filter_key,
    filter_values_in,
    filter_values_not_in,
):
    repo = tag_repo(async_pg_session)
    if filter_key == "author_id":
        user = random_user(id=attribute_value)
    else:
        user = random_user()
    if filter_key == "privacy":
        domain = tag.create_tag(
            name=random_tag_id(random_enum=random_enum),
            author_id=user.id,
            privacy=attribute_value,
        )
    else:
        domain = tag.create_tag(
            name=random_tag_id(random_enum=random_enum), author_id=user.id
        )
    if filter_key != "author_id" and filter_key != "privacy":
        setattr(domain, filter_key, attribute_value)
    await repo.add(domain)
    for value in filter_values_in:
        query = await repo.query({filter_key: value})
        assert len(query) == 1
        assert query[0] == domain
    for value in filter_values_not_in:
        query = await repo.query({filter_key: value})
        assert len(query) == 0
