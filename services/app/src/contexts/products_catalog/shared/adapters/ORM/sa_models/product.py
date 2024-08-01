from dataclasses import dataclass, fields
from datetime import datetime

import src.db.sa_field_types as sa_field
from sqlalchemy import TEXT, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.association_tables import (
    products_allergens_association,
    products_diet_types_association,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.brand import (
    BrandSaModel,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.is_food_votes import (
    IsFoodVotesSaModel,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.source import (
    SourceSaModel,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.category import (
    CategorySaModel,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.food_group import (
    FoodGroupSaModel,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.parent_category import (
    ParentCategorySaModel,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.process_type import (
    ProcessTypeSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.allergen import AllergenSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.diet_type import DietTypeSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts import (
    NutriFactsSaModel,
)
from src.db.base import SaBase


@dataclass
class ScoreSaModel:
    final_score: float | None = None
    ingredients_score: float | None = None
    nutrients_score: float | None = None


class ProductSaModel(SaBase):
    __tablename__ = "products"

    id: Mapped[sa_field.strpk]
    source_id: Mapped[str] = mapped_column(
        ForeignKey("products_catalog.sources.id"), index=True
    )
    source: Mapped[SourceSaModel] = relationship(
        foreign_keys=[source_id], lazy="selectin"
    )
    name: Mapped[sa_field.str_required_idx]
    preprocessed_name: Mapped[str | None] = mapped_column(index=True)
    brand_id: Mapped[str | None] = mapped_column(
        ForeignKey("products_catalog.brands.id"), index=True
    )
    brand: Mapped[BrandSaModel | None] = relationship(
        foreign_keys=[brand_id], lazy="selectin"
    )
    is_food: Mapped[bool | None]
    is_food_houses_choice: Mapped[bool | None]
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("products_catalog.tags.id")
    )
    category: Mapped[CategorySaModel | None] = relationship(
        foreign_keys=[category_id], lazy="selectin"
    )
    parent_category_id: Mapped[str | None] = mapped_column(
        ForeignKey("products_catalog.tags.id")
    )
    parent_category: Mapped[ParentCategorySaModel | None] = relationship(
        foreign_keys=[parent_category_id], lazy="selectin"
    )
    food_group_id: Mapped[str | None] = mapped_column(
        ForeignKey("products_catalog.tags.id")
    )
    food_group: Mapped[FoodGroupSaModel | None] = relationship(
        foreign_keys=[food_group_id], lazy="selectin"
    )
    process_type_id: Mapped[str | None] = mapped_column(
        ForeignKey("products_catalog.tags.id")
    )
    process_type: Mapped[ProcessTypeSaModel | None] = relationship(
        foreign_keys=[process_type_id], lazy="selectin"
    )
    diet_types: Mapped[list[DietTypeSaModel]] = relationship(
        secondary=products_diet_types_association, lazy="selectin"
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
    allergens: Mapped[list[AllergenSaModel]] = relationship(
        secondary=products_allergens_association, lazy="selectin"
    )
    package_size: Mapped[float | None]
    package_size_unit: Mapped[str | None]
    image_url: Mapped[str | None]
    nutri_facts: Mapped[NutriFactsSaModel] = composite(
        *[mapped_column(i.name) for i in fields(NutriFactsSaModel)]
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    json_data: Mapped[str | None] = mapped_column(TEXT)
    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)
    is_food_votes: Mapped[list[IsFoodVotesSaModel]] = relationship(lazy="selectin")

    __table_args__ = (
        Index(
            "ix_products_catalog_products_preprocessed_name_gin_trgm",
            "preprocessed_name",
            postgresql_ops={"preprocessed_name": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
        {"schema": "products_catalog", "extend_existing": True},
    )
