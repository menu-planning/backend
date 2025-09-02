from sqlalchemy import Column, ForeignKey, Table
from src.db.base import SaBase

# Association table linking meals to tags.
# Many-to-many relationship between meals and tags for flexible
# categorization and filtering of meal entities.
# Schema: recipes_catalog. Table: meals_tags_association.
# Foreign keys: meals.id, shared_kernel.tags.id.
# Composite primary key: (meal_id, tag_id) ensures unique associations.
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
        ForeignKey("shared_kernel.tags.id"),
        primary_key=True,
    ),
    schema="recipes_catalog",
    extend_existing=True,
)

# Association table linking recipes to tags.
# Many-to-many relationship between recipes and tags for flexible
# categorization and filtering of recipe entities.
# Schema: recipes_catalog. Table: recipes_tags_association.
# Foreign keys: recipes.id, shared_kernel.tags.id.
# Composite primary key: (recipe_id, tag_id) ensures unique associations.
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
