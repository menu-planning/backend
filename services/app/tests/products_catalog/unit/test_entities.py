import pytest
from src.contexts.products_catalog.shared.domain.entities.product import Product
from tests.products_catalog.random_refs import random_attr, random_food_product_kwargs


def test_can_add_and_remove_diet_type_from_product():
    kwargs = random_food_product_kwargs()
    product = Product.add_food_product(**kwargs)
    product.add_diet_types_ids("vegan")
    assert "vegan" in product.diet_types_ids
    product.remove_diet_types_ids("vegan")
    assert "vegan" not in product.diet_types_ids


@pytest.mark.parametrize(
    "is_food,is_not_food,result",
    [
        (2, 0, None),
        (3, 0, True),
        (3, 2, None),
        (4, 1, True),
        (4, 2, None),
        (5, 2, True),
        (5, 3, None),
    ],
)
def test_can_compute_users_is_food_input(is_food, is_not_food, result):
    kwargs = random_food_product_kwargs()
    product = Product.add_food_product(**kwargs)
    for _ in range(is_food):
        product.add_house_input_to_is_food_registry(random_attr("id"), True)
    for _ in range(is_not_food):
        product.add_house_input_to_is_food_registry(random_attr("id"), False)
    assert len(product._is_food_votes.is_food_houses) == is_food
    assert len(product._is_food_votes.is_not_food_houses) == is_not_food
    assert product.is_food_houses_choice == result
