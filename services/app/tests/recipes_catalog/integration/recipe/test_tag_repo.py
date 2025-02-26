import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.recipes_catalog.shared.adapters.repositories.tag.recipe_tag import \
    TagRepo
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from tests.recipes_catalog.random_refs import random_attr, random_user

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_can_add_tag_to_repo(
    async_pg_session: AsyncSession,
):
    repo = TagRepo(async_pg_session)
    user = random_user()
    domain = Tag(
        key=random_attr("tag_key"),
        value=random_attr("tag_value"),
        author_id=user.id,
        type="recipe",
    )
    query = await repo.query(
        filter={
            "key": domain.key,
            "value": domain.value,
            "author_id": user.id,
            "type": "recipe",
        }
    )
    assert len(query) == 0
    await repo.add(domain)
    query = await repo.query(
        filter={
            "key": domain.key,
            "value": domain.value,
            "author_id": user.id,
            "type": "recipe",
        }
    )
    assert len(query) == 1
    assert query[0] == domain
