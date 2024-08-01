import random
import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError
from src.contexts.food_tracker.shared.adapters.api_schemas.commands.items.commands_api_schema import (
    ApiUpdateItem,
)
from src.contexts.food_tracker.shared.adapters.api_schemas.entities.house import (
    ApiHouse,
)
from src.contexts.food_tracker.shared.adapters.api_schemas.entities.item import ApiItem
from src.contexts.food_tracker.shared.adapters.api_schemas.value_objects.receipt import (
    ApiReceipt,
)
from src.contexts.food_tracker.shared.domain.entities.item import Item
from src.contexts.food_tracker.shared.domain.enums import Unit
from src.contexts.shared_kernel.domain.value_objects import Amount
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.amount import (
    ApiAmount,
)
from tests.food_tracker.random_refs import random_attr, random_barcode, random_house


def _deep_dict_equal(dict1, dict2):
    """
    Recursively checks if two dictionaries are equal, accounting for nested dictionaries
    and lists containing dictionaries as their items.
    """
    if isinstance(dict1, dict) and isinstance(dict2, dict):
        if dict1.keys() != dict2.keys():
            return False
        for key in dict1:
            if not _deep_dict_equal(dict1[key], dict2[key]):
                return False
        return True
    elif isinstance(dict1, list) and isinstance(dict2, list):
        # Ensure both lists contain the same dictionaries, regardless of order
        if len(dict1) != len(dict2):
            return False
        for item in dict1:
            # Check each item in dict1 to see if there is an equivalent in dict2
            if isinstance(item, dict):
                if not any(_deep_dict_equal(item, d2_item) for d2_item in dict2):
                    return False
            else:
                # For non-dict items, just ensure the item is present in dict2
                if item not in dict2:
                    return False
        return True
    else:
        return dict1 == dict2


class TestItem:
    def test_api_item_from_and_to_domain(self) -> None:
        item = Item(
            id=uuid.uuid4().hex,
            house_id=uuid.uuid4().hex,
            date=datetime.now(),
            description=random_attr("description"),
            amount=Amount(
                quantity=random.uniform(0, 100),
                unit=random.choice([p.value for p in Unit]),
            ),
            is_food=random.choice([True, False]),
            price_per_unit=random.uniform(0, 100),
            barcode=random_barcode(),
            cfe_key=random_attr("cfe_key"),
            product_id=uuid.uuid4().hex,
            ids_of_productos_with_similar_names=set(
                [uuid.uuid4().hex, uuid.uuid4().hex]
            ),
        )
        api_item = ApiItem.from_domain(item)
        assert api_item.id == item.id
        assert api_item.house_id == item.house_id
        assert api_item.date == item.date
        assert api_item.description == item.description
        assert api_item.amount == ApiAmount.from_domain(item.amount)
        assert api_item.is_food == item.is_food
        assert api_item.price_per_unit == item.price_per_unit
        assert api_item.barcode == item.barcode
        assert api_item.cfe_key == item.cfe_key
        assert api_item.product_id == item.product_id
        assert (
            set([i.hex for i in api_item.ids_of_products_with_similar_names])
            == item.ids_of_products_with_similar_names
        )

    def test_update_item_to_domain(self) -> None:
        with pytest.raises(ValidationError):
            missing_item_id = ApiUpdateItem(
                updates={
                    "date": datetime.now(),
                    "description": random_attr("description"),
                    "amount": ApiAmount(
                        quantity=random.uniform(0, 100),
                        unit=random.choice([p.value for p in Unit]),
                    ),
                    "is_food": random.choice([True, False]),
                    "price_per_unit": random.uniform(0, 100),
                    "product_id": random_attr("product_id"),
                }
            )
            missing_item_id.item_id = uuid.uuid4().hex
            domain_cmd = missing_item_id.to_domain()
            assert domain_cmd.item_id == missing_item_id.item_id
            assert _deep_dict_equal(domain_cmd.updates, missing_item_id.updates)


class TestHouse:
    def test_api_house_from_and_to_domain(self) -> None:
        house = random_house()
        api_house = ApiHouse.from_domain(house)
        assert api_house.id == house.id
        assert api_house.owner_id == house.owner_id
        assert api_house.name == house.name
        assert set(api_house.members_ids) == house.members_ids
        assert set(api_house.nutritionists_ids) == house.nutritionists_ids
        assert api_house.pending_receipts == set(
            [ApiReceipt.from_domain(r) for r in house.pending_receipts]
        )
        assert api_house.added_receipts == set(
            [ApiReceipt.from_domain(r) for r in house.added_receipts]
        )
        assert api_house.discarded == house.discarded
        assert api_house.version == house.version

        reverse_domain = api_house.to_domain()
        assert reverse_domain.id == house.id
        assert reverse_domain.owner_id == house.owner_id
        assert reverse_domain.name == house.name
        assert reverse_domain.members_ids == house.members_ids
        assert reverse_domain.nutritionists_ids == house.nutritionists_ids
        assert reverse_domain.pending_receipts == house.pending_receipts
        assert reverse_domain.added_receipts == house.added_receipts
        assert reverse_domain.discarded == house.discarded
        assert reverse_domain.version == house.version
