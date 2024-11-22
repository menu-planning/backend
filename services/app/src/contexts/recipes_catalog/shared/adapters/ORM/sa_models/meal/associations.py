from sqlalchemy import Column, ForeignKey, Table
from src.db.base import SaBase

meals_tags_association = Table(
    "meals_tags_association",
    SaBase.metadata,
    Column(
        "meal_id",
        ForeignKey("recipes_catalog.meals.id"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        ForeignKey("recipes_catalog.tags.id"),
        primary_key=True,
    ),
    schema="recipes_catalog",
    extend_existing=True,
)


meals_season_association = Table(
    "meals_season_association",
    SaBase.metadata,
    Column("meal_id", ForeignKey("recipes_catalog.meals.id"), primary_key=True),
    Column("season_id", ForeignKey("recipes_catalog.months.id"), primary_key=True),
    schema="recipes_catalog",
    extend_existing=True,
)

meals_diet_types_association = Table(
    "meals_diet_types_association",
    SaBase.metadata,
    Column(
        "meal_id",
        ForeignKey("recipes_catalog.meals.id"),
        primary_key=True,
    ),
    Column(
        "diet_type_id",
        ForeignKey("shared_kernel.diet_types.id"),
        primary_key=True,
    ),
    schema="recipes_catalog",
    extend_existing=True,
)

meals_allergens_association = Table(
    "meals_allergens_association",
    SaBase.metadata,
    Column("meal_id", ForeignKey("recipes_catalog.meals.id"), primary_key=True),
    Column("allergen_name", ForeignKey("shared_kernel.allergens.id"), primary_key=True),
    schema="recipes_catalog",
    extend_existing=True,
)

meals_cuisines_association = Table(
    "meals_cuisines_association",
    SaBase.metadata,
    Column(
        "meal_id",
        ForeignKey("recipes_catalog.meals.id"),
        primary_key=True,
    ),
    Column(
        "cuisine_id",
        ForeignKey("shared_kernel.cuisines.id"),
        primary_key=True,
    ),
    schema="recipes_catalog",
    extend_existing=True,
)

meals_flavors_association = Table(
    "meals_flavors_association",
    SaBase.metadata,
    Column(
        "meal_id",
        ForeignKey("recipes_catalog.meals.id"),
        primary_key=True,
    ),
    Column(
        "flavor_id",
        ForeignKey("shared_kernel.flavors.id"),
        primary_key=True,
    ),
    schema="recipes_catalog",
    extend_existing=True,
)

meals_textures_association = Table(
    "meals_textures_association",
    SaBase.metadata,
    Column(
        "meal_id",
        ForeignKey("recipes_catalog.meals.id"),
        primary_key=True,
    ),
    Column(
        "texture_id",
        ForeignKey("shared_kernel.textures.id"),
        primary_key=True,
    ),
    schema="recipes_catalog",
    extend_existing=True,
)
