import pytest
from cattrs import structure
from src.contexts._receipt_tracker.shared.domain.entities.receipt import Receipt
from src.contexts._receipt_tracker.shared.domain.events import (
    ItemsAddedToReceipt,
    ReceiptAdded,
)
from src.contexts._receipt_tracker.shared.domain.value_objects.item import Item
from src.contexts.seedwork.shared.endpoints.exceptions import InvalidApiSchemaException


def test_validate_id() -> None:
    no_state = {
        "cfe_key": f"99{'0'*42}",
        "house_ids": ["1"],
    }
    with pytest.raises(InvalidApiSchemaException):
        Receipt.add_receipt(**no_state)

    not_44 = {
        "cfe_key": "1",
        "house_ids": ["1"],
    }
    with pytest.raises(InvalidApiSchemaException):
        Receipt.add_receipt(**not_44)

    letter = {
        "cfe_key": f"35{'0'*41}X",
        "house_ids": ["1"],
    }
    with pytest.raises(InvalidApiSchemaException):
        Receipt.add_receipt(**letter)


def test_add_receipt_create_ReceiptAdded_event():
    kwargs = {
        "cfe_key": f"35{'0'*42}",
        "house_ids": ["1"],
    }
    receipt = Receipt.add_receipt(**kwargs)
    event = ReceiptAdded(
        cfe_key=kwargs["cfe_key"], house_ids=kwargs["house_ids"], state="SP"
    )
    assert receipt.events[0] == event


def test_can_add_items():
    kargs = {
        "cfe_key": f"35{'0'*42}",
        "house_ids": ["1"],
    }
    receipt = Receipt.add_receipt(**kargs)
    item = {
        "description": "banana",
        "amount": {"quantity": 1.5, "unit": "un"},
        "price_paid": 1.5,
        "price_per_unit": 1.5,
        "gross_price": 1.5,
        "sellers_product_code": "00001",
        "barcode": "00001",
        "discount": 0,
    }
    receipt.add_items([structure(item, Item)] * 3)
    assert len(receipt.items) == 3
    event = ItemsAddedToReceipt(kargs["cfe_key"])
    assert event in receipt.events


def test_can_consolidate_items():
    kwargs = {
        "cfe_key": f"35{'0'*42}",
        "house_ids": ["1"],
    }
    receipt = Receipt.add_receipt(**kwargs)
    item = {
        "description": "banana",
        "amount": {"quantity": 1.0, "unit": "un"},
        "price_paid": 1.5,
        "price_per_unit": 1.5,
        "gross_price": 1.5,
        "sellers_product_code": "00001",
        "barcode": "00001",
        "discount": 0,
    }
    receipt.add_items([structure(item, Item)] * 3)
    item["number"] = 1
    item["cfe_key"] = f"35{'0'*42}"
    consolidated = structure(item, Item) + structure(item, Item) + structure(item, Item)
    assert receipt.consolidate_items() == [consolidated]
