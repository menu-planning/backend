import random

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.repositories.product_repository import (
    ProductRepo,
)
from src.contexts.products_catalog.core.adapters.repositories.source_repository import SourceRepo
from src.contexts.products_catalog.core.domain.value_objects.is_food_votes import (
    IsFoodVotes,
)
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from old_tests.products_catalog.random_refs import random_attr, random_barcode, random_food_product, random_nutri_facts
from tests.contexts.products_catalog.utils import insert_food_product


pytestmark = [pytest.mark.anyio, pytest.mark.integration]


_source_sort_order = ["manual", "tbca", "taco", "private", "gs1", "auto"]


async def test_unique_column_works(async_pg_session: AsyncSession):
    product_id = random_attr("id")
    await insert_food_product(async_pg_session, product_id)
    repo = ProductRepo(async_pg_session)
    same_id = random_food_product()
    same_id._id = product_id
    with pytest.raises(IntegrityError):
        await repo.add(same_id)
        await repo._session.commit()


async def test_can_add_multiple_houses_to_product_registry(
    async_pg_session: AsyncSession,
):
    product_1_id = random_attr("id")
    await insert_food_product(async_pg_session, product_1_id)
    product_2_id = random_attr("id")
    await insert_food_product(async_pg_session, product_2_id)
    repo = ProductRepo(async_pg_session)
    product_1 = await repo.get(product_1_id)
    product_2 = await repo.get(product_2_id)
    house_ids = [random_attr("id") for _ in range(3)]
    product_1.add_house_input_to_is_food_registry(house_ids[0], True)
    product_1.add_house_input_to_is_food_registry(house_ids[1], False)
    product_1.add_house_input_to_is_food_registry(house_ids[2], True)
    product_1.add_house_input_to_is_food_registry(house_ids[2], False)
    product_2.add_house_input_to_is_food_registry(house_ids[0], False)
    product_2.add_house_input_to_is_food_registry(house_ids[0], True)
    product_2.add_house_input_to_is_food_registry(house_ids[1], False)
    product_2.add_house_input_to_is_food_registry(house_ids[2], True)
    await repo.persist(product_1)
    # assert False
    await repo.persist(product_2)
    product_1 = await repo.get(product_1.id)
    product_2 = await repo.get(product_2.id)
    assert (
        len(product_1.is_food_votes.is_food_houses)
        + len(product_1.is_food_votes.is_not_food_houses)
        == 3
    )
    assert (
        len(product_2.is_food_votes.is_food_houses)
        + len(product_2.is_food_votes.is_not_food_houses)
        == 3
    )


async def test_cannot_persist_product_not_added(async_pg_session: AsyncSession):
    repo = ProductRepo(async_pg_session)
    product = random_food_product()
    with pytest.raises(AssertionError):
        await repo.persist(product)


async def test_can_search_by_name_similarity(async_pg_session: AsyncSession):
    name_not_in = "feijao"
    names_in = ["banana prata", "rabanada", "banana maca"]
    all_names = [name_not_in] + names_in
    for name in all_names:
        product_id = random_attr("id")
        await insert_food_product(session=async_pg_session, id=product_id, name=name)
    repo = ProductRepo(async_pg_session)
    for name in names_in:
        products_found = await repo.list_top_similar_names(name[:-3])
        assert name == products_found[0].name
        assert name_not_in not in [i.name for i in products_found]
    assert False


async def test_filter_by_first_word_match_on_search_by_name_similarity(
    async_pg_session: AsyncSession,
):
    first_word_not_in = "banana maca"
    names_in = ["maca fuji", "maca verde"]
    all_names = [first_word_not_in] + names_in
    for name in all_names:
        product_id = random_attr("id")
        await insert_food_product(session=async_pg_session, id=product_id, name=name)
    repo = ProductRepo(async_pg_session)
    for name in all_names:
        dont_filter_by_first_word = await repo.list_top_similar_names(name)
        assert name == dont_filter_by_first_word[0].name
        assert first_word_not_in in [i.name for i in dont_filter_by_first_word]
    for name in names_in:
        filter_by_first_word = await repo.list_top_similar_names(
            name, filter_by_first_word_partial_match=True
        )
        assert name == filter_by_first_word[0].name
        assert first_word_not_in not in [i.name for i in filter_by_first_word]



