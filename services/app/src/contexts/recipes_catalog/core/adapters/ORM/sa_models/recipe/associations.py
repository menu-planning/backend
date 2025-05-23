from sqlalchemy import Column, ForeignKey, Table
from src.db.base import SaBase, SerializerMixin

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
        ForeignKey("shared_kernel.tags.id"),
        primary_key=True,
    ),
    schema="recipes_catalog",
    extend_existing=True,
)
