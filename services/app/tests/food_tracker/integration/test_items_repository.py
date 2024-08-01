import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.food_tracker.shared.adapters.repositories.houses import HousesRepo
from src.contexts.food_tracker.shared.adapters.repositories.items import ItemsRepo
from src.contexts.products_catalog.shared.adapters.repositories.product import (
    ProductRepo,
)
from src.contexts.products_catalog.shared.adapters.repositories.source import SourceRepo
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.contexts.shared_kernel.adapters.repositories.diet_type import DietTypeRepo
from tests.food_tracker.random_refs import random_house, random_item
from tests.products_catalog.random_refs import (
    random_diet_type,
    random_food_product,
    random_source,
)

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_unique_column_works(async_pg_session: AsyncSession):
    house_repo = HousesRepo(async_pg_session)
    house = random_house()
    await house_repo.add(house)
    repo = ItemsRepo(async_pg_session)
    item = random_item(house_id=house.id)
    same_id = random_item(house_id=house.id)
    same_id._id = item._id
    await repo.add(item)
    with pytest.raises(IntegrityError):
        await repo.add(same_id)
        await async_pg_session.commit()


async def test_cannot_persist_item_not_added(async_pg_session: AsyncSession):
    repo = ItemsRepo(async_pg_session)
    item = random_item()
    with pytest.raises(AssertionError):
        await repo.persist(item)


async def test_can_filter_by_product(async_pg_session: AsyncSession):
    source_repo = SourceRepo(async_pg_session)
    source = random_source()
    await source_repo.add(source)
    product_repo = ProductRepo(async_pg_session)
    product_1 = random_food_product(
        prefix="existing1",
        source_id=source.id,
    )
    product_2 = random_food_product(
        prefix="existing2",
        source_id=source.id,
    )
    await product_repo.add(product_1)
    await product_repo.add(product_2)

    house_repo = HousesRepo(async_pg_session)
    house = random_house()
    await house_repo.add(house)
    item_repo = ItemsRepo(async_pg_session)
    item_1 = random_item(house_id=house.id, product_id=product_1.id)
    item_2 = random_item(house_id=house.id, product_id=product_2.id)
    await item_repo.add(item_1)
    await item_repo.add(item_2)
    assert [item_1] == await item_repo.query(filter={"product_id": product_1.id})
    assert [item_2] == await item_repo.query(filter={"product_id": product_2.id})


async def test_can_filter_by_diet_type(async_pg_session: AsyncSession):
    source_repo = SourceRepo(async_pg_session)
    source = random_source()
    await source_repo.add(source)
    diet_type_repo = DietTypeRepo(async_pg_session)
    vegan = random_diet_type(name="vegan")
    await diet_type_repo.add(vegan)
    vegetarian = random_diet_type(name="vegetarian")
    await diet_type_repo.add(vegetarian)
    product_repo = ProductRepo(async_pg_session)
    product_1 = random_food_product(
        prefix="existing1",
        source_id=source.id,
        diet_types_ids=set([vegan.id, vegetarian.id]),
    )
    product_2 = random_food_product(
        prefix="existing2",
        source_id=source.id,
        diet_types_ids=set([vegan.id]),
    )
    await product_repo.add(product_1)
    await product_repo.add(product_2)

    house_repo = HousesRepo(async_pg_session)
    house = random_house()
    await house_repo.add(house)
    item_repo = ItemsRepo(async_pg_session)
    item_1 = random_item(house_id=house.id, product_id=product_1.id)
    item_2 = random_item(house_id=house.id, product_id=product_2.id)
    await item_repo.add(item_1)
    await item_repo.add(item_2)
    both_items = await item_repo.query(
        filter={"product_diet_types": [vegan.name, vegetarian.name]}
    )
    both_items_again = await item_repo.query(
        filter={"product_diet_types": [vegan.name]}
    )
    only_item_1 = await item_repo.query(filter={"product_diet_types": vegetarian.name})
    assert item_1 in both_items
    assert item_2 in both_items
    assert item_2 in both_items_again
    assert item_1 in both_items_again
    assert item_1 in only_item_1
    assert item_2 not in only_item_1


async def test_can_list_with_empty_filter(async_pg_session: AsyncSession):
    house_repo = HousesRepo(async_pg_session)
    house = random_house()
    await house_repo.add(house)
    repo = ItemsRepo(async_pg_session)
    item_1 = random_item(house_id=house.id)
    item_2 = random_item(house_id=house.id)
    await repo.add(item_1)
    await repo.add(item_2)
    result = await repo.query()
    assert item_1 in result
    assert item_2 in result