brands = [random_attr(f"brand{i}") for i in range(1, 4)]
list_brand_and_categories_fields_data = {
    random_attr("parent_category_1"): {
        random_attr("category_11"): random.sample(brands, 2),
        random_attr("category_12"): random.sample(brands, 2),
    },
    random_attr("parent_category_2"): {
        random_attr("category_21"): random.sample(brands, 2),
        random_attr("category_22"): random.sample(brands, 2),
    },
}


# class TestListBrandAndCategories:
#     async def test_no_filter(self, async_pg_session: AsyncSession):
#         source_repo = SourceRepo(async_pg_session)
#         source = random_source()
#         await source_repo.add(source)
#         repo = ProductRepo(async_pg_session)
#         data = list_brand_and_categories_fields_data
#         used_brands = set()
#         parent_cat_repo = AsyncParentCategoryRepo(async_pg_session)
#         cat_repo = CategoryRepo(async_pg_session)
#         brand_repo = BrandRepo(async_pg_session)
#         for pck, pcv in data.items():
#             parent_category = random_parent_category(name=pck)
#             await parent_cat_repo.add(parent_category)
#             for ck, cv in pcv.items():
#                 category = random_category(name=ck)
#                 await cat_repo.add(category)
#                 for brand in cv:
#                     brand_instance = random_brand(name=brand)
#                     await brand_repo.add(brand_instance)
#                     used_brands.add(brand)
#                     product = random_food_product(
#                         source_id=source.id,
#                         brand_id=brand_instance.id,
#                         category_id=category.id,
#                         parent_category_id=parent_category.id,
#                     )
#                     await repo.add(product)
#         await repo._session.commit()
#         fields = await repo.list_filter_options()
#         for i in data.keys():
#             assert i in fields["parent-category"]["options"]
#         assert fields["category"]["options"] == []
#         for i in used_brands:
#             assert i in fields["brand"]["options"]

#     async def test_parent_category_filter(self, async_pg_session: AsyncSession):
#         repo = ProductRepo(async_pg_session)
#         data = list_brand_and_categories_fields_data
#         for pck, pcv in data.items():
#             for cck, ccv in pcv.items():
#                 for brand in ccv:
#                     product = random_food_product(
#                         brand=brand,
#                         category=cck,
#                         parent_category=pck,
#                     )
#                     await repo.add(product)
#         pc_value_in = list(data.keys())[0]
#         pc_value_out = list(data.keys())[1]
#         fields = await repo.list_filter_options(filter={"parent_category": pc_value_in})
#         used_brands = set()
#         for cck, ccv in data[pc_value_in].items():
#             for brand in ccv:
#                 used_brands.add(brand)
#         for i in data.keys():
#             assert i in fields["parent-category"]["options"]
#         for i in data[pc_value_in].keys():
#             assert i in fields["category"]["options"]
#         for i in data[pc_value_out].keys():
#             assert i not in fields["category"]["options"]
#         for i in used_brands:
#             assert i in fields["brand"]["options"]

