from collections.abc import MutableMapping
from random import randrange

KEY_MAP = {
    "descrição": "description",
    "qtd. comercial": "quantity",
    "cód. produto": "sellers_product_code",
    "cód. gtin": "barcode",
    "unid. comercial": "unit",
    "valor líquido do item": "price_paid",
    "valor unit.": "price_per_unit",
    "valor bruto": "gross_price",
    "valor do desconto": "discount",
}

VALUE_MAP = {
    "un": "un",
    "kg": "kg",
    "pc": "un",
    "fr": "un",
    "gl": "un",
}


def parse_scraped_item(data: dict) -> dict:
    """
    Parse the data scraped from SP Fazenda
    Arguments:
        data: an dict
    Returns:
        a dict with the data parsed to match a ReceiptItem init arguments
    """
    parsed_data = {}
    for key, value in data.items():
        if key in KEY_MAP:
            if isinstance(value, str) and value.lower() in VALUE_MAP:
                parsed_data[KEY_MAP[key]] = VALUE_MAP[value.lower()]
            elif key == "valor do desconto":
                try:
                    float(value)
                    parsed_data[KEY_MAP[key]] = value
                except Exception:
                    parsed_data[KEY_MAP[key]] = 0
            elif key == "cód. gtin" or key == "cód. produto":
                try:
                    int(value)
                    parsed_data[KEY_MAP[key]] = value
                except Exception:
                    parsed_data[KEY_MAP[key]] = str(randrange(99999))

            else:
                parsed_data[KEY_MAP[key]] = value
    try:
        Unit(parsed_data["unit"])
        parsed_data["amount"] = {
            "unit": parsed_data["unit"],
            "quantity": parsed_data["quantity"],
        }
    except Exception:
        parsed_data["amount"] = {
            "unit": "un",
            "quantity": parsed_data["quantity"],
        }
    del parsed_data["unit"]
    del parsed_data["quantity"]
    return parsed_data


def flatten_dict(
    d: MutableMapping,
    parent_key: str = "",
    sep: str = ".",
    keep_parent_name: bool = True,
) -> MutableMapping:
    items = []
    for k, v in d.items():
        new_key = (
            (parent_key + sep if keep_parent_name else "") + k if parent_key else k
        )
        if isinstance(v, MutableMapping):
            items.extend(
                flatten_dict(
                    d=v,
                    parent_key=new_key,
                    sep=sep,
                    keep_parent_name=keep_parent_name,
                ).items()
            )
        else:
            items.append((new_key, v))
    return dict(items)
