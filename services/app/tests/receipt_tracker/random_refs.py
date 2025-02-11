import inspect
import random
import uuid
from datetime import datetime
from random import randint

from src.contexts._receipt_tracker.shared.domain.entities.receipt import Receipt
from src.contexts._receipt_tracker.shared.domain.enums import CfeStateCodes, State, Unit
from src.contexts._receipt_tracker.shared.domain.value_objects.item import Item
from src.contexts._receipt_tracker.shared.domain.value_objects.product import Product
from src.contexts._receipt_tracker.shared.domain.value_objects.seller import Seller
from src.contexts.shared_kernel.domain.value_objects import Amount
from src.contexts.shared_kernel.domain.value_objects.address import Address
from tests.utils import check_missing_attributes

# def _class_attributes(cls) -> list[str]:
#     attributes = [
#         attr
#         for attr in inspect.getmembers(cls, lambda a: not (inspect.isroutine(a)))
#         if not (attr[0].startswith("_") or attr[0] == "instance_id")
#     ]
#     return [i[0] for i in attributes]


# def _class_method_attributes(method) -> list[str]:
#     if not inspect.ismethod(method):
#         raise TypeError("The argument must be a class method.")

#     sig = inspect.signature(method)
#     return [param.name for param in sig.parameters.values() if param.name != "cls"]


# def _missing_attributes(cls_or_method, kwargs) -> list[str]:
#     if inspect.isclass(cls_or_method):
#         attribute_names = _class_attributes(cls_or_method)
#     elif inspect.ismethod(cls_or_method):
#         attribute_names = _class_method_attributes(cls_or_method)
#     else:
#         raise TypeError("The first argument must be a class or a class method.")

#     return [attr for attr in attribute_names if attr not in kwargs]


def random_suffix(module_name: str = "") -> str:
    return f"{uuid.uuid4().hex[:6]}{module_name}"


def random_attr(attr="") -> str:
    return f"{attr}-{random_suffix()}"


def random_cfe_key(state_code: int | None = None, model: int | None = None) -> str:
    if not state_code:
        state_code = int(random.choice(list(CfeStateCodes)).value)
    mid = randint(int("1" + "0" * 17), int("1" + "0" * 18))
    end = randint(int("1" + "0" * 21), int("1" + "0" * 22))
    return f"{state_code}{mid}{model or '00'}{end}"


def random_cnpj() -> str:
    return str(randint(int("1" + "0" * 13), int("1" + "0" * 14)))


def random_address_kwargs(**kwargs) -> dict:
    prefix = kwargs.get("prefix") or ""
    final_kwargs = {
        "street": (
            kwargs.get("street")
            if kwargs.get("street")
            else random_attr(f"{prefix}street")
        ),
        "number": (
            kwargs.get("number")
            if kwargs.get("number")
            else random_attr(f"{prefix}number")
        ),
        "zip_code": (
            kwargs.get("zip_code")
            if kwargs.get("zip_code")
            else random_attr(f"{prefix}zip_code")
        ),
        "district": (
            kwargs.get("district")
            if kwargs.get("district")
            else random_attr(f"{prefix}district")
        ),
        "city": (
            kwargs.get("city") if kwargs.get("city") else random_attr(f"{prefix}city")
        ),
        "state": (
            kwargs.get("state")
            if kwargs.get("state")
            else random.choice(list(State)).value
        ),
        "complement": (
            kwargs.get("complement")
            if kwargs.get("complement")
            else random_attr(f"{prefix}complement")
        ),
        "note": (
            kwargs.get("note") if kwargs.get("note") else random_attr(f"{prefix}note")
        ),
    }
    missing = check_missing_attributes(Address, final_kwargs)
    assert not missing, f"Missing attributes {missing}"
    return final_kwargs


def random_address(**kwargs) -> Address:
    return Address(**random_address_kwargs(**kwargs))


def random_seller_kwargs(
    **kwargs,
) -> dict:
    prefix = kwargs.get("prefix") or ""
    final_kwargs = {
        "cnpj": kwargs.get("cnpj") if kwargs.get("cnpj") else random_cnpj(),
        "name": (
            kwargs.get("name") if kwargs.get("name") else random_attr(f"{prefix}name")
        ),
        "state_registration": (
            kwargs.get("state_registration")
            if kwargs.get("state_registration")
            else random_attr(f"{prefix}state_registration")
        ),
        "address": kwargs.get("address") if kwargs.get("address") else random_address(),
    }
    missing = check_missing_attributes(Seller, final_kwargs)
    assert not missing, f"Missing attributes {missing}"
    return final_kwargs


