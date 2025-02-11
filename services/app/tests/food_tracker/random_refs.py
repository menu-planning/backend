import inspect
import random
import uuid
from datetime import datetime
from enum import Enum

from src.contexts.food_tracker.shared.domain.entities.house import House
from src.contexts.food_tracker.shared.domain.entities.item import Item
from src.contexts.food_tracker.shared.domain.enums import Unit
from src.contexts.food_tracker.shared.domain.value_objects.receipt import Receipt
from src.contexts.shared_kernel.domain.value_objects import Amount
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


def random_barcode() -> str:
    return f"{random.randint(100000000000, 999999999999)}"


def random_amount() -> Amount:
    return Amount(
        quantity=random.uniform(0, 1000),
        unit=random.choice(list(Unit)).value,
    )


def random_cfe_key(state_code: int | None = None, model: int | None = None) -> str:
    if not state_code:
        state_code = int(random.choice(list(CfeStateCodes)).value)
    mid = random.randint(int("1" + "0" * 17), int("1" + "0" * 18))
    end = random.randint(int("1" + "0" * 21), int("1" + "0" * 22))
    return f"{state_code}{mid}{model or '00'}{end}"


def random_receipt_kwargs(**kwargs) -> dict:
    prefix = kwargs.get("prefix") or ""
    final_kwargs = {
        "cfe_key": (kwargs.get("cfe_key") if "cfe_key" in kwargs else random_cfe_key()),
        "qrcode": kwargs.get("qrcode") if "qrcode" in kwargs else None,
    }
    missing = check_missing_attributes(Receipt, final_kwargs)
    assert not missing, f"Missing attributes {missing}"
    return final_kwargs


def random_receipt(**kwargs) -> Receipt:
    return Receipt(**random_receipt_kwargs(**kwargs))


def random_create_house_classmethod_kwargs(**kwargs):
    prefix = kwargs.get("prefix") or ""
    final_kwargs = {
        # "id": kwargs.get("id") if "id" in kwargs else random_attr(f"{prefix}id"),
        "owner_id": (
            kwargs.get("owner_id") if "owner_id" in kwargs else uuid.uuid4().hex
        ),
        "name": (
            kwargs.get("name") if "name" in kwargs else random_attr(f"{prefix}name")
        ),
        "members_ids": kwargs.get("members_ids") if "members_ids" in kwargs else set(),
        "nutritionists_ids": (
            kwargs.get("nutritionists_ids") if "nutritionists_ids" in kwargs else set()
        ),
        "pending_receipts": (
            kwargs.get("pending_receipts") if "pending_receipts" in kwargs else set()
        ),
        "added_receipts": (
            kwargs.get("added_receipts") if "added_receipts" in kwargs else set()
        ),
    }
    missing = check_missing_attributes(House.create_house, final_kwargs)
    assert not missing, f"Missing attributes {missing}"
    return final_kwargs


def random_house(**kwargs) -> House:
    return House.create_house(**random_create_house_classmethod_kwargs(**kwargs))


def random_add_item_classmethod_kwargs(**kwargs) -> dict:
    prefix = kwargs.get("prefix") or ""
    final_kwargs = {
        # "id": kwargs.get("id") if "id" in kwargs else random_attr(f"{prefix}id"),
        "house_id": (
            kwargs.get("house_id")
            if "house_id" in kwargs
            else random_attr(f"{prefix}house_id")
        ),
        "date": kwargs.get("date") if "date" in kwargs else datetime.now(),
        "description": (
            kwargs.get("description")
            if "description" in kwargs
            else random_attr(f"{prefix}description")
        ),
        "amount": kwargs.get("amount") if "amount" in kwargs else random_amount(),
        "is_food": kwargs.get("is_food") if "is_food" in kwargs else True,
        "price_per_unit": (
            kwargs.get("price_per_unit")
            if "price_per_unit" in kwargs
            else random.uniform(0, 1000)
        ),
        "barcode": kwargs.get("barcode") if "barcode" in kwargs else random_barcode(),
        "cfe_key": (kwargs.get("cfe_key") if "cfe_key" in kwargs else random_cfe_key()),
        "product_id": (
            kwargs.get("product_id")
            if "product_id" in kwargs
            else random_attr(f"{prefix}product_id")
        ),
        # "top_similar_names": kwargs.get("top_similar_names")
        # if "top_similar_names" in kwargs
        # else None,
    }
    missing = check_missing_attributes(Item.add_item, final_kwargs)
    assert not missing, f"Missing attributes {missing}"
    return final_kwargs


def random_item(**kwargs) -> Item:
    return Item.add_item(**random_add_item_classmethod_kwargs(**kwargs))


class CfeStateCodes(Enum):
    AC = 12
    AL = 27
    AP = 16
    AM = 13
    BA = 29
    CE = 23
    DF = 53
    ES = 32
    GO = 52
    MA = 21
    MT = 51
    MS = 50
    MG = 31
    PA = 15
    PB = 25
    PR = 41
    PE = 26
    PI = 22
    RJ = 33
    RN = 24
    RS = 43
    RO = 11
    RR = 14
    SC = 42
    SP = 35
    SE = 28
    TO = 17

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, State) and self.value == __o.value


class State(Enum):
    AC = "AC"
    AL = "AL"
    AP = "AP"
    AM = "AM"
    BA = "BA"
    CE = "CE"
    DF = "DF"
    ES = "ES"
    GO = "GO"
    MA = "MA"
    MT = "MT"
    MS = "MS"
    MG = "MG"
    PA = "PA"
    PB = "PB"
    PR = "PR"
    PE = "PE"
    PI = "PI"
    RJ = "RJ"
    RN = "RN"
    RS = "RS"
    RO = "RO"
    RR = "RR"
    SC = "SC"
    SP = "SP"
    SE = "SE"
    TO = "TO"

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, State) and self.value == __o.value
