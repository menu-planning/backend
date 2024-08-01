from sqlalchemy import Column, ForeignKey, Table
from src.db.base import SaBase

products_allergens_association = Table(
    "products_allergens_association",
    SaBase.metadata,
    Column(
        "product_id",
        ForeignKey("products_catalog.products.id"),
        primary_key=True,
    ),
    Column(
        "allergen_id",
        ForeignKey("shared_kernel.allergens.id"),
        primary_key=True,
    ),
    schema="products_catalog",
    extend_existing=True,
)

products_diet_types_association = Table(
    "products_diet_types_association",
    SaBase.metadata,
    Column(
        "product_id",
        ForeignKey("products_catalog.products.id"),
        primary_key=True,
    ),
    Column(
        "diet_type_id",
        ForeignKey("shared_kernel.diet_types.id"),
        primary_key=True,
    ),
    schema="products_catalog",
    extend_existing=True,
)
