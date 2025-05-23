from sqlalchemy import Column, ForeignKey, Table
from src.db.base import SaBase, SerializerMixin

menus_tags_association = Table(
    "menus_tags_association",
    SaBase.metadata,
    Column(
        "menu_id",
        ForeignKey("recipes_catalog.menus.id"),
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
