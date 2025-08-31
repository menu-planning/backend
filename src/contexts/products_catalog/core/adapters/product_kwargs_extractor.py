import json
from collections import abc
from collections.abc import Callable
from typing import Any, Type


def traverse(
    *, keys: list, type: type, data: Any, nutri_fact_value_normalizer: float = 1
) -> Any:
    if not keys:
        if type == str and isinstance(data, abc.MutableSequence):
            return data.pop(0)
        try:
            return type(data) / nutri_fact_value_normalizer
        except Exception:
            if type == float or type == int:
                return 0
            return data
    i = keys.pop(0)
    try:
        return traverse(
            keys=keys,
            type=type,
            data=data[i],
            nutri_fact_value_normalizer=nutri_fact_value_normalizer,
        )
    except Exception:
        if type == float or type == int:
            return 0
        raise Exception(f"Error while traversing {keys} in {data}")


def taco_extractor(data: dict) -> dict[str, Any]:
    return {
        "source": "taco",
        "name": traverse(keys=["description"], type=str, data=data),
        "brand": "",
        "barcode": "",
        "is_food": True,
        "category": traverse(keys=["category_id"], type=str, data=data),
        "parent_category": traverse(keys=["category_id"], type=str, data=data),
        "ingredients": None,
        "package_size": "",
        "package_size_unit": "g",
        "score": {
            "final": None,
            "ingredients": None,
            "nutrients": None,
        },
        "nutri_facts": {
            "calories": traverse(
                keys=["attributes", "energy", "kcal"], type=float, data=data
            ),
            "protein": traverse(
                keys=["attributes", "protein", "qty"], type=float, data=data
            ),
            "carbohydrate": traverse(
                keys=["attributes", "carbohydrate", "qty"], type=float, data=data
            ),
            "total_fat": traverse(
                keys=["attributes", "lipid", "qty"], type=float, data=data
            ),
            "saturated_fat": traverse(
                keys=["attributes", "fatty_acids", "saturated", "qty"],
                type=float,
                data=data,
            ),
            "dietary_fiber": traverse(
                keys=["attributes", "fiber", "qty"], type=float, data=data
            ),
            "sodium": traverse(
                keys=["attributes", "sodium", "qty"], type=float, data=data
            ),
            "arachidonic_acid": traverse(
                keys=["attributes", "fatty_acids", "20:4", "qty"], type=float, data=data
            ),
            "ashes": traverse(
                keys=["attributes", "ashes", "qty"], type=float, data=data
            ),
            "dha": traverse(
                keys=["attributes", "fatty_acids", "22:6", "qty"], type=float, data=data
            ),
            "epa": traverse(
                keys=["attributes", "fatty_acids", "20:5", "qty"], type=float, data=data
            ),
            "calcium": traverse(
                keys=["attributes", "calcium", "qty"], type=float, data=data
            ),
            "copper": traverse(
                keys=["attributes", "copper", "qty"], type=float, data=data
            ),
            "cholesterol": traverse(
                keys=["attributes", "cholesterol", "qty"], type=float, data=data
            ),
            "iron": traverse(keys=["attributes", "iron", "qty"], type=float, data=data),
            "phosphorus": traverse(
                keys=["attributes", "phosphorus", "qty"], type=float, data=data
            ),
            "monounsaturated_fat": traverse(
                keys=["attributes", "fatty_acids", "monounsaturated", "qty"],
                type=float,
                data=data,
            ),
            "polyunsaturated_fat": traverse(
                keys=["attributes", "fatty_acids", "polyunsaturated", "qty"],
                type=float,
                data=data,
            ),
            "magnesium": traverse(
                keys=["attributes", "magnesium", "qty"], type=float, data=data
            ),
            "manganese": traverse(
                keys=["attributes", "manganese", "qty"], type=float, data=data
            ),
            "linolenic_acid": traverse(
                keys=["attributes", "fatty_acids", "18:3 n-3", "qty"],
                type=float,
                data=data,
            ),
            "linoleic_acid": traverse(
                keys=["attributes", "fatty_acids", "18:2 n-6", "qty"],
                type=float,
                data=data,
            ),
            "oleic_acid": traverse(
                keys=["attributes", "fatty_acids", "18:1", "qty"], type=float, data=data
            ),
            "potassium": traverse(
                keys=["attributes", "potassium", "qty"], type=float, data=data
            ),
            "vitamin_c": traverse(keys=["vitaminC", "qty"], type=float, data=data),
            "zinc": traverse(keys=["attributes", "zinc", "qty"], type=float, data=data),
            "retinol": traverse(
                keys=["attributes", "retinol", "qty"], type=float, data=data
            ),
            "thiamine": traverse(
                keys=["attributes", "thiamine", "qty"], type=float, data=data
            ),
            "riboflavin": traverse(
                keys=["attributes", "riboflavin", "qty"], type=float, data=data
            ),
            "pyridoxine": traverse(
                keys=["attributes", "pyidoxine", "qty"], type=float, data=data
            ),
            "niacin": traverse(
                keys=["attributes", "niacin", "qty"], type=float, data=data
            ),
        },
    }


