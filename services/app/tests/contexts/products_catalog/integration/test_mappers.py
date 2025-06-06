import random
from dataclasses import asdict as dataclass_asdict
from typing import Literal

import pytest
import tests.products_catalog.utils as utils
from attrs import asdict as attrs_asdict
from sqlalchemy import inspect
from src.contexts.products_catalog.core.adapters.name_search import StrProcessor
from src.contexts.products_catalog.core.adapters.ORM.mappers.product import (
    ProductMapper,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.is_food_votes import (
    IsFoodVotesSaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.product import (
    ProductSaModel,
)
from src.contexts.products_catalog.core.domain.entities.product import Product
from src.contexts.products_catalog.core.domain.enums import Unit
from src.contexts.products_catalog.core.domain.value_objects.is_food_votes import (
    IsFoodVotes,
)
from tests.products_catalog.random_refs import (
    random_attr,
    random_barcode,
    random_nutri_facts,
    random_score,
)

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


@pytest.mark.parametrize(
    "is_food, source_id, score, nutri_facts",
    [
        (False, "auto", False, None),
        (False, "manual", False, None),
        (True, "auto", False, None),
        (True, "private", True, True),
        (True, "taco", False, True),
    ],
)
async def test_map_product(
    is_food: bool,
    source_id: Literal["auto", "manual", "private", "taco"],
    score: bool,
    nutri_facts: Literal[True] | None,
    async_pg_session,
) -> None:
    mapper = ProductMapper()
    brand_id = random_attr("brand") if source_id == "private" else None
    if brand_id:
        await utils.insert_brand(async_pg_session, brand_id)
    category_id = random_attr("category")
    await utils.insert_category(async_pg_session, category_id)
    parent_category_id = random_attr("parent_category")
    await utils.insert_category(async_pg_session, parent_category_id)
    food_group_id = random_attr("food_group")
    await utils.insert_food_group(async_pg_session, food_group_id)
    process_type_id = random_attr("process_type")
    await utils.insert_process_type(async_pg_session, process_type_id)
    domain_model = Product(
        id=random_attr("id"),
        source_id=source_id,
        name=random_attr("name"),
        shopping_name=random_attr("shopping_name"),
        store_department_name=random_attr("store_department_name"),
        recommended_brands_and_products=random_attr(
            "recommended_brands_and_products"
        ),
        edible_yield=random.uniform(0, 1),
        kg_per_unit=random.uniform(0, 100),
        liters_per_kg=random.uniform(0, 100),
        nutrition_group=random_attr("nutrition_group"),
        cooking_factor=random.uniform(0.5, 3),
        conservation_days=random.randint(0, 100),
        substitutes=random_attr("substitutes"),
        brand_id=brand_id,
        is_food=is_food,
        category_id=category_id,
        parent_category_id=parent_category_id,
        food_group_id=food_group_id,
        process_type_id=process_type_id,
        score=random_score() if score else None,
        barcode=random_barcode(),
        ingredients=random_attr("ingredients"),
        nutri_facts=random_nutri_facts() if nutri_facts else None,
        package_size=random.uniform(0, 100),
        package_size_unit=random.choice(list(Unit)).value,
        image_url=random_attr("image_url"),
        json_data=random_attr("json_data"),
        discarded=False,
        version=1,
        is_food_votes=IsFoodVotes(), # type: ignore
    )
    sa_model_is_food_votes: list[IsFoodVotesSaModel] = []
    if domain_model.is_food_votes:
        sa_model_is_food_votes: list[IsFoodVotesSaModel] = []
        for house_id in domain_model.is_food_votes.is_food_houses:
            sa_model_is_food_votes.append(
                IsFoodVotesSaModel(
                    house_id=house_id,
                    is_food=True,
                )
            )
        for house_id in domain_model.is_food_votes.is_not_food_houses:
            sa_model_is_food_votes.append(
                IsFoodVotesSaModel(
                    house_id=house_id,
                    is_food=False,
                )
            )
    sa_model = await mapper.map_domain_to_sa(async_pg_session, domain_model)
    assert sa_model.id == domain_model.id
    assert sa_model.source_id == domain_model.source_id
    assert sa_model.name == domain_model.name
    assert sa_model.preprocessed_name == StrProcessor(domain_model.name).output
    assert sa_model.shopping_name == domain_model.shopping_name
    assert sa_model.store_department_name == domain_model.store_department_name
    assert sa_model.recommended_brands_and_products == domain_model.recommended_brands_and_products
    assert sa_model.edible_yield == domain_model.edible_yield
    assert sa_model.kg_per_unit == domain_model.kg_per_unit
    assert sa_model.liters_per_kg == domain_model.liters_per_kg
    assert sa_model.nutrition_group == domain_model.nutrition_group
    assert sa_model.cooking_factor == domain_model.cooking_factor
    assert sa_model.conservation_days == domain_model.conservation_days
    assert sa_model.substitutes == domain_model.substitutes
    assert sa_model.brand_id == domain_model.brand_id
    assert sa_model.is_food == domain_model.is_food
    assert sa_model.category_id == domain_model.category_id
    assert sa_model.parent_category_id == domain_model.parent_category_id
    assert sa_model.food_group_id == domain_model.food_group_id
    assert sa_model.process_type_id == domain_model.process_type_id
    if score:
        assert sa_model.score.final_score == domain_model.score.final # type: ignore
        assert sa_model.score.ingredients_score == domain_model.score.ingredients # type: ignore
        assert sa_model.score.nutrients_score == domain_model.score.nutrients # type: ignore
    else:
        assert sa_model.score.final_score is None
        assert sa_model.score.ingredients_score is None
        assert sa_model.score.nutrients_score is None
    assert sa_model.ingredients == domain_model.ingredients
    if nutri_facts:
        assert dataclass_asdict(sa_model.nutri_facts) == {
            k: v["value"] for k, v in attrs_asdict(domain_model.nutri_facts).items()
        }
    else:
        assert set(dataclass_asdict(sa_model.nutri_facts).values()) == {None}
    assert sa_model.package_size == domain_model.package_size
    assert sa_model.package_size_unit == domain_model.package_size_unit
    assert sa_model.image_url == domain_model.image_url
    assert sa_model.json_data == domain_model.json_data
    assert sa_model.discarded == domain_model.discarded
    assert sa_model.version == domain_model.version
    assert sa_model.is_food_votes == sa_model_is_food_votes
    assert sa_model.barcode == domain_model.barcode
    assert sa_model.is_food_houses_choice == domain_model.is_food_houses_choice


    reverted_domain = mapper.map_sa_to_domain(sa_model)
    assert reverted_domain == domain_model
    assert reverted_domain.id == domain_model.id
    assert reverted_domain.source_id == domain_model.source_id
    assert reverted_domain.name == domain_model.name
    assert reverted_domain.shopping_name == domain_model.shopping_name
    assert reverted_domain.store_department_name == domain_model.store_department_name
    assert reverted_domain.recommended_brands_and_products == domain_model.recommended_brands_and_products
    assert reverted_domain.edible_yield == domain_model.edible_yield
    assert reverted_domain.kg_per_unit == domain_model.kg_per_unit
    assert reverted_domain.liters_per_kg == domain_model.liters_per_kg
    assert reverted_domain.nutrition_group == domain_model.nutrition_group
    assert reverted_domain.cooking_factor == domain_model.cooking_factor
    assert reverted_domain.conservation_days == domain_model.conservation_days
    assert reverted_domain.substitutes == domain_model.substitutes
    assert reverted_domain.brand_id == domain_model.brand_id
    assert reverted_domain.is_food == domain_model.is_food
    assert reverted_domain.category_id == domain_model.category_id
    assert reverted_domain.parent_category_id == domain_model.parent_category_id
    assert reverted_domain.food_group_id == domain_model.food_group_id
    assert reverted_domain.process_type_id == domain_model.process_type_id
    assert reverted_domain.score == domain_model.score
    assert reverted_domain.ingredients == domain_model.ingredients
    assert reverted_domain.nutri_facts == domain_model.nutri_facts
    assert reverted_domain.package_size == domain_model.package_size
    assert reverted_domain.package_size_unit == domain_model.package_size_unit
    assert reverted_domain.image_url == domain_model.image_url
    assert reverted_domain.json_data == domain_model.json_data
    assert reverted_domain.discarded == domain_model.discarded
    assert reverted_domain.version == domain_model.version
    assert reverted_domain.is_food_votes == domain_model.is_food_votes
    assert reverted_domain.barcode == domain_model.barcode
    assert reverted_domain.is_food_houses_choice == domain_model.is_food_houses_choice


async def test_if_sa_model_relationship_name_match_domain_model_attribute_name():
    inspector = inspect(ProductSaModel)
    for attribute in inspector.relationships.keys():
        assert (
            attribute in dir(Product)
            or f"{attribute}_id" in dir(Product)
            or f"{attribute}_ids" in dir(Product)
        )