#     async def test_parent_category_and_category_filter(
#         self, async_pg_session: AsyncSession
#     ):
#         repo = ProductRepo(async_pg_session)
#         data = list_brand_and_categories_fields_data
#         for pck, pcv in data.items():
#             for cck, ccv in pcv.items():
#                 for brand in ccv:
#                     product = random_food_product(
#                         brand=brand,
#                         category=cck,
#                         parent_category=pck,
#                     )
#                     await repo.add(product)
#         pc_value_in = list(data.keys())[1]
#         pc_value_out = list(data.keys())[0]
#         cc_value_in = list(data[pc_value_in].keys())[0]
#         cc_value_out = list(data[pc_value_out].keys())[1]
#         fields = await repo.list_filter_options(
#             filter={"parent_category": pc_value_in, "category": cc_value_in}
#         )
#         used_brands = set()
#         for brand in data[pc_value_in][cc_value_in]:
#             used_brands.add(brand)
#         unused_brands = set()
#         for brand in data[pc_value_out][cc_value_out]:
#             unused_brands.add(brand)
#         for i in data.keys():
#             assert i in fields["parent-category"]["options"]
#         for i in data[pc_value_in].keys():
#             assert i in fields["category"]["options"]
#         for i in data[pc_value_out].keys():
#             assert i not in fields["category"]["options"]
#         for i in used_brands:
#             assert i in fields["brand"]["options"]
#         for i in unused_brands:
#             assert i not in fields["category"]["options"]

#     async def test_category_and_NO_parent_category_filter(
#         self, async_pg_session: AsyncSession
#     ):
#         repo = ProductRepo(async_pg_session)
#         data = list_brand_and_categories_fields_data
#         used_brands = set()
#         for pck, pcv in data.items():
#             for cck, ccv in pcv.items():
#                 for brand in ccv:
#                     used_brands.add(brand)
#                     product = random_food_product(
#                         brand=brand,
#                         category=cck,
#                         parent_category=pck,
#                     )
#                     await repo.add(product)
#         pc_value = list(data.keys())[1]
#         cc_value = list(data[pc_value].keys())[0]
#         with pytest.raises(BadRequestException):
#             await repo.list_filter_options(filter={"category": cc_value})
#         # fields = await repo.list_filter_options(filters={"category": cc_value})
#         # for i in data.keys():
#         #     assert i in fields["parent-category"]["options"]
#         # assert fields["category"]["options"] == []
#         # print(fields["brand"]["options"])
#         # assert all([i in used_brands for i in fields["brand"]["options"]])


