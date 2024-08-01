import pytest
from cattrs import structure
from src.contexts.receipt_tracker.shared.domain.enums import Unit
from src.contexts.receipt_tracker.shared.domain.value_objects.item import Item
from src.contexts.shared_kernel.domain.value_objects import Amount


def test_can_add_amount():
    a = Amount(quantity=1, unit=Unit.kilogram.value)
    b = Amount(quantity=2, unit=Unit.kilogram.value)
    assert a + b == Amount(quantity=3, unit=Unit.kilogram.value)


def test_cannot_add_amount_with_different_units():
    a = Amount(quantity=1, unit=Unit.kilogram.value)
    b = Amount(quantity=2, unit=Unit.unit.value)
    with pytest.raises(TypeError):
        a + b


def test_can_add_item():
    item = {
        "number": 1,
        "description": "banana",
        "amount": {"quantity": 1.5, "unit": "un"},
        "price_paid": 1.5,
        "price_per_unit": 1.5,
        "gross_price": 1.5,
        "sellers_product_code": "00001",
        "barcode": "00001",
        "discount": 0,
    }
    a = structure(item, Item)
    b = structure(item, Item)
    c = a + b
    assert c.amount == a.amount + b.amount
    assert c.price_paid == a.price_paid + b.price_paid
    assert c.gross_price == a.gross_price + b.gross_price
    assert c.discount == a.discount + b.discount
