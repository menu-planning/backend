import inspect
import random
import uuid
from enum import Enum, unique
from typing import Literal

from src.contexts.recipes_catalog.shared.domain.commands import CreateMeal, CreateRecipe
from src.contexts.recipes_catalog.shared.domain.commands.tags.base_classes import (
    CreateTag,
)
from src.contexts.recipes_catalog.shared.domain.entities import Recipe
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.recipes_catalog.shared.domain.entities.tags.base_classes import Tag
from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.rating import Rating
from src.contexts.recipes_catalog.shared.domain.value_objects.role import Role
from src.contexts.recipes_catalog.shared.domain.value_objects.user import User
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Month, Privacy
from src.contexts.shared_kernel.domain.value_objects.name_tag.allergen import Allergen
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
        "meal_id": kwargs.get("meal_id") if "meal_id" in kwargs else None,
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
        "allergens": (
            kwargs.get("allergens")
            if "allergens" in kwargs
            else set(
                [
                    Allergen(name=random.choice([i for i in AllergenRandomEnum]).value)
                    for _ in range(3)
                ]
            )
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
        "meal_id": kwargs.get("meal_id") if "meal_id" in kwargs else None,
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
        "allergens": (
            kwargs.get("allergens")
            if "allergens" in kwargs
            else set(
                [
                    Allergen(name=random.choice([i for i in AllergenRandomEnum]).value)
                    for _ in range(3)
                ]
            )
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
    # missing.remove("event_type")
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


def random_create_meal_cmd_kwargs(**kwargs) -> dict:
    final_kwargs = {
        "name": kwargs.get("name") if "name" in kwargs else random_attr("meal_name"),
        "description": (
            kwargs.get("description")
            if "description" in kwargs
            else random_attr("meal_description")
        ),
        "author_id": (
            kwargs.get("author_id") if "author_id" in kwargs else random_user().id
        ),
        "recipes": (
            kwargs.get("recipes")
            if "recipes" in kwargs
            else [random_recipe() for _ in range(3)]
        ),
        "menu_id": kwargs.get("menu_id") if "menu_id" in kwargs else None,
        "notes": (
            kwargs.get("notes") if "notes" in kwargs else random_attr("meal_notes")
        ),
        "image_url": (
            kwargs.get("image_url")
            if "image_url" in kwargs
            else random_attr("meal_image_url")
        ),
    }
    missing = _missing_attributes(CreateMeal, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_create_meal_classmethod_kwargs(**kwargs) -> dict:
    final_kwargs = {
        "name": kwargs.get("name") if "name" in kwargs else random_attr("meal_name"),
        # "description": (
        #     kwargs.get("description")
        #     if "description" in kwargs
        #     else random_attr("meal_description")
        # ),
        "author_id": (
            kwargs.get("author_id") if "author_id" in kwargs else random_user().id
        ),
        # "recipes": (
        #     kwargs.get("recipes")
        #     if "recipes" in kwargs
        #     else [random_recipe() for _ in range(3)]
        # ),
        # "menu_id": kwargs.get("menu_id") if "menu_id" in kwargs else None,
        # "notes": (
        #     kwargs.get("notes") if "notes" in kwargs else random_attr("meal_notes")
        # ),
        # "image_url": (
        #     kwargs.get("image_url")
        #     if "image_url" in kwargs
        #     else random_attr("meal_image_url")
        # ),
    }
    missing = _missing_attributes(Meal.create_meal, final_kwargs)
    assert not missing, f"Missing attributes: {missing}"
    return final_kwargs


def random_meal(**kwargs) -> Meal:
    return Meal.create_meal(**random_create_meal_classmethod_kwargs(**kwargs))


def random_create_recipe_on_meal_kwargs(**kwargs):
    recipe_cmd = random_create_recipe_classmethod_kwargs(**kwargs)
    recipe_cmd.pop("meal_id")
    return recipe_cmd


@unique
class DietTypeRandomEnum(Enum):
    VEGAN = "Vegana"
    VEGETARIAN = "Vegetariana"
    LOWFODMAP = "Low FODMAP"
    GLUTEN_FREE = "Sem glúten"
    LACTOSE_FREE = "Sem lactose"
    SUGAR_FREE = "Sem açúcar"
    LOW_SODIUM = "Baixa em sódio"
    LOW_FAT = "Baixa em gordura"
    LOW_SUGAR = "Baixa em açúcar"
    LOW_CALORIES = "Baixa em caloria"
    LOW_CARB = "Baixa em carboidrato"
    HIGH_PROTEIN = "Alta em proteína"
    HIGH_FIBER = "Alta em fibra"
    HIGH_CALCIUM = "Alta em cálcio"
    HIGH_IRON = "Alta em ferro"
    HIGH_POTASSIUM = "Alta em potássio"
    PALEO = "Paleo"
    KETO = "Keto"
    DAIRY_FREE = "Sem laticínios"
    PESCATARIAN = "Pescetariana"
    WHOLE30 = "Whole30"
    DASH = "DASH"
    MEDITERRANEAN = "Mediterrânea"


@unique
class AllergenRandomEnum(Enum):
    CELERY = "Aipo"
    GARLIC = "Alho"
    PEANUT = "Amendoim"
    BANANA = "Banana"
    CACAO = "Cacau"
    NUTS = "Castanhas"
    CITRUS_FRUITS = "Frutas cítricas"
    SEAFOOD = "Frutos do mar"
    GLUTEN = "Glúten"
    LEGUMES = "Leguminosas"
    MILK = "Leite"
    LUPIN = "Lupino"
    SHELLFISH = "Mariscos"
    CORN = "Milho"
    STRAWBERRY = "Morango"
    MUSTARD = "Mostarda"
    EGG = "Ovo"
    FISH = "Peixe"
    SESAME = "Semente de gergelim"
    SOY = "Soja"
    SULFITES = "Sulfitos"
    WHEAT = "Trigo"


@unique
class CuisineRandomEnum(Enum):
    AFRICAN = "Africana"
    GERMAN = "Alemã"
    ARABIC = "Árabe"
    ARGENTINIAN = "Argentina"
    ASIAN = "Asiática"
    BRAZILIAN = "Brasileira"
    CAPIXABA = "Capixaba"
    CARIBBEAN = "Caribenha"
    CHILEAN = "Chilena"
    CHINESE = "Chinesa"
    KOREAN = "Coreana"
    CUBAN = "Cubana"
    SPANISH = "Espanhola"
    AMERICAN = "Estado Unidense"
    EUROPEAN = "Europeia"
    FRENCH = "Francesa"
    GAUCHA = "Gaúcha"
    GREEK = "Grega"
    INDIAN = "Indiana"
    INDONESIAN = "Indonésia"
    ITALIAN = "Italiana"
    JAPANESE = "Japonesa"
    LATIN_AMERICAN = "Latino-americana"
    LEBANESE = "Libanesa"
    MEDITERRANEAN = "Mediterrânea"
    MEXICAN = "Mexicana"
    MINAS = "Mineira"
    NORTHEASTERN = "Nordestina"
    MIDDLE_EASTERN = "Oriente Médio"
    PERUVIAN = "Peruana"
    PORTUGUESE = "Portuguesa"
    RUSSIAN = "Russa"
    THAI = "Tailandesa"
    TURKISH = "Turca"
    VIETNAMESE = "Vietnamita"


@unique
class FlavorRandomEnum(Enum):
    ACIDIC = "Ácido"
    SWEET_AND_SOUR = "Agridoce"
    BITTER = "Amargo"
    ALMOND = "Amendoado"
    VELVETY = "Aveludado"
    SOUR = "Azedo"
    CARAMELIZED = "Caramelizado"
    CITRUS = "Cítrico"
    COMPLEX = "Complexo"
    SMOKY = "Defumado"
    SWEET = "Doce"
    FRESH = "Fresco"
    FRUITY = "Frutado"
    HERBACEOUS = "Herbáceo"
    BUTTERY = "Manteigoso"
    SPICY = "Picante"
    RICH = "Rico"
    SALTY = "Salgado"
    SMOOTH = "Suave"
    EARTHY = "Terroso"
    TOASTED = "Tostado"
    TROPICAL = "Tropical"
    UMAMI = "Umami"


@unique
class TextureRandomEnum(Enum):
    AIRY = "Aerado"
    CREAMY = "Cremoso"
    CRUNCHY = "Crocante"
    CRUSTY = "Crostinha"
    CRUMBLY = "Esfarelado"
    SPONGY = "Esponjoso"
    FIRM = "Firme"
    FLAKY = "Flocos"
    GELATINOUS = "Gelatinoso"
    GRAINY = "Granuloso"
    LIQUID = "Líquido"
    SMOOTH = "Liso"
    SOFT = "Macio"
    BUTTERY = "Manteigoso"
    OILY = "Oleoso"
    STICKY = "Pegajoso"
    SILKY = "Sedoso"


@unique
class CategoryRandomEnum(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    DESSERT = "dessert"
    DRINK = "drink"


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
