import inspect
import random
import uuid
from enum import Enum, unique

from src.contexts.products_catalog.shared.domain.commands import AddFoodProduct
from src.contexts.products_catalog.shared.domain.entities.product import Product
from src.contexts.products_catalog.shared.domain.entities.tags import (
    Brand,
    Category,
    FoodGroup,
    ParentCategory,
    ProcessType,
    Source,
    Tag,
)
from src.contexts.products_catalog.shared.domain.enums import Unit
from src.contexts.products_catalog.shared.domain.value_objects.role import Role
from src.contexts.products_catalog.shared.domain.value_objects.score import Score
from src.contexts.products_catalog.shared.domain.value_objects.user import User
from src.contexts.shared_kernel.domain.entities.diet_type import DietType
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


def _class_attributes(cls) -> list[str]:
    attributes = [
        attr
        for attr in inspect.getmembers(cls, lambda a: not (inspect.isroutine(a)))
        if not (attr[0].startswith("_") or attr[0] == "instance_id")
    ]
    return [i[0] for i in attributes]


def _missing_attributes(cls, kwargs) -> list[str]:
    attribute_names = _class_attributes(cls)
    return [attr for attr in attribute_names if attr not in kwargs]


def random_suffix(module_name: str = "") -> str:
    return f"{uuid.uuid4().hex[:6]}{module_name}"


def random_attr(attr="") -> str:
    return f"{attr}-{random_suffix()}"


def random_score_kwargs(**kwargs):
    kwargs["nutrients"] = random.uniform(0, 100)
    kwargs["ingredients"] = random.uniform(0, 100)
    kwargs["final"] = (kwargs["nutrients"] + kwargs["ingredients"]) / 2
    missing = _missing_attributes(Score, kwargs)
    assert not missing, f"Missing attributes {missing}"
    return kwargs


def random_score(**kwargs) -> Score:
    return Score(**random_score_kwargs(**kwargs))


def random_barcode() -> str:
    return f"{random.randint(100000000000, 999999999999)}"


def random_nutri_facts_kwargs(**kwargs):
    for i in inspect.signature(NutriFacts).parameters:
        kwargs[i] = kwargs.get(i) or random.uniform(0, 1000)
    missing = _missing_attributes(NutriFacts, kwargs)
    assert not missing, f"Missing attributes {missing}"
    return kwargs


def random_nutri_facts(**kwargs) -> NutriFacts:
    return NutriFacts(**random_nutri_facts_kwargs(**kwargs))


