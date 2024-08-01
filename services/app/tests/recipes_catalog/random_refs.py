import inspect
import random
import uuid
from enum import Enum, unique
from typing import Literal

from src.contexts.recipes_catalog.shared.domain.commands import CreateRecipe
from src.contexts.recipes_catalog.shared.domain.commands.tags.base_classes import (
    CreateTag,
)
from src.contexts.recipes_catalog.shared.domain.entities import Recipe
from src.contexts.recipes_catalog.shared.domain.entities.tags.base_classes import Tag
from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.rating import Rating
from src.contexts.recipes_catalog.shared.domain.value_objects.role import Role
from src.contexts.recipes_catalog.shared.domain.value_objects.user import User
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Month, Privacy
from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine
from src.contexts.shared_kernel.domain.value_objects.name_tag.flavor import Flavor
from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


def _class_attributes(cls) -> list[str]:
    attributes = [
        attr
        for attr in inspect.getmembers(cls, lambda a: not (inspect.isroutine(a)))
        if not (attr[0].startswith("_") or attr[0] == "instance_id")
    ]
    return [i[0] for i in attributes]


def _class_method_attributes(method) -> list[str]:
    if not inspect.ismethod(method):
        raise TypeError("The argument must be a class method.")

    sig = inspect.signature(method)
    return [param.name for param in sig.parameters.values() if param.name != "cls"]


def _missing_attributes(cls_or_method, kwargs) -> list[str]:
    if inspect.isclass(cls_or_method):
        attribute_names = _class_attributes(cls_or_method)
    elif inspect.ismethod(cls_or_method):
        attribute_names = _class_method_attributes(cls_or_method)
    else:
        raise TypeError("The first argument must be a class or a class method.")

    return [attr for attr in attribute_names if attr not in kwargs]


def random_suffix(module_name: str = "") -> str:
    return f"{uuid.uuid4().hex[:6]}{module_name}"


def random_attr(attr="") -> str:
    return f"{attr}-{random_suffix()}"


