import inspect
import random
import uuid
from typing import Literal

from src.contexts.recipes_catalog.shared.domain.commands import CreateRecipe
from src.contexts.recipes_catalog.shared.domain.commands.meals.create_meal import (
    CreateMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.tags.create import CreateTag
from src.contexts.recipes_catalog.shared.domain.entities import Recipe
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.rating import Rating
from src.contexts.recipes_catalog.shared.domain.value_objects.role import Role
from src.contexts.recipes_catalog.shared.domain.value_objects.user import User
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Privacy
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from tests.products_catalog.test_enums import CategoryTestEnum
from tests.recipes_catalog.test_enums import MealPlanningTestEnum
from tests.test_enums import (
    CuisineTestEnum,
    DietTypeTestEnum,
    FlavorTestEnum,
    TextureTestEnum,
)
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


# def check_missing_attributes(cls_or_method, kwargs) -> list[str]:
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


def random_nutri_facts_kwargs(**kwargs):
    for i in inspect.signature(NutriFacts).parameters:
        kwargs[i] = kwargs.get(i) or random.uniform(0, 1000)
    missing = check_missing_attributes(NutriFacts, kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return kwargs


def random_nutri_facts(**kwargs) -> NutriFacts:
    return NutriFacts(**random_nutri_facts_kwargs(**kwargs))


def random_user_kwargs(**kwargs) -> dict:
    final_kwargs = {
        "id": kwargs.get("id") if "id" in kwargs else random_attr("user_id"),
        "roles": kwargs.get("roles") if "roles" in kwargs else [],
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


def random_ingredient_kwargs(**kwargs) -> dict:
    final_kwargs = {
        "name": (
            kwargs.get("name") if "name" in kwargs else random_attr("ingredient_name")
        ),
        "unit": (
            kwargs.get("unit")
            if "unit" in kwargs
            else random.choice([i for i in MeasureUnit])
        ),
        "quantity": (
            kwargs.get("quantity") if "quantity" in kwargs else random.uniform(0, 100)
        ),
        "product_id": (
            kwargs.get("product_id")
            if "product_id" in kwargs
            else random_attr("product_id")
        ),
        "full_text": (
            kwargs.get("full_text")
            if "full_text" in kwargs
            else random_attr("ingredient_full_text")
        ),
        "position": (kwargs.get("position") if "position" in kwargs else 1),
    }
    missing = check_missing_attributes(Ingredient, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_ingredient(**kwargs) -> dict:
    return Ingredient(**random_ingredient_kwargs(**kwargs))


def random_rate_cmd_kwargs(**kwargs) -> dict:
    final_kwargs = {
        "user_id": (
            kwargs.get("user_id") if "user_id" in kwargs else random_attr("user_id")
        ),
        "taste": kwargs.get("taste") if "taste" in kwargs else random.randint(0, 5),
        "convenience": (
            kwargs.get("convenience")
            if "convenience" in kwargs
            else random.randint(0, 5)
        ),
        "comment": (
            kwargs.get("comment")
            if "comment" in kwargs
            else random_attr("rate_comment")
        ),
    }
    missing = check_missing_attributes(Rating, final_kwargs | {"recipe_id": None})
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_rating(**kwargs) -> dict:
    recipe_id = kwargs.get("recipe_id") or random_attr("recipe_id")
    return Rating(**random_rate_cmd_kwargs(**kwargs), recipe_id=recipe_id)


def random_create_recipe_cmd_kwargs(**kwargs) -> dict:
    author_id = (
        kwargs.get("author_id") if "author_id" in kwargs else random_attr("user_id")
    )
    user = random_user(id=author_id)
    tag = random_tag(author_id=user.id)
    final_kwargs = {
        "name": kwargs.get("name") if "name" in kwargs else random_attr("recipe_name"),
        "meal_id": kwargs.get("meal_id") if "meal_id" in kwargs else None,
        "description": (
            kwargs.get("description")
            if "description" in kwargs
            else random_attr("recipe_description")
        ),
        "ingredients": (
            kwargs.get("ingredients")
            if "ingredients" in kwargs
            else [random_ingredient(position=i) for i in range(1, 4)]
        ),
        "instructions": (
            kwargs.get("instructions")
            if "instructions" in kwargs
            else random_attr("recipe_instructions")
        ),
        "author_id": (kwargs.get("author_id") if "author_id" in kwargs else user.id),
        "tags": (kwargs.get("tags") if "tags" in kwargs else {tag}),
        "utensils": (
            kwargs.get("utensils") if "utensils" in kwargs else random_attr("utensils")
        ),
        "total_time": (
            kwargs.get("total_time")
            if "total_time" in kwargs
            else random.randint(0, 100)
        ),
        "notes": (
            kwargs.get("notes") if "notes" in kwargs else random_attr("recipe_notes")
        ),
        "privacy": kwargs.get("privacy") if "privacy" in kwargs else Privacy.PRIVATE,
        "nutri_facts": (
            kwargs.get("nutri_facts")
            if "nutri_facts" in kwargs
            else random_nutri_facts()
        ),
        "weight_in_grams": (
            kwargs.get("weight_in_grams")
            if "weight_in_grams" in kwargs
            else random.randint(0, 1000)
        ),
        "image_url": (
            kwargs.get("image_url")
            if "image_url" in kwargs
            else random_attr("recipe_image_url")
        ),
    }
    missing = check_missing_attributes(CreateRecipe, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_create_recipe_classmethod_kwargs(**kwargs) -> dict:
    author_id = (
        kwargs.get("author_id") if "author_id" in kwargs else random_attr("user_id")
    )
    user = random_user(id=author_id)
    tag = random_tag(author_id=user.id)
    final_kwargs = {
        # "id": kwargs.get("id") if "id" in kwargs else random_attr("recipe_id"),
        "name": kwargs.get("name") if "name" in kwargs else random_attr("recipe_name"),
        "meal_id": kwargs.get("meal_id") if "meal_id" in kwargs else None,
        "description": (
            kwargs.get("description")
            if "description" in kwargs
            else random_attr("recipe_description")
        ),
        "ingredients": (
            kwargs.get("ingredients")
            if "ingredients" in kwargs
            else [random_ingredient(position=i) for i in range(1, 4)]
        ),
        "instructions": (
            kwargs.get("instructions")
            if "instructions" in kwargs
            else random_attr("recipe_instructions")
        ),
        "author_id": (kwargs.get("author_id") if "author_id" in kwargs else user.id),
        "utensils": (
            kwargs.get("utensils") if "utensils" in kwargs else random_attr("utensils")
        ),
        "total_time": (
            kwargs.get("total_time")
            if "total_time" in kwargs
            else random.randint(0, 100)
        ),
        "notes": (
            kwargs.get("notes") if "notes" in kwargs else random_attr("recipe_notes")
        ),
        "privacy": kwargs.get("privacy") if "privacy" in kwargs else Privacy.PRIVATE,
        "tags": kwargs.get("tags") if "tags" in kwargs else {tag},
        "nutri_facts": (
            kwargs.get("nutri_facts")
            if "nutri_facts" in kwargs
            else random_nutri_facts()
        ),
        "weight_in_grams": (
            kwargs.get("weight_in_grams")
            if "weight_in_grams" in kwargs
            else random.randint(0, 1000)
        ),
        "image_url": (
            kwargs.get("image_url")
            if "image_url" in kwargs
            else random_attr("recipe_image_url")
        ),
    }
    missing = check_missing_attributes(Recipe.create_recipe, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_recipe(**kwargs) -> Recipe:
    return Recipe.create_recipe(**random_create_recipe_classmethod_kwargs(**kwargs))


def random_create_recipe_tag_cmd_kwargs(**kwargs) -> dict:
    author_id = (
        kwargs.get("author_id") if "author_id" in kwargs else random_attr("user_id")
    )
    user = random_user(id=author_id)
    key = (
        kwargs.get("key")
        if "key" in kwargs
        else random.choice(
            [
                "Tipo de Dieta",
                "Cozinha",
                "Sabor",
                "Textura",
                "Planejamento",
            ]
        )
    )
    final_kwargs = {
        "key": key,
        "value": kwargs.get("value") if "value" in kwargs else random_tag_value(key),
        "author_id": (kwargs.get("author_id") if "author_id" in kwargs else user.id),
        "type": kwargs.get("type") if "type" in kwargs else "recipe",
    }
    missing = check_missing_attributes(CreateTag, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_tag_value(
    type: Literal[
        "Tipo de Dieta",
        "Cozinha",
        "Sabor",
        "Textura",
        "Planejamento",
    ]
):
    mapping = {
        "Tipo de Dieta": DietTypeTestEnum,
        "Cozinha": CuisineTestEnum,
        "Sabor": FlavorTestEnum,
        "Textura": TextureTestEnum,
        "Planejamento": MealPlanningTestEnum,
    }
    return random.choice([i.value for i in mapping[type]])


def random_tag(**kwargs) -> Tag:
    kw = random_create_recipe_tag_cmd_kwargs(**kwargs)
    # kw.update({"type": "recipe"})
    return Tag(**kw)


def random_create_meal_cmd_kwargs(**kwargs) -> dict:
    author_id = (
        kwargs.get("author_id") if "author_id" in kwargs else random_attr("user_id")
    )
    user = random_user(id=author_id)
    tag = random_tag(author_id=user.id, type="meal")
    final_kwargs = {
        "name": kwargs.get("name") if "name" in kwargs else random_attr("meal_name"),
        "description": (
            kwargs.get("description")
            if "description" in kwargs
            else random_attr("meal_description")
        ),
        "author_id": (kwargs.get("author_id") if "author_id" in kwargs else user.id),
        "recipes": (
            kwargs.get("recipes")
            if "recipes" in kwargs
            else [random_recipe(author_id=author_id) for _ in range(3)]
        ),
        # "menu_id": kwargs.get("menu_id") if "menu_id" in kwargs else None,
        "notes": (
            kwargs.get("notes") if "notes" in kwargs else random_attr("meal_notes")
        ),
        "tags": (kwargs.get("tags") if "tags" in kwargs else {tag}),
        "image_url": (
            kwargs.get("image_url")
            if "image_url" in kwargs
            else random_attr("meal_image_url")
        ),
    }
    missing = check_missing_attributes(CreateMeal, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_create_meal_classmethod_kwargs(**kwargs) -> dict:
    author_id = (
        kwargs.get("author_id") if "author_id" in kwargs else random_attr("user_id")
    )
    user = random_user(id=author_id)
    tag = random_tag(author_id=user.id, type="meal")
    final_kwargs = {
        "name": kwargs.get("name") if "name" in kwargs else random_attr("meal_name"),
        "description": (
            kwargs.get("description")
            if "description" in kwargs
            else random_attr("meal_description")
        ),
        "author_id": (kwargs.get("author_id") if "author_id" in kwargs else user.id),
        "recipes": (
            kwargs.get("recipes")
            if "recipes" in kwargs
            else [random_recipe(author_id=author_id) for _ in range(3)]
        ),
        "tags": (kwargs.get("tags") if "tags" in kwargs else {tag}),
        "notes": (kwargs.get("notes") if "notes" in kwargs else None),
        "image_url": (kwargs.get("image_url") if "image_url" in kwargs else None),
    }
    missing = check_missing_attributes(Meal.create_meal, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_meal(**kwargs) -> Meal:
    return Meal.create_meal(**random_create_meal_classmethod_kwargs(**kwargs))


def random_create_recipe_on_meal_kwargs(**kwargs):
    recipe_cmd = random_create_recipe_classmethod_kwargs(**kwargs)
    recipe_cmd.pop("meal_id")
    return recipe_cmd
