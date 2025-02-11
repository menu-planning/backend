from datetime import datetime

import pytest
from cattrs import structure
from src.contexts._receipt_tracker.shared.adapters.api_schemas.commands.add_receipt import (
    ApiAddReceipt,
)
from src.contexts._receipt_tracker.shared.adapters.api_schemas.entities.receipt import (
    ApiReceipt,
)
from src.contexts._receipt_tracker.shared.adapters.api_schemas.value_objects.item import (
    ApiItem,
)
from src.contexts._receipt_tracker.shared.adapters.api_schemas.value_objects.seller import (
    ApiSeller,
)
from src.contexts._receipt_tracker.shared.domain.commands import AddReceipt
from src.contexts._receipt_tracker.shared.domain.entities.receipt import Receipt
from src.contexts._receipt_tracker.shared.domain.value_objects.item import Item
from src.contexts._receipt_tracker.shared.domain.value_objects.seller import Seller
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.address import (
    ApiAddress,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.amount import (
    ApiAmount,
)
from src.contexts.shared_kernel.domain.value_objects import Amount
from src.contexts.shared_kernel.domain.value_objects.address import Address


def test_api_address() -> None:
    address = {
        "street": "street",
        "number": "number",
        "zip_code": "zip_code",
        "district": "district",
        "city": "city",
        "state": "SP",
    }
    domain_address = structure(address, Address)
    api_address = ApiAddress(**address)
    assert ApiAddress.to_domain(api_address) == domain_address
    assert ApiAddress.from_domain(domain_address) == api_address


def test_invalid_state() -> None:
    address = {
        "street": "street",
        "number": "number",
        "zip_code": "zip_code",
        "district": "district",
        "city": "city",
        "state": "XX",
    }
    with pytest.raises(ValueError):
        ApiAddress.model_validate(address)


def test_api_seller() -> None:
    seller = {
        "name": "name",
        "cnpj": "12345678901234",
        "state_registration": "state_registration",
        "address": {
            "street": "street",
            "number": "number",
            "zip_code": "zip_code",
            "district": "district",
            "city": "city",
            "state": "SP",
        },
    }

    domain_seller = structure(seller, Seller)
    api_seller = ApiSeller(**seller)
    assert ApiSeller.to_domain(api_seller) == domain_seller
    assert ApiSeller.from_domain(domain_seller) == api_seller


def test_api_amount() -> None:
    amount = {
        "quantity": 1.5,
        "unit": "un",
    }
    domain_amount = structure(amount, Amount)
    api_amount = ApiAmount(**amount)
    assert ApiAmount.to_domain(api_amount) == domain_amount
    assert ApiAmount.from_domain(domain_amount) == api_amount


def test_invalid_quantity() -> None:
    item = {
        "number": 1,
        "description": "banana",
        "amount": {"quantity": -1.5, "unit": "un"},
        "price_paid": 1.5,
        "price_per_unit": 1.5,
        "gross_price": 1.5,
        "sellers_product_code": "00001",
        "barcode": "00001",
        "discount": 0,
    }
    with pytest.raises(ValueError):
        ApiItem.model_validate(item)


def test_invalid_unit() -> None:
    item = {
        "number": 1,
        "description": "banana",
        "amount": {"quantity": 1.5, "unit": "wrong"},
        "price_paid": 1.5,
        "price_per_unit": 1.5,
        "gross_price": 1.5,
        "sellers_product_code": "00001",
        "barcode": "00001",
        "discount": 0,
    }
    with pytest.raises(ValueError):
        ApiItem.model_validate(item)


def test_api_item() -> None:
    item = {
        "cfe_key": f"35{'0'*42}",
        "number": 1,
        "description": "banana",
        "amount": {"quantity": 1.5, "unit": "un"},
        "price_paid": 1.5,
        "price_per_unit": 1.5,
        "gross_price": 1.5,
        "sellers_product_code": "00001",
        "barcode": "00001",
        "discount": 0,
        "product": {
            "id": "1",
            "source": "source",
            "name": "name",
            "is_food": True,
        },
    }

    domain_item = structure(item, Item)
    api_item = ApiItem(**item)
    assert ApiItem.to_domain(api_item) == domain_item
    assert ApiItem.from_domain(domain_item) == api_item


def test_api_receipt() -> None:
    item = {
        "cfe_key": f"35{'0'*42}",
        "number": 1,
        "description": "banana",
        "amount": {"quantity": 1.5, "unit": "un"},
        "price_paid": 1.5,
        "price_per_unit": 1.5,
        "gross_price": 1.5,
        "sellers_product_code": "00001",
        "barcode": "00001",
        "discount": 0,
        "product": {
            "id": "1",
            "source": "source",
            "name": "name",
            "is_food": True,
        },
    }
    receipt = {
        "cfe_key": f"35{'0'*42}",
        "state": "SP",
        "house_ids": ["1"],
        "date": datetime.now(),
        "items": [
            structure(item, Item),
        ],
    }

    domain_receipt = Receipt(**receipt)
    receipt["items"] = [item]
    api_receipt = ApiReceipt(**receipt)
    assert ApiReceipt.to_domain(api_receipt) == domain_receipt
    assert ApiReceipt.from_domain(domain_receipt) == api_receipt


def test_validate_id() -> None:
    no_state = {
        "cfe_key": f"99{'0'*42}",
        "house_ids": ["1"],
    }
    with pytest.raises(ValueError):
        ApiReceipt.model_validate(no_state)

    not_44 = {
        "cfe_key": "1",
        "house_ids": ["1"],
    }
    with pytest.raises(ValueError):
        ApiReceipt.model_validate(not_44)

    letter = {
        "cfe_key": f"35{'0'*41}X",
        "house_ids": ["1"],
    }
    with pytest.raises(ValueError):
        ApiReceipt.model_validate(letter)


def test_add_receipt_cmd() -> None:
    no_state = {
        "cfe_key": f"99{'0'*42}",
        "house_id": "1",
    }
    with pytest.raises(ValueError):
        ApiAddReceipt.model_validate(no_state)

    not_44 = {
        "cfe_key": "1",
        "house_id": "1",
    }
    with pytest.raises(ValueError):
        ApiAddReceipt.model_validate(not_44)

    letter = {
        "cfe_key": f"35{'0'*41}X",
        "house_id": "1",
    }
    with pytest.raises(ValueError):
        ApiAddReceipt.model_validate(letter)

    valid = {
        "cfe_key": f"35{'0'*42}",
        "house_id": "1",
    }
    ApiAddReceipt.model_validate(valid) == ApiAddReceipt.from_domain(
        AddReceipt(**valid)
    )


class TestApiFilter:
    @pytest.mark.skip()
    def test_receipt_api_filters_match_repository_filters(self) -> None:
        # TODO: Implement this test
        pass

    @pytest.mark.skip()
    def test_seller_api_filters_match_repository_filters(self) -> None:
        # TODO: Implement this test
        pass