def random_nutri_facts_kwargs(**kwargs):
    for i in inspect.signature(NutriFacts).parameters:
        kwargs[i] = kwargs.get(i) or random.uniform(0, 1000)
    missing = _missing_attributes(NutriFacts, kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return kwargs


def random_nutri_facts(**kwargs) -> NutriFacts:
    return NutriFacts(**random_nutri_facts_kwargs(**kwargs))


def random_user_kwargs(**kwargs) -> dict:
    final_kwargs = {
        "id": kwargs.get("id") if "id" in kwargs else random_attr("user_id"),
        "roles": kwargs.get("roles") if "roles" in kwargs else [],
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
    }
    missing = _missing_attributes(Ingredient, final_kwargs)
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
    missing = _missing_attributes(Rating, final_kwargs | {"recipe_id": None})
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_rating(**kwargs) -> dict:
    recipe_id = kwargs.get("recipe_id") or random_attr("recipe_id")
    return Rating(**random_rate_cmd_kwargs(**kwargs), recipe_id=recipe_id)


def random_create_recipe_cmd_kwargs(**kwargs) -> dict:
    final_kwargs = {
        "name": kwargs.get("name") if "name" in kwargs else random_attr("recipe_name"),
        "description": (
            kwargs.get("description")
            if "description" in kwargs
            else random_attr("recipe_description")
        ),
        "ingredients": (
            kwargs.get("ingredients")
            if "ingredients" in kwargs
            else [random_ingredient() for _ in range(3)]
        ),
        "instructions": (
            kwargs.get("instructions")
            if "instructions" in kwargs
            else random_attr("recipe_instructions")
        ),
        "author_id": (
            kwargs.get("author_id") if "author_id" in kwargs else random_user().id
        ),
        "utensils": (
            kwargs.get("utensils") if "utensils" in kwargs else random_attr("utensils")
        ),
        "total_time": (
            kwargs.get("total_time")
            if "total_time" in kwargs
            else random.randint(0, 100)
        ),
        "servings": kwargs.get("servings") if "servings" in kwargs else 1,
        "notes": (
            kwargs.get("notes") if "notes" in kwargs else random_attr("recipe_notes")
        ),
        "diet_types_ids": (
            kwargs.get("diet_types_ids")
            if "diet_types_ids" in kwargs
            else set([random_tag_id(DietTypeRandomEnum) for _ in range(3)])
        ),
        "categories_ids": (
            kwargs.get("categories_ids")
            if "categories_ids" in kwargs
            else set([random_tag_id(CategoryRandomEnum) for _ in range(3)])
        ),
        "cuisine": (
            kwargs.get("cuisine")
            if "cuisine" in kwargs
            else Cuisine(name=random_tag_id(CuisineRandomEnum))
        ),
        "flavor": (
            kwargs.get("flavor")
            if "flavor" in kwargs
            else Flavor(name=random_tag_id(FlavorRandomEnum))
        ),
        "texture": (
            kwargs.get("texture")
            if "texture" in kwargs
            else Texture(name=random_tag_id(TextureRandomEnum))
        ),
        "meal_planning_ids": (
            kwargs.get("meal_planning_ids")
            if "meal_planning_ids" in kwargs
            else set([random_tag_id(MealPlanningRandomEnum) for _ in range(3)])
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
        "season": (
            kwargs.get("season")
            if "season" in kwargs
            else set([random.choice([i for i in Month]) for _ in range(3)])
        ),
        "image_url": (
            kwargs.get("image_url")
            if "image_url" in kwargs
            else random_attr("recipe_image_url")
        ),
    }
    missing = _missing_attributes(CreateRecipe, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_create_recipe_classmethod_kwargs(**kwargs) -> dict:
    final_kwargs = {
        # "id": kwargs.get("id") if "id" in kwargs else random_attr("recipe_id"),
        "name": kwargs.get("name") if "name" in kwargs else random_attr("recipe_name"),
        "description": (
            kwargs.get("description")
            if "description" in kwargs
            else random_attr("recipe_description")
        ),
        "ingredients": (
            kwargs.get("ingredients")
            if "ingredients" in kwargs
            else [random_ingredient() for _ in range(3)]
        ),
        "instructions": (
            kwargs.get("instructions")
            if "instructions" in kwargs
            else random_attr("recipe_instructions")
        ),
        "author_id": (
            kwargs.get("author_id") if "author_id" in kwargs else random_user().id
        ),
        "utensils": (
            kwargs.get("utensils") if "utensils" in kwargs else random_attr("utensils")
        ),
        "total_time": (
            kwargs.get("total_time")
            if "total_time" in kwargs
            else random.randint(0, 100)
        ),
        "servings": kwargs.get("servings") if "servings" in kwargs else 1,
        "notes": (
            kwargs.get("notes") if "notes" in kwargs else random_attr("recipe_notes")
        ),
        "diet_types_ids": (
            kwargs.get("diet_types_ids")
            if "diet_types_ids" in kwargs
            else set([random_tag_id(DietTypeRandomEnum) for _ in range(3)])
        ),
        "categories_ids": (
            kwargs.get("categories_ids")
            if "categories_ids" in kwargs
            else set([random_tag_id(CategoryRandomEnum) for _ in range(3)])
        ),
        "cuisine": (
            kwargs.get("cuisine")
            if "cuisine" in kwargs
            else Cuisine(name=random_tag_id(CuisineRandomEnum))
        ),
        "flavor": (
            kwargs.get("flavor")
            if "flavor" in kwargs
            else Flavor(name=random_tag_id(FlavorRandomEnum))
        ),
        "texture": (
            kwargs.get("texture")
            if "texture" in kwargs
            else Texture(name=random_tag_id(TextureRandomEnum))
        ),
        "meal_planning_ids": (
            kwargs.get("meal_planning_ids")
            if "meal_planning_ids" in kwargs
            else set([random_tag_id(MealPlanningRandomEnum) for _ in range(3)])
        ),
        "privacy": kwargs.get("privacy") if "privacy" in kwargs else Privacy.PRIVATE,
        # "ratings": kwargs.get("ratings")
        # if "ratings" in kwargs
        # else [random_rating() for _ in range(3)],
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
        "season": (
            kwargs.get("season")
            if "season" in kwargs
            else set([random.choice([i for i in Month]) for _ in range(3)])
        ),
        "image_url": (
            kwargs.get("image_url")
            if "image_url" in kwargs
            else random_attr("recipe_image_url")
        ),
        # "created_at": kwargs.get("created_at")
        # if "created_at" in kwargs
        # else datetime.now(),
        # "discarded": kwargs.get("discarded") if "discarded" in kwargs else False,
        # "version": kwargs.get("version") if "version" in kwargs else 1,
    }
    missing = _missing_attributes(Recipe.create_recipe, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_recipe(**kwargs) -> Recipe:
    return Recipe.create_recipe(**random_create_recipe_classmethod_kwargs(**kwargs))


def random_create_tag_cmd_kwargs(**kwargs) -> dict:
    final_kwargs = {
        "name": kwargs.get("name") if "name" in kwargs else random_attr("tag_name"),
        "author_id": (
            kwargs.get("author_id") if "author_id" in kwargs else random_user().id
        ),
        "description": (
            kwargs.get("description")
            if "description" in kwargs
            else random_attr("tag_description")
        ),
        "privacy": kwargs.get("privacy") if "privacy" in kwargs else Privacy.PRIVATE,
    }
    missing = _missing_attributes(CreateTag, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_create_tag_classmethod_kwargs(**kwargs) -> dict:
    final_kwargs = {
        "name": kwargs.get("name") if "name" in kwargs else random_attr("tag_name"),
        "author_id": (
            kwargs.get("author_id") if "author_id" in kwargs else random_user().id
        ),
        "description": (
            kwargs.get("description")
            if "description" in kwargs
            else random_attr("tag_description")
        ),
        "privacy": kwargs.get("privacy") if "privacy" in kwargs else Privacy.PRIVATE,
    }
    missing = _missing_attributes(Tag.create_tag, final_kwargs)
    missing.remove("event_type")
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_tag_name(
    type: Literal[
        "DietType",
        "Category",
        "Cuisine",
        "Flavor",
        "Texture",
        "MealPlanning",
    ]
):
    mapping = {
        "DietType": DietTypeRandomEnum,
        "Category": CategoryRandomEnum,
        "Cuisine": CuisineRandomEnum,
        "Flavor": FlavorRandomEnum,
        "Texture": TextureRandomEnum,
        "MealPlanning": MealPlanningRandomEnum,
    }
    return random.choice([i.value for i in mapping[type]])


def random_tag_id(random_enum: Enum) -> Tag:
    return random.choice([i.value for i in random_enum])


@unique
class DietTypeRandomEnum(str, Enum):
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


@unique
class CategoryRandomEnum(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    DESSERT = "dessert"
    DRINK = "drink"


@unique
class CuisineRandomEnum(Enum):
    american = "American"
    asian = "Asian"
    mexican = "Mexican"
    italian = "Italian"
    french = "French"
    mediterranean = "Mediterranean"
    indian = "Indian"
    chinese = "Chinese"
    japanese = "Japanese"
    thai = "Thai"
    greek = "Greek"
    spanish = "Spanish"
    middle_eastern = "Middle Eastern"
    african = "African"
    caribbean = "Caribbean"
    latin_american = "Latin American"
    european = "European"
    other = "Other"


@unique
class FlavorRandomEnum(str, Enum):
    SAVORY = "savory"
    SWEET = "sweet"
    SPICY = "spicy"
    SOUR = "sour"
    BITTER = "bitter"
    UMAMI = "umami"
    HERBACEOUS = "herbaceous"
    EARTHY = "earthy"
    CITRUSY = "citrusy"
    FRUITY = "fruity"
    NUTTY = "nutty"
    SMOKY = "smoky"
    GARLICKY = "garlicky"
    CREAMY = "creamy"
    TANGY = "tangy"
    MILD = "mild"
    COMPLEX = "complex"
    FRESH = "fresh"
    RICH = "rich"
    TROPICAL = "tropical"


@unique
class TextureRandomEnum(str, Enum):
    SOFT = "soft"
    CRUNCHY = "crunchy"
    CREAMY = "creamy"
    CRISPY = "crispy"
    FIRM = "firm"
    AERATED = "aerated"
    WATERY = "watery"


@unique
class MealPlanningRandomEnum(str, Enum):
    QUICK = "quick"
    SLOW = "slow"
    MAKE_AHEAD = "make_ahead"
    ONE_POT = "one_pot"
    FREEZER_FRIENDLY = "freezer_friendly"
    KID_FRIENDLY = "kid_friendly"
    BUDGET_FRIENDLY = "budget_friendly"
    LEFTOVERS = "leftovers"
    ENTERTAINING = "entertaining"


# def random_add_new_food_product_cmd_kwargs(
#     source: str | None = None,
#     name: str | None = None,
#     category: str | None = None,
#     parent_category: str | None = None,
#     brand: str | None = None,
#     nutri_facts: NutriFacts | None = None,
#     diet_types: set[str] | None = None,
#     process_type: str | None = None,
#     barcode: str | None = None,
# ) -> dict:
#     kwargs = {}
#     kwargs["source"] = source or random.choice(
#         [i.value for i in Source if i.value != "auto"]
#     )
#     kwargs["name"] = name or random_attr("auto_name")
#     kwargs["category"] = category or random_attr("auto_category")
#     kwargs["parent_category"] = parent_category or random_attr("auto_parent_category")
#     kwargs["brand"] = brand or random_attr("auto_brand")
#     kwargs["nutri_facts"] = nutri_facts or random_nutri_facts()
#     kwargs["barcode"] = barcode
#     kwargs["diet_types"] = diet_types
#     kwargs["process_type"] = process_type
#     return kwargs


# def random_food_product_kwargs(
#     prefix=None,
#     source: str | None = None,
#     name: str | None = None,
#     category: str | None = None,
#     parent_category: str | None = None,
#     brand: str | None = None,
#     nutri_facts: NutriFacts | None = None,
#     diet_types: set[str] | None = None,
#     process_type: str | None = None,
#     barcode: str | None = None,
#     score: Score | None = None,
# ) -> dict:
#     kwargs = {}
#     kwargs["id"] = random_attr(f"{prefix or ''}id")
#     kwargs["source"] = source or random.choice(
#         [i.value for i in Source if i.value != "auto"]
#     )
#     kwargs["name"] = name or random_attr(f"{prefix or ''}name")
#     kwargs["category"] = category or random_attr(f"{prefix or ''}category")
#     kwargs["parent_category"] = parent_category or random_attr(
#         f"{prefix or ''}parent_category"
#     )
#     kwargs["brand"] = brand or random_attr(f"{prefix or ''}brand")
#     kwargs["nutri_facts"] = nutri_facts or random_nutri_facts()
#     kwargs["barcode"] = barcode
#     kwargs["diet_types"] = diet_types
#     kwargs["process_type"] = process_type
#     kwargs["score"] = score
#     kwargs["is_food"] = True
#     return kwargs


# def random_food_product(prefix: str = None, **kwargs) -> Product:
#     kwargs = random_food_product_kwargs(prefix=prefix, **kwargs)
#     return Product(**kwargs)