class TestCanFilter:
    async def test_can_list_with_empty_filter(self, async_pg_session: AsyncSession):
        product_1_id = random_attr("id")
        await insert_food_product(async_pg_session, product_1_id)
        product_2_id = random_attr("id")
        await insert_food_product(async_pg_session, product_2_id)
        repo = ProductRepo(async_pg_session)
        result = await repo.query()
        ids = [i.id for i in result]
        assert product_1_id in ids
        assert product_2_id in ids

    async def test_cannot_use_not_allowed_filter(self, async_pg_session: AsyncSession):
        repo = ProductRepo(async_pg_session)
        with pytest.raises(BadRequestException):
            await repo.query(filter={"not_allowed": "not_allowed"})

    async def test_can_list_with_str_or_list(self, async_pg_session: AsyncSession):
        product_1_id = random_attr("id")
        await insert_food_product(async_pg_session, product_1_id)
        product_2_id = random_attr("id")
        await insert_food_product(async_pg_session, product_2_id)
        repo = ProductRepo(async_pg_session)
        result = await repo.query(filter={"id": [product_1_id, product_2_id]})
        ids = [i.id for i in result]
        assert product_1_id in ids
        assert product_2_id in ids
        p1 = await repo.query(filter={"id": product_1_id})
        assert p1[0].id == product_1_id
        p2 = await repo.query(filter={"id": product_2_id})
        assert p2[0].id == product_2_id

    async def test_can_hide_undefined_auto_product(
        self, async_pg_session: AsyncSession
    ):
        barcode = random_barcode()
        product_1_id = random_attr("id")
        await insert_food_product(
            session=async_pg_session,
            id=product_1_id,
            barcode=barcode,
            source="auto",
        )
        product_2_id = random_attr("id")
        await insert_food_product(
            session=async_pg_session,
            id=product_2_id,
            barcode=barcode,
            source="private",
        )
        repo = ProductRepo(async_pg_session)
        result = await repo.query(filter={"barcode": barcode})
        ids = [i.id for i in result]
        assert product_1_id not in ids
        assert product_2_id in ids
        new_barcode = random_barcode()
        source_repo = SourceRepo(async_pg_session)
        source_auto = await source_repo.get("auto")
        product_3 = random_food_product(source_id=source_auto.id, barcode=new_barcode)
        product_3._is_food_votes = IsFoodVotes(
            is_food_houses=[random_attr("id") for _ in range(3)], is_not_food_houses=[]
        )
        await repo.add(product_3)
        result = await repo.query(filter={"barcode": product_3.barcode})
        assert product_3 in result

    async def test_can_sort(self, async_pg_session: AsyncSession):
        product_1_id = random_attr("id")
        await insert_food_product(
            session=async_pg_session, id=product_1_id, source="private"
        )

        product_2_id = random_attr("id")
        await insert_food_product(
            session=async_pg_session, id=product_2_id, source="taco"
        )

        product_3_id = random_attr("id")
        await insert_food_product(
            session=async_pg_session, id=product_3_id, source="gs1"
        )

        repo = ProductRepo(async_pg_session)

        p1 = await repo.get(product_1_id)
        p1.nutri_facts = random_nutri_facts()
        await repo.persist(p1)

        p2 = await repo.get(product_2_id)
        p2.nutri_facts = random_nutri_facts()
        await repo.persist(p2)

        p3 = await repo.get(product_3_id)
        p3.nutri_facts = random_nutri_facts()
        await repo.persist(p3)

        p4 = random_food_product(source_id="taco", nutri_facts=p1.nutri_facts)
        await repo.add(p4)

        p5 = random_food_product(source_id="gs1", nutri_facts=p1.nutri_facts)
        await repo.add(p5)

        result = await repo.query(filter={"sort": "calories"})
        result = [i for i in result if i.id in [p1.id, p2.id, p3.id, p4.id, p5.id]]
        for i in range(len(result) - 1):
            assert (
                result[i].nutri_facts.calories.value
                <= result[i + 1].nutri_facts.calories.value
            )
            if (
                result[i].nutri_facts.calories.value
                == result[i + 1].nutri_facts.calories.value
            ):
                for j in ["private", "taco", "gsi"]:
                    if j == result[i].source_id:
                        source_i = j
                    if j == result[i + 1].source_id:
                        source_i_plus_1 = j
                assert _source_sort_order.index(source_i) <= _source_sort_order.index(
                    source_i_plus_1
                )
        result = await repo.query(filter={"sort": "-calories"})
        result = [i for i in result if i.id in [p1.id, p2.id, p3.id, p4.id, p5.id]]
        for i in range(len(result) - 1):
            assert (
                result[i].nutri_facts.calories.value
                >= result[i + 1].nutri_facts.calories.value
            )
            if (
                result[i].nutri_facts.calories.value
                == result[i + 1].nutri_facts.calories.value
            ):
                for j in ["private", "taco", "gsi"]:
                    if j == result[i].source_id:
                        source_i = j
                    if j == result[i + 1].source_id:
                        source_i_plus_1 = j
                assert _source_sort_order.index(source_i) <= _source_sort_order.index(
                    source_i_plus_1
                )

    async def test_can_skip(self, async_pg_session: AsyncSession):
        product_1_id = random_attr("id")
        await insert_food_product(async_pg_session, product_1_id)

        product_2_id = random_attr("id")
        await insert_food_product(async_pg_session, product_2_id)

        repo = ProductRepo(async_pg_session)

        all = await repo.query()
        skipped = await repo.query(filter={"skip": 1})
        assert len(list(all)) - len(list(skipped)) == 1

    async def test_can_limit(self, async_pg_session: AsyncSession):
        product_1_id = random_attr("id")
        await insert_food_product(async_pg_session, product_1_id)

        product_2_id = random_attr("id")
        await insert_food_product(async_pg_session, product_2_id)

        repo = ProductRepo(async_pg_session)

        all = await repo.query()
        limited = await repo.query(filter={"limit": 1})
        assert len(list(all)) > 1
        assert len(list(limited)) == 1