def private_extractor(data: dict) -> dict[str, Any]:
    nutri_fact_value_normalizer = 1
    if serving_size := traverse(
        keys=["nutrition_facts", "serving_size"],
        type=float,
        data=data,
    ):
        nutri_fact_value_normalizer = serving_size / 100
    return {
        "source": "private",
        "name": traverse(keys=["name"], type=str, data=data),
        "category": traverse(keys=["category"], type=str, data=data),
        "parent_category": traverse(keys=["parent_category"], type=str, data=data),
        "brand": traverse(keys=["brands"], type=str, data=data),
        "barcode": traverse(keys=["barcode"], type=str, data=data),
        "ingredients": traverse(keys=["ingredients_text"], type=str, data=data),
        "package_size": traverse(keys=["package_size"], type=str, data=data),
        "package_size_unit": traverse(keys=["package_size_unit"], type=str, data=data),
        "is_food": True,
        "score": {
            "final": traverse(keys=["score", "final"], type=float, data=data),
            "ingredients": traverse(
                keys=["score", "ingredients"], type=float, data=data
            ),
            "nutrients": traverse(keys=["score", "nutrients"], type=float, data=data),
        },
        "nutri_facts": {
            "calories": traverse(
                keys=["nutrition_facts", "calories"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "protein": traverse(
                keys=["nutrition_facts", "protein"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "carbohydrate": traverse(
                keys=["nutrition_facts", "carbohydrate"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "total_fat": traverse(
                keys=["nutrition_facts", "total_fat"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "saturated_fat": traverse(
                keys=["nutrition_facts", "saturated_fat"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "trans_fat": traverse(
                keys=["nutrition_facts", "trans_fat"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "dietary_fiber": traverse(
                keys=["nutrition_facts", "dietary_fiber"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "sodium": traverse(
                keys=["nutrition_facts", "sodium"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "arachidonic_acid": traverse(
                keys=["nutrition_facts", "arachidonic_acid"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "ashes": traverse(
                keys=["nutrition_facts", "ashes"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "dha": traverse(
                keys=["nutrition_facts", "dha"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "epa": traverse(
                keys=["nutrition_facts", "epa"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "sugar": traverse(
                keys=["nutrition_facts", "sugar"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "starch": traverse(
                keys=["nutrition_facts", "starch"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "biotin": traverse(
                keys=["nutrition_facts", "biotin"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "boro": traverse(
                keys=["nutrition_facts", "boro"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "caffeine": traverse(
                keys=["nutrition_facts", "caffeine"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "calcium": traverse(
                keys=["nutrition_facts", "calcium"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "chlorine": traverse(
                keys=["nutrition_facts", "chlorine"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "copper": traverse(
                keys=["nutrition_facts", "copper"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "cholesterol": traverse(
                keys=["nutrition_facts", "cholesterol"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "choline": traverse(
                keys=["nutrition_facts", "choline"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "chrome": traverse(
                keys=["nutrition_facts", "chrome"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "dextrose": traverse(
                keys=["nutrition_facts", "dextrose"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "sulfur": traverse(
                keys=["nutrition_facts", "sulfur"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "phenylalanine": traverse(
                keys=["nutrition_facts", "phenylalanine"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "iron": traverse(
                keys=["nutrition_facts", "iron"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "insoluble_fiber": traverse(
                keys=["nutrition_facts", "insoluble_fiber"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "soluble_fiber": traverse(
                keys=["nutrition_facts", "soluble_fiber"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "fluor": traverse(
                keys=["nutrition_facts", "fluor"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "phosphorus": traverse(
                keys=["nutrition_facts", "phosphorus"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "fructo_oligosaccharides": traverse(
                keys=["nutrition_facts", "fructo_oligosaccharides"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "fructose": traverse(
                keys=["nutrition_facts", "fructose"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "galacto_oligosaccharides": traverse(
                keys=["nutrition_facts", "galacto_oligosaccharides"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "galactose": traverse(
                keys=["nutrition_facts", "galactose"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "glucose": traverse(
                keys=["nutrition_facts", "glucose"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "glucoronolactone": traverse(
                keys=["nutrition_facts", "glucoronolactone"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "monounsaturated_fat": traverse(
                keys=["nutrition_facts", "monounsaturated_fat"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "polyunsaturated_fat": traverse(
                keys=["nutrition_facts", "polyunsaturated_fat"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "guarana": traverse(
                keys=["nutrition_facts", "guarana"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "inositol": traverse(
                keys=["nutrition_facts", "inositol"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "inulin": traverse(
                keys=["nutrition_facts", "inulin"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "iodine": traverse(
                keys=["nutrition_facts", "iodine"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "l_carnitine": traverse(
                keys=["nutrition_facts", "l_carnitine"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "l_methionine": traverse(
                keys=["nutrition_facts", "l_methionine"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "lactose": traverse(
                keys=["nutrition_facts", "lactose"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "magnesium": traverse(
                keys=["nutrition_facts", "magnesium"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "maltose": traverse(
                keys=["nutrition_facts", "maltose"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "manganese": traverse(
                keys=["nutrition_facts", "manganese"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "molybdenum": traverse(
                keys=["nutrition_facts", "molybdenum"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "linolenic_acid": traverse(
                keys=["nutrition_facts", "linolenic_acid"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "linoleic_acid": traverse(
                keys=["nutrition_facts", "linoleic_acid"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "omega_7": traverse(
                keys=["nutrition_facts", "omega_7"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "omega_9": traverse(
                keys=["nutrition_facts", "omega_9"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "oleic_acid": traverse(
                keys=["nutrition_facts", "oleic_acid"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "other_carbo": traverse(
                keys=["nutrition_facts", "other_carbo"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "polydextrose": traverse(
                keys=["nutrition_facts", "polydextrose"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "polyols": traverse(
                keys=["nutrition_facts", "polyols"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "potassium": traverse(
                keys=["nutrition_facts", "potassium"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "sacarose": traverse(
                keys=["nutrition_facts", "sacarose"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "selenium": traverse(
                keys=["nutrition_facts", "selenium"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "silicon": traverse(
                keys=["nutrition_facts", "silicon"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "sorbitol": traverse(
                keys=["nutrition_facts", "sorbitol"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "sucralose": traverse(
                keys=["nutrition_facts", "sucralose"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "taurine": traverse(
                keys=["nutrition_facts", "taurine"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "vitamin_a": traverse(
                keys=["nutrition_facts", "vitamin_a"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "vitamin_b1": traverse(
                keys=["nutrition_facts", "vitamin_b1"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "vitamin_b2": traverse(
                keys=["nutrition_facts", "vitamin_b2"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "vitamin_b3": traverse(
                keys=["nutrition_facts", "vitamin_b3"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "vitamin_b5": traverse(
                keys=["nutrition_facts", "vitamin_b5"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "vitamin_b6": traverse(
                keys=["nutrition_facts", "vitamin_b6"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "folic_acid": traverse(
                keys=["nutrition_facts", "folic_acid"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "vitamin_b12": traverse(
                keys=["nutrition_facts", "vitamin_b12"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "vitamin_c": traverse(
                keys=["nutrition_facts", "vitamin_c"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "vitamin_d": traverse(
                keys=["nutrition_facts", "vitamin_d"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "vitamin_e": traverse(
                keys=["nutrition_facts", "vitamin_e"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "vitamin_k": traverse(
                keys=["nutrition_facts", "vitamin_k"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
            "zinc": traverse(
                keys=["nutrition_facts", "zinc"],
                type=float,
                data=data,
                nutri_fact_value_normalizer=nutri_fact_value_normalizer,
            ),
        },
    }


class ProductKwargsExtractor:
    def __init__(
        self,
        data: list[dict],
        extractor: Callable[..., dict[str, Any]],
        nutri_factor_divider: tuple | None = None,
    ) -> None:
        self.data = data
        self.extractor = extractor
        self.nutri_factor_divider = nutri_factor_divider

    @property
    def kwargs(self) -> list[dict[str, Any]]:
        product_list_kwargs: list[dict[str, Any]] = []
        for product in self.data:
            kwargs = self.extractor(product)
            kwargs["json_data"] = json.dumps(product, ensure_ascii=False)
            if all([i == 0 for i in kwargs["score"].values()]):
                # kwargs["score"] = asdict(Score())
                kwargs["score"] = None
            product_list_kwargs.append(kwargs)
        return product_list_kwargs

    @classmethod
    def from_path(cls, path):
        try:
            f = open(path)
            txt = f.read()
            data = json.loads(txt)
            if "private" in path:
                return cls.from_private(data)
            elif "taco" in path:
                return cls.from_taco(data)
            else:
                raise NotImplementedError
        except Exception:
            return path

    @classmethod
    def from_private(
        cls,
        data: list[dict],
        extractor: Callable[..., dict[str, Any]] = private_extractor,
    ):
        return cls(data, extractor, ("nutrition_facts", "serving_size"))

    @classmethod
    def from_taco(
        cls, data: list[dict], extractor: Callable[..., dict[str, Any]] = taco_extractor
    ):
        return cls(data, extractor)


class ProductKwargsExtractorFactory:
    def __init__(self):
        self._extractor: dict[str, Callable] = {
            "private": ProductKwargsExtractor.from_private,
            "taco": ProductKwargsExtractor.from_taco,
        }

    def get_extractor(self, source: str) -> Callable[..., ProductKwargsExtractor]:
        return self._extractor[source]
