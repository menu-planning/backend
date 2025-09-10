"""SQLAlchemy models for catalog products and embedded score dataclass."""

from dataclasses import dataclass, fields
from decimal import Decimal

import src.db.sa_field_types as sa_field
from sqlalchemy import TEXT, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship
from src.contexts.products_catalog.core.adapters.ORM.sa_models.brand import (
    BrandSaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.category_sa_model import (
    CategorySaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.food_group_sa_model import (
    FoodGroupSaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.parent_categorysa_model import (
    ParentCategorySaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.process_type_sa_model import (
    ProcessTypeSaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.is_food_votes import (
    IsFoodVotesSaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.source import (
    SourceSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import (
    NutriFactsSaModel,
)
from src.db.base import SaBase, SerializerMixin


@dataclass
class ScoreSaModel:
    """Dataclass for product score composite attribute.

    Attributes:
        final_score: Final product score.
        ingredients_score: Ingredients-based score.
        nutrients_score: Nutrients-based score.
    """

    final_score: float | None = None
    ingredients_score: float | None = None
    nutrients_score: float | None = None


class ProductSaModel(SerializerMixin, SaBase):
    """SQLAlchemy model for products catalog products.

    Represents the main product entity with all its attributes including
    nutritional information, classifications, and voting data.
    """

    __tablename__ = "products"

    id: Mapped[sa_field.strpk]
    source_id: Mapped[str] = mapped_column(
        ForeignKey("products_catalog.sources.id"), index=True
    )
    source: Mapped[SourceSaModel] = relationship(
        lazy="selectin",
        cascade="save-update, merge",
    )
    name: Mapped[sa_field.str_required_idx]
    preprocessed_name: Mapped[str | None] = mapped_column(index=True)
    shopping_name: Mapped[str | None]
    store_department_name: Mapped[str | None]
    recommended_brands_and_products: Mapped[str | None]
    edible_yield: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        default=Decimal("1.0"),
    )
    kg_per_unit: Mapped[float | None]
    liters_per_kg: Mapped[float | None]
    nutrition_group: Mapped[str | None]
    cooking_factor: Mapped[float | None]
    conservation_days: Mapped[int | None]
    substitutes: Mapped[str | None]
    brand_id: Mapped[str | None] = mapped_column(
        ForeignKey("products_catalog.brands.id"), index=True
    )
    brand: Mapped[BrandSaModel | None] = relationship(
        foreign_keys=[brand_id],
        lazy="selectin",
        cascade="save-update, merge",
    )
    is_food: Mapped[bool | None]
    is_food_houses_choice: Mapped[bool | None]
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("products_catalog.classifications.id")
    )
    category: Mapped[CategorySaModel | None] = relationship(
        foreign_keys=[category_id],
        lazy="selectin",
        cascade="save-update, merge",
    )
    parent_category_id: Mapped[str | None] = mapped_column(
        ForeignKey("products_catalog.classifications.id")
    )
    parent_category: Mapped[ParentCategorySaModel | None] = relationship(
        foreign_keys=[parent_category_id],
        lazy="selectin",
        cascade="save-update, merge",
    )
    food_group_id: Mapped[str | None] = mapped_column(
        ForeignKey("products_catalog.classifications.id")
    )
    food_group: Mapped[FoodGroupSaModel | None] = relationship(
        foreign_keys=[food_group_id],
        lazy="selectin",
        cascade="save-update, merge",
    )
    process_type_id: Mapped[str | None] = mapped_column(
        ForeignKey("products_catalog.classifications.id")
    )
    process_type: Mapped[ProcessTypeSaModel | None] = relationship(
        foreign_keys=[process_type_id],
        lazy="selectin",
        cascade="save-update, merge",
    )
    final_score: Mapped[float | None]
    ingredients_score: Mapped[float | None]
    nutrients_score: Mapped[float | None]
    score: Mapped[ScoreSaModel] = composite(
        ScoreSaModel,
        "final_score",
        "ingredients_score",
        "nutrients_score",
    )
    barcode: Mapped[str | None] = mapped_column(index=True)
    ingredients: Mapped[str | None] = mapped_column(TEXT)
    package_size: Mapped[float | None]
    package_size_unit: Mapped[str | None]
    image_url: Mapped[str | None]
    nutri_facts: Mapped[NutriFactsSaModel] = composite(
        *[mapped_column(i.name) for i in fields(NutriFactsSaModel)]
    )
    created_at: Mapped[sa_field.datetime_tz_updated]
    updated_at: Mapped[sa_field.datetime_tz_updated]
    json_data: Mapped[str | None] = mapped_column(TEXT)
    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)
    is_food_votes: Mapped[list[IsFoodVotesSaModel]] = relationship(
        lazy="selectin",
        cascade="save-update, merge",
    )

    __table_args__ = (
        Index(
            "ix_products_catalog_products_preprocessed_name_gin_trgm",
            "preprocessed_name",
            postgresql_ops={"preprocessed_name": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
        {"schema": "products_catalog", "extend_existing": True},
    )