def random_seller(**kwargs) -> Seller:
    return Seller(**random_seller_kwargs(**kwargs))


def random_product_kwarg(
    **kwargs,
) -> dict:
    prefix = kwargs.get("prefix") or ""
    final_kwargs = {
        "id": kwargs.get("id") if "id" in kwargs else random_attr(f"{prefix}id"),
        "source": (
            kwargs.get("source")
            if "source" in kwargs
            else random_attr(f"{prefix}source")
        ),
        "name": (
            kwargs.get("name") if "name" in kwargs else random_attr(f"{prefix}name")
        ),
        "is_food": (
            kwargs.get("is_food")
            if "is_food" in kwargs
            else random.choice([True, False])
        ),
    }
    missing = check_missing_attributes(Product, final_kwargs)
    assert not missing, f"Missing attributes {missing}"
    return final_kwargs


def random_product(**kwargs) -> Product:
    return Product(**random_product_kwarg(**kwargs))


def random_item_kwargs(
    **kwargs,
) -> dict:
    prefix = kwargs.get("prefix") or ""
    final_kwargs = {
        "description": (
            kwargs.get("description")
            if kwargs.get("description")
            else random_attr(f"{prefix}description")
        ),
        "amount": (
            kwargs.get("amount")
            if "amount" in kwargs
            else Amount(
                quantity=(
                    kwargs.get("quantity")
                    if "quantity" in kwargs
                    else round(random.uniform(0.1, 100), 2)
                ),
                unit=(
                    kwargs.get("unit")
                    if "unit" in kwargs
                    else random.choice(list(Unit))
                ),
            )
        ),
        "price_paid": (
            kwargs.get("price_paid")
            if "price_paid" in kwargs
            else round(random.uniform(0.1, 100), 2)
        ),
        "sellers_product_code": (
            kwargs.get("sellers_product_code")
            if "sellers_product_code" in kwargs
            else random_attr(f"{prefix}sellers_product_code")
        ),
        "barcode": (
            kwargs.get("barcode")
            if "barcode" in kwargs
            else str(randint(int("1" + "0" * 12), int("1" + "0" * 13)))
        ),
        "discount": kwargs.get("discount") if "discount" in kwargs else 0,
        "number": kwargs.get("number", None),
        "product": kwargs.get("product") if "product" in kwargs else random_product(),
    }
    final_kwargs["price_per_unit"] = (
        final_kwargs["price_paid"] / final_kwargs["amount"].quantity
    )
    final_kwargs["gross_price"] = final_kwargs["price_paid"]
    missing = check_missing_attributes(Item, final_kwargs)
    assert not missing, f"Missing attributes {missing}"
    return final_kwargs


def random_item(**kwargs) -> Item:
    return Item(**random_item_kwargs(**kwargs))


def random_receipt_kwargs(**kwargs) -> dict:
    prefix = kwargs.get("prefix") or ""
    final_kwargs = {
        "cfe_key": kwargs.get("cfe_key") if "cfe_key" in kwargs else random_cfe_key(),
        "house_ids": (
            kwargs.get("house_ids")
            if "house_ids" in kwargs
            else [random_attr(f"{prefix}house_id")]
        ),
        "qrcode": kwargs.get("qrcode") if "qrcode" in kwargs else None,
        # "state": kwargs.get("state")
        # if "state" in kwargs
        # else random.choice(list(State)).value,
        "date": kwargs.get("date") if "date" in kwargs else datetime.now(),
        "seller_id": (
            kwargs.get("seller_id")
            if "seller_id" in kwargs
            else random_attr(f"{prefix}seller_id")
        ),
        "scraped": kwargs.get("scraped") if "scraped" in kwargs else False,
        "products_added": (
            kwargs.get("products_added") if "products_added" in kwargs else False
        ),
        "items": kwargs.get("items") if "items" in kwargs else [],
        # "discarded": kwargs.get("discarded") if "discarded" in kwargs else False,
        # "version": kwargs.get("version") if "version" in kwargs else 1,
    }
    missing = check_missing_attributes(Receipt.add_receipt, final_kwargs)
    assert not missing, f"Missing attributes {missing}"
    return final_kwargs


def random_receipt(**kwargs) -> Receipt:
    return Receipt.add_receipt(**random_receipt_kwargs(**kwargs))
