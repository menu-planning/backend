import inspect
import random
import uuid

from src.contexts.products_catalog.core.domain.commands.products.add_food_product import (
    AddFoodProduct,
)
from src.contexts.products_catalog.core.domain.entities.classification import (
    Brand,
    Category,
    Classification,
    FoodGroup,
    ParentCategory,
    ProcessType,
    Source,
)
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.products_catalog.core.domain.enums import Unit
from src.contexts.products_catalog.core.domain.value_objects.role import Role
from src.contexts.products_catalog.core.domain.value_objects.score import Score
from src.contexts.products_catalog.core.domain.value_objects.user import User
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts

from tests.contexts.products_catalog.test_enums import CategoryTestEnum, FoodGroupTestEnum, ParentCategoryTestEnum, ProcessTypeTestEnum, SourceTestEnum
from tests.utils import check_missing_attributes

# def _class_attributes(cls) -> list[str]:
#     attributes = [
#         attr
#         for attr in inspect.getmembers(cls, lambda a: not (inspect.isroutine(a)))
#         if not (attr[0].startswith("_") or attr[0] == "instance_id")
#     ]
#     return [i[0] for i in attributes]


# def _missing_attributes(cls, kwargs) -> list[str]:
#     attribute_names = _class_attributes(cls)
#     return [attr for attr in attribute_names if attr not in kwargs]


def random_suffix(module_name: str = "") -> str:
    return f"{uuid.uuid4().hex[:6]}{module_name}"


def random_attr(attr="") -> str:
    return f"{attr}-{random_suffix()}"


def random_score_kwargs(**kwargs):
    kwargs["nutrients"] = random.uniform(0, 100)
    kwargs["ingredients"] = random.uniform(0, 100)
    kwargs["final"] = (kwargs["nutrients"] + kwargs["ingredients"]) / 2
    missing = check_missing_attributes(Score, kwargs)
    assert not missing, f"Missing attributes {missing}"
    return kwargs


def random_score(**kwargs) -> Score:
    return Score(**random_score_kwargs(**kwargs))


def random_barcode() -> str:
    return f"{random.randint(100000000000, 999999999999)}"


def random_nutri_facts_kwargs(**kwargs):
    for i in inspect.signature(NutriFacts).parameters:
        kwargs[i] = kwargs.get(i) or random.uniform(0, 1000)
    missing = check_missing_attributes(NutriFacts, kwargs)
    assert not missing, f"Missing attributes {missing}"
    return kwargs


def random_nutri_facts(**kwargs) -> NutriFacts:
    return NutriFacts(**random_nutri_facts_kwargs(**kwargs))


def random_user_kwargs(**kwargs) -> dict:
    final_kwargs = {
        "id": kwargs.get("id") if "id" in kwargs else random_attr("user_id"),
        "roles": (kwargs.get("roles") if "roles" in kwargs else []),
    }
    missing = check_missing_attributes(User, final_kwargs)
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
            else random.choice([i.value for i in SourceTestEnum if i.value != "auto"])
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
    missing = check_missing_attributes(AddFoodProduct, final_kwargs)
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
            else random.choice([i.value for i in SourceTestEnum if i.value != "auto"])
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
    missing = check_missing_attributes(Product.add_food_product, final_kwargs)
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
            else random.choice([i.value for i in SourceTestEnum if i.value != "auto"])
        ),
        "name": (
            kwargs.get("name") if "name" in kwargs else random_attr(f"{prefix}name")
        ),
        "barcode": kwargs.get("barcode") if "barcode" in kwargs else random_barcode(),
    }
    missing = check_missing_attributes(Product.add_non_food_product, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_non_food_product(**kwargs) -> Product:
    return Product.add_non_food_product(**random_non_food_product_kwargs(**kwargs))


def random_create_classification_classmethod_kwargs(**kwargs) -> dict:
    final_kwargs = {
        "name": (
            kwargs.get("name")
            if "name" in kwargs
            else random_attr("classification_name")
        ),
        "author_id": (
            kwargs.get("author_id") if "author_id" in kwargs else admin_user().id
        ),
        "description": (
            kwargs.get("description")
            if "description" in kwargs
            else random_attr("classification_description")
        ),
        "event_type": kwargs.get("event_type"),
    }
    missing = check_missing_attributes(
        Classification.create_classification, final_kwargs
    )
    assert not missing, f"Missing attributes: {missing}"
    final_kwargs.pop('event_type')
    return final_kwargs


def random_source(**kwargs) -> Source:
    name = (
        kwargs.get("name")
        if "name" in kwargs
        else random.choice([i.value for i in SourceTestEnum if i.value != "auto"])
    )
    kwargs["name"] = name
    return Source.create_classification(
        **random_create_classification_classmethod_kwargs(**kwargs)
    )


def random_brand(**kwargs) -> Brand:
    return Brand.create_classification(
        **random_create_classification_classmethod_kwargs(**kwargs)
    )


def random_category(**kwargs) -> Category:
    name = (
        kwargs.get("name")
        if "name" in kwargs
        else random.choice([i.value for i in CategoryTestEnum if i.value != "auto"])
    )
    kwargs["name"] = name
    return Category.create_classification(
        **random_create_classification_classmethod_kwargs(**kwargs)
    )


def random_parent_category(**kwargs) -> ParentCategory:
    name = (
        kwargs.get("name")
        if "name" in kwargs
        else random.choice(
            [i.value for i in ParentCategoryTestEnum if i.value != "auto"]
        )
    )
    kwargs["name"] = name
    return ParentCategory.create_classification(
        **random_create_classification_classmethod_kwargs(**kwargs)
    )


def random_food_group(**kwargs) -> FoodGroup:
    name = (
        kwargs.get("name")
        if "name" in kwargs
        else random.choice([i.value for i in FoodGroupTestEnum if i.value != "auto"])
    )
    kwargs["name"] = name
    return FoodGroup.create_classification(
        **random_create_classification_classmethod_kwargs(**kwargs)
    )


def random_process_type(**kwargs) -> ProcessType:
    name = (
        kwargs.get("name")
        if "name" in kwargs
        else random.choice([i.value for i in ProcessTypeTestEnum if i.value != "auto"])
    )
    kwargs["name"] = name
    return ProcessType.create_classification(
        **random_create_classification_classmethod_kwargs(**kwargs)
    )