async def test_cannot_use_not_allowed_filter(async_pg_session: AsyncSession):
    repo = ItemsRepo(async_pg_session)
    with pytest.raises(BadRequestException):
        await repo.query(filter={"not_allowed": "not_allowed"})


async def test_can_list_with_str_or_list(async_pg_session: AsyncSession):
    source_repo = SourceRepo(async_pg_session)
    source = random_source()
    await source_repo.add(source)
    diet_type_repo = DietTypeRepo(async_pg_session)
    vegan = random_diet_type(name="vegan")
    await diet_type_repo.add(vegan)
    vegetarian = random_diet_type(name="vegetarian")
    await diet_type_repo.add(vegetarian)
    product_repo = ProductRepo(async_pg_session)
    product_1 = random_food_product(
        prefix="existing1",
        source_id=source.id,
        diet_types_ids=set([vegan.id, vegetarian.id]),
    )
    product_2 = random_food_product(
        prefix="existing2",
        source_id=source.id,
        diet_types_ids=set([vegan.id]),
    )
    await product_repo.add(product_1)
    await product_repo.add(product_2)

    house_repo = HousesRepo(async_pg_session)
    house = random_house()
    await house_repo.add(house)
    item_repo = ItemsRepo(async_pg_session)
    item_1 = random_item(house_id=house.id, product_id=product_1.id)
    item_2 = random_item(house_id=house.id, product_id=product_2.id)
    await item_repo.add(item_1)
    await item_repo.add(item_2)
    both_items = await item_repo.query(filter={"product_diet_types": [vegan.name]})
    only_item_1 = await item_repo.query(
        filter={"product_diet_types": [vegetarian.name]}
    )
    assert item_1 in only_item_1
    assert item_2 not in only_item_1
    assert item_2 in both_items
    assert item_1 in both_items
    both_items = await item_repo.query(filter={"product_diet_types": vegan.name})
    only_item_1 = await item_repo.query(filter={"product_diet_types": vegetarian.name})
    assert item_1 in only_item_1
    assert item_2 not in only_item_1
    assert item_2 in both_items
    assert item_1 in both_items


async def test_can_sort_by_nutri_facts(async_pg_session: AsyncSession):
    source_repo = SourceRepo(async_pg_session)
    source = random_source()
    await source_repo.add(source)
    product_repo = ProductRepo(async_pg_session)
    product_1 = random_food_product(
        prefix="existing1",
        source_id=source.id,
    )
    product_2 = random_food_product(
        prefix="existing2",
        source_id=source.id,
    )
    await product_repo.add(product_1)
    await product_repo.add(product_2)

    house_repo = HousesRepo(async_pg_session)
    house = random_house()
    await house_repo.add(house)
    item_repo = ItemsRepo(async_pg_session)
    item_1 = random_item(house_id=house.id, product_id=product_1.id)
    item_2 = random_item(house_id=house.id, product_id=product_2.id)
    await item_repo.add(item_1)
    await item_repo.add(item_2)
    ordered_items = await item_repo.query(filter={"sort": "calories"})
    ordered_products = [
        i.id
        for i in sorted(
            [product_1, product_2], key=lambda x: x.nutri_facts.calories.value
        )
    ]
    assert ordered_items[0].product_id == ordered_products[0]
    assert ordered_items[1].product_id == ordered_products[1]


# async def test_can_sort_by_cfe_key(async_pg_session: AsyncSession):
#     repo = HousesRepo(async_pg_session)
#     house_1 = random_house()
#     receipt_1 = random_receipt(cfe_key="test_can_filte_by_cfe_key_1")
#     house_1.add_receipt(receipt=receipt_1)
#     house_2 = random_house()
#     receipt_2 = random_receipt(cfe_key="test_can_filte_by_cfe_key_2")
#     house_2.add_receipt(receipt=receipt_2)
#     await repo.add(house_1)
#     await repo.add(house_2)
#     result = await repo.select(filter={"sort": "cfe_key"})
#     assert result.index(house_1) < result.index(house_2)
#     result = await repo.select(filter={"sort": "-cfe_key"})
#     assert result.index(house_1) > result.index(house_2)
