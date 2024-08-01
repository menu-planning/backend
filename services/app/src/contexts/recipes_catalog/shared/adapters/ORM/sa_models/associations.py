from sqlalchemy import Column, ForeignKey, Table
from src.db.base import SaBase

recipes_tags_association = Table(
    "recipes_tags_association",
    SaBase.metadata,
    Column(
        "recipe_id",
        ForeignKey("recipes_catalog.recipes.id"),
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


recipes_season_association = Table(
    "recipes_season_association",
    SaBase.metadata,
    Column("recipe_id", ForeignKey("recipes_catalog.recipes.id"), primary_key=True),
    Column("season_id", ForeignKey("recipes_catalog.months.id"), primary_key=True),
    schema="recipes_catalog",
    extend_existing=True,
)

recipes_diet_types_association = Table(
    "recipes_diet_types_association",
    SaBase.metadata,
    Column(
        "recipe_id",
        ForeignKey("recipes_catalog.recipes.id"),
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
