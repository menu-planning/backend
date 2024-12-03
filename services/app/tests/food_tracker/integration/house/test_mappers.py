import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.food_tracker.shared.adapters.ORM.mappers.house import HouseMapper
from src.contexts.food_tracker.shared.domain.entities.house import House
from tests.food_tracker.random_refs import random_attr

pytestmark = [pytest.mark.anyio]


def list_of_members(n: int) -> list[str]:
    return [uuid.uuid4().hex for _ in range(n)]


def list_of_nutritionists(n: int) -> list[str]:
    return [uuid.uuid4().hex for _ in range(n)]


@pytest.mark.parametrize(
    "n_members,n_nutritionists,version",
    [
        (0, 0, 1),
        (2, 2, 3),
    ],
)
async def test_map_house(
    n_members, n_nutritionists, version, async_pg_session: AsyncSession
) -> None:
    mapper = HouseMapper
    domain_model = House(
        id=random_attr("id"),
        owner_id=random_attr("id"),
        name=random_attr("name"),
        members_ids=list_of_members(n_members),
        nutritionists_ids=list_of_nutritionists(n_nutritionists),
        version=version,
    )
    sa_model = await mapper.map_domain_to_sa(async_pg_session, domain_model)
    assert sa_model.id == domain_model.id
    assert sa_model.owner_id == domain_model.owner_id
    assert sa_model.name == domain_model.name
    assert sa_model.discarded == domain_model.discarded
    assert sa_model.version == domain_model.version
    assert len(sa_model.members) == n_members
    for id in domain_model.members_ids:
        assert id in [i.user_id for i in sa_model.members]
    assert len(sa_model.nutritionists) == n_nutritionists
    for id in domain_model.nutritionists_ids:
        assert id in [i.user_id for i in sa_model.nutritionists]

    reverted_domain = mapper.map_sa_to_domain(sa_model)
    assert reverted_domain == domain_model
    assert reverted_domain.id == domain_model.id
    assert reverted_domain.owner_id == domain_model.owner_id
    assert reverted_domain.name == domain_model.name
    assert reverted_domain.discarded == domain_model.discarded
    assert reverted_domain.version == domain_model.version
    assert len(reverted_domain.members_ids) == n_members
    for id in domain_model.members_ids:
        assert id in reverted_domain.members_ids
    assert len(reverted_domain.nutritionists_ids) == n_nutritionists
    for id in domain_model.nutritionists_ids:
        assert id in reverted_domain.nutritionists_ids