def random_user_kwargs(**kwargs) -> dict:
    final_kwargs = {
        "id": kwargs.get("id") if "id" in kwargs else random_attr("user_id"),
        "roles": (kwargs.get("roles") if "roles" in kwargs else []),
    }
    missing = _missing_attributes(User, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_user(**kwargs) -> User:
    kwargs = random_user_kwargs(**kwargs)
    return User(**kwargs)


def admin_user(**kwargs) -> User:
    kwargs = random_user_kwargs(**kwargs)
    kwargs["roles"] = [Role.administrator()]
    return User(**kwargs)


def regular_user(**kwargs) -> User:
    kwargs = random_user_kwargs(**kwargs)
    kwargs["roles"] = [Role.user()]
    return User(**kwargs)


def random_add_food_product_cmd_kwargs(**kwargs) -> dict:
    prefix = kwargs.get("prefix") or ""
    final_kwargs = {
        "source_id": (
            kwargs.get("source_id")
            if "source_id" in kwargs
            else random.choice([i.value for i in SourceNames if i.value != "auto"])
        ),
        "name": (
            kwargs.get("name") if "name" in kwargs else random_attr(f"{prefix}name")
        ),
        "category_id": (
            kwargs.get("category_id")
            if "category_id" in kwargs
            else None
            # else random_attr(f"{prefix}category")
        ),
        "parent_category_id": (
            kwargs.get("parent_category_id")
            if "parent_category_id" in kwargs
            else None
            # else random_attr(f"{prefix}parent_category")
        ),
        "brand_id": (
            kwargs.get("brand_id")
            if "brand_id" in kwargs
            else None
            # else random_attr(f"{prefix}brand_id")
        ),
        "nutri_facts": (
            kwargs.get("nutri_facts")
            if "nutri_facts" in kwargs
            else random_nutri_facts()
        ),
        "barcode": kwargs.get("barcode") if "barcode" in kwargs else random_barcode(),
        "diet_types_ids": (
            kwargs.get("diet_types_ids")
            if "diet_types_ids" in kwargs
            else set()
            # else set([random.choice([i.value for i in DietType])])
        ),
        "process_type_id": (
            kwargs.get("process_type_id")
            if "process_type_id" in kwargs
            else None
            # else random.choice([i.value for i in ProcessType])
        ),
        "score": kwargs.get("score") if "score" in kwargs else random_score(),
        "ingredients": (
            kwargs.get("ingredients")
            if "ingredients" in kwargs
            else random_attr(f"{prefix}ingredients")
        ),
        "allergens": (
            kwargs.get("allergens")
            if "allergens" in kwargs
            else random_attr(f"{prefix}allergens")
        ),
        "food_group_id": (
            kwargs.get("food_group_id")
            if "food_group_id" in kwargs
            else None
            # else random.choice([i.value for i in FoodGroup])
        ),
        "package_size": (
            kwargs.get("package_size")
            if "package_size" in kwargs
            else random.uniform(0, 1000)
        ),
        "package_size_unit": (
            kwargs.get("package_size_unit")
            if "package_size_unit" in kwargs
            else random.choice([i.value for i in Unit])
        ),
        "image_url": (
            kwargs.get("image_url")
            if "image_url" in kwargs
            else random_attr(f"{prefix}image_url")
        ),
        "json_data": (
            kwargs.get("json_data")
            if "json_data" in kwargs
            else random_attr(f"{prefix}json_data")
        ),
    }
    missing = _missing_attributes(AddFoodProduct, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_food_product_kwargs(
    **kwargs,
) -> dict:
    prefix = kwargs.get("prefix") or ""
    final_kwargs = {
        # "id": kwargs.get("id") if "id" in kwargs else random_attr(f"{prefix}id"),
        "source_id": (
            kwargs.get("source_id")
            if "source_id" in kwargs
            else random.choice([i.value for i in SourceNames if i.value != "auto"])
        ),
        "name": (
            kwargs.get("name") if "name" in kwargs else random_attr(f"{prefix}name")
        ),
        "category_id": (
            kwargs.get("category_id")
            if "category_id" in kwargs
            else None
            # else random_attr(f"{prefix}category")
        ),
        "parent_category_id": (
            kwargs.get("parent_category_id")
            if "parent_category_id" in kwargs
            else None
            # else random_attr(f"{prefix}parent_category")
        ),
        # "is_food": True,
        "barcode": kwargs.get("barcode") if "barcode" in kwargs else random_barcode(),
        "brand_id": (
            kwargs.get("brand_id")
            if "brand_id" in kwargs
            else None
            # else random_attr(f"{prefix}brand_id")
        ),
        "score": kwargs.get("score") if "score" in kwargs else random_score(),
        "food_group_id": (
            kwargs.get("food_group_id")
            if "food_group_id" in kwargs
            else None
            # else random.choice([i.value for i in FoodGroupNames])
        ),
        "process_type_id": (
            kwargs.get("process_type_id")
            if "process_type_id" in kwargs
            else None
            # else random.choice([i.value for i in ProcessTypeNames])
        ),
        "diet_types_ids": (
            kwargs.get("diet_types_ids")
            if "diet_types_ids" in kwargs
            else set()
            # else set([random.choice([i.value for i in DietTypeNames])])
        ),
        "nutri_facts": (
            kwargs.get("nutri_facts")
            if "nutri_facts" in kwargs
            else random_nutri_facts()
        ),
        "ingredients": (
            kwargs.get("ingredients")
            if "ingredients" in kwargs
            else random_attr(f"{prefix}ingredients")
        ),
        "package_size": (
            kwargs.get("package_size")
            if "package_size" in kwargs
            else random.uniform(0, 1000)
        ),
        "package_size_unit": (
            kwargs.get("package_size_unit")
            if "package_size_unit" in kwargs
            else random.choice([i.value for i in Unit])
        ),
        "image_url": (
            kwargs.get("image_url")
            if "image_url" in kwargs
            else random_attr(f"{prefix}image_url")
        ),
        "json_data": (
            kwargs.get("json_data")
            if "json_data" in kwargs
            else random_attr(f"{prefix}json_data")
        ),
        # "discarded": kwargs.get("discarded") if "discarded" in kwargs else False,
        # "version": kwargs.get("version") if "version" in kwargs else 1,
        "is_food_votes": kwargs.get("is_food_votes"),
    }
    missing = _missing_attributes(Product.add_food_product, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_food_product(**kwargs) -> Product:
    return Product.add_food_product(**random_food_product_kwargs(**kwargs))


def random_non_food_product_kwargs(
    **kwargs,
) -> dict:
    prefix = kwargs.get("prefix") or ""
    final_kwargs = {
        "source_id": (
            kwargs.get("source_id")
            if "source_id" in kwargs
            else random.choice([i.value for i in SourceNames if i.value != "auto"])
        ),
        "name": (
            kwargs.get("name") if "name" in kwargs else random_attr(f"{prefix}name")
        ),
        "barcode": kwargs.get("barcode") if "barcode" in kwargs else random_barcode(),
    }
    missing = _missing_attributes(Product.add_non_food_product, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_non_food_product(**kwargs) -> Product:
    return Product.add_non_food_product(**random_non_food_product_kwargs(**kwargs))


def random_create_tag_classmethod_kwargs(**kwargs) -> dict:
    final_kwargs = {
        "name": (
            kwargs.get("name")
            if "name" in kwargs
            else random.choice([i.value for i in SourceNames if i.value != "auto"])
        ),
        "author_id": (
            kwargs.get("author_id") if "author_id" in kwargs else admin_user().id
        ),
        "description": (
            kwargs.get("description")
            if "description" in kwargs
            else random_attr("tag_description")
        ),
    }
    missing = _missing_attributes(Tag.create_tag, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_source(**kwargs) -> Source:
    return Source.create_tag(**random_create_tag_classmethod_kwargs(**kwargs))


def random_brand(**kwargs) -> Brand:
    return Brand.create_tag(**random_create_tag_classmethod_kwargs(**kwargs))


def random_category(**kwargs) -> Category:
    return Category.create_tag(**random_create_tag_classmethod_kwargs(**kwargs))


def random_parent_category(**kwargs) -> ParentCategory:
    return ParentCategory.create_tag(**random_create_tag_classmethod_kwargs(**kwargs))


def random_food_group(**kwargs) -> FoodGroup:
    return FoodGroup.create_tag(**random_create_tag_classmethod_kwargs(**kwargs))


def random_process_type(**kwargs) -> ProcessType:
    return ProcessType.create_tag(**random_create_tag_classmethod_kwargs(**kwargs))


def random_diet_type(**kwargs) -> DietType:
    return DietType.create(**random_create_tag_classmethod_kwargs(**kwargs))


@unique
class SourceNames(Enum):
    PRIVATE = "private"
    MANUAL = "manual"
    TACO = "taco"
    GS1 = "gs1"
    AUTO = "auto"


@unique
class FoodGroupNames(Enum):
    ENERGY = "Energéticos"
    BUILDERS = "Construtores"
    REGULATORS = "Reguladores"


@unique
class ProcessTypeNames(Enum):
    UNPROCESSED = "In natura"
    MIN_PROCCESSED = "Minimante processados"
    PROCESSED = "Processados"
    ULTRA_PROCESSED = "Ultra processados"
    OILS_FAT_SALT_SUGAR = "Óleos, gorduras, sal e açúcar"


@unique
class DietTypeNames(Enum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    LOWFODMAP = "lowfodmap"
    GLUTEN_FREE = "gluten_free"
    LACTOSE_FREE = "lactose_free"
    SUGAR_FREE = "sugar_free"
    LOW_SODIUM = "low_sodium"
    LOW_FAT = "low_fat"
    LOW_SUGAR = "low_sugar"
    LOW_CALORIES = "low_calories"
    LOW_CARB = "low_carb"
    HIGH_PROTEIN = "high_protein"
    HIGH_FIBER = "high_fiber"
    HIGH_CALCIUM = "high_calcium"
    HIGH_IRON = "high_iron"
    HIGH_POTASSIUM = "high_potassium"
    # TODO: add more diet types
