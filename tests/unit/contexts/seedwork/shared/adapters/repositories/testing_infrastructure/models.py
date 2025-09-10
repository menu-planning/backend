"""
SQLAlchemy test models for comprehensive repository testing

This module contains all test database models used for integration testing
of the SaGenericRepository. These models are designed to test:

- Complex relationships (one-to-many, many-to-many)
- Edge cases (circular references, self-referential)
- Real database constraints (foreign keys, check constraints, unique constraints)
- Composite types and advanced column types
- Association tables

All models use the 'test_seedwork' schema to isolate from production data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

import src.db.sa_field_types as sa_field
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship
from src.db.base import SaBase

# Test schema - isolate from production
TEST_SCHEMA = "test_seedwork"

# =============================================================================
# TEST COMPOSITE TYPES (Real DB models for edge cases)
# =============================================================================


@dataclass
class NutriFactsTestSaModel:
    """Test composite type replicating NutriFactsSaModel complexity"""

    calories: float | None = None
    protein: float | None = None
    carbohydrate: float | None = None
    total_fat: float | None = None
    saturated_fat: float | None = None
    trans_fat: float | None = None
    dietary_fiber: float | None = None
    sodium: float | None = None
    sugar: float | None = None
    vitamin_a: float | None = None
    vitamin_c: float | None = None
    iron: float | None = None
    calcium: float | None = None


# =============================================================================
# ASSOCIATION TABLES (Real DB with proper constraints)
# =============================================================================

test_meals_tags_association = Table(
    "test_meals_tags_association",
    SaBase.metadata,
    Column(
        "meal_id", String, ForeignKey(f"{TEST_SCHEMA}.test_meals.id"), primary_key=True
    ),
    Column(
        "tag_id", Integer, ForeignKey(f"{TEST_SCHEMA}.test_tags.id"), primary_key=True
    ),
    schema=TEST_SCHEMA,
    extend_existing=True,
)

test_recipes_tags_association = Table(
    "test_recipes_tags_association",
    SaBase.metadata,
    Column(
        "recipe_id",
        String,
        ForeignKey(f"{TEST_SCHEMA}.test_recipes.id"),
        primary_key=True,
    ),
    Column(
        "tag_id", Integer, ForeignKey(f"{TEST_SCHEMA}.test_tags.id"), primary_key=True
    ),
    schema=TEST_SCHEMA,
    extend_existing=True,
)

test_self_ref_friends_association = Table(
    "test_self_ref_friends",
    SaBase.metadata,
    Column(
        "user_id",
        String,
        ForeignKey(f"{TEST_SCHEMA}.test_self_ref.id"),
        primary_key=True,
    ),
    Column(
        "friend_id",
        String,
        ForeignKey(f"{TEST_SCHEMA}.test_self_ref.id"),
        primary_key=True,
    ),
    schema=TEST_SCHEMA,
    extend_existing=True,
)

# =============================================================================
# TEST SA MODELS (Real database models for comprehensive testing)
# =============================================================================


class TagSaTestModel(SaBase):
    """Test tag model replicating exact structure and relationships"""

    __tablename__ = "test_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    author_id: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # "meal", "recipe", etc.

    __table_args__ = (
        UniqueConstraint(
            "key", "value", "author_id", "type", name="unique_tag_per_author_type"
        ),
        {"schema": TEST_SCHEMA, "extend_existing": True},
    )


class RatingSaTestModel(SaBase):
    """Test rating model for testing recipe relationships"""

    __tablename__ = "test_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    recipe_id: Mapped[str] = mapped_column(
        String, ForeignKey(f"{TEST_SCHEMA}.test_recipes.id"), nullable=False
    )
    taste: Mapped[int] = mapped_column(Integer, nullable=False)
    convenience: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[sa_field.datetime_tz_created]

    __table_args__ = (
        CheckConstraint("taste >= 0 AND taste <= 5", name="check_taste_rating"),
        CheckConstraint(
            "convenience >= 0 AND convenience <= 5", name="check_convenience_rating"
        ),
        {"schema": TEST_SCHEMA, "extend_existing": True},
    )


class IngredientSaTestModel(SaBase):
    """Test ingredient model for testing recipe relationships"""

    __tablename__ = "test_ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    recipe_id: Mapped[str] = mapped_column(
        String, ForeignKey(f"{TEST_SCHEMA}.test_recipes.id"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    product_id: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_positive_quantity"),
        {"schema": TEST_SCHEMA, "extend_existing": True},
    )


class RecipeSaTestModel(SaBase):
    """
    Test recipe model replicating full complexity:
    - 20+ columns including composite nutri_facts
    - Multiple relationships: ingredients, ratings, tags
    - Foreign key to meal
    - Complex column types and constraints
    """

    __tablename__ = "test_recipes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    preprocessed_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    instructions: Mapped[str] = mapped_column(String, nullable=False)
    author_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    meal_id: Mapped[str | None] = mapped_column(
        String, ForeignKey(f"{TEST_SCHEMA}.test_meals.id"), nullable=True
    )
    utensils: Mapped[str | None] = mapped_column(String, nullable=True)
    total_time: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    privacy: Mapped[str | None] = mapped_column(String, nullable=True)
    weight_in_grams: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )
    calorie_density: Mapped[float | None] = mapped_column(
        Float, nullable=True, index=True
    )
    carbo_percentage: Mapped[float | None] = mapped_column(
        Float, nullable=True, index=True
    )
    protein_percentage: Mapped[float | None] = mapped_column(
        Float, nullable=True, index=True
    )
    total_fat_percentage: Mapped[float | None] = mapped_column(
        Float, nullable=True, index=True
    )
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[sa_field.datetime_tz_created]
    updated_at: Mapped[sa_field.datetime_tz_updated]
    discarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    average_taste_rating: Mapped[float | None] = mapped_column(
        Float, nullable=True, index=True
    )
    average_convenience_rating: Mapped[float | None] = mapped_column(
        Float, nullable=True, index=True
    )

    # Individual columns for composite field
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbohydrate: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    saturated_fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    trans_fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    dietary_fiber: Mapped[float | None] = mapped_column(Float, nullable=True)
    sodium: Mapped[float | None] = mapped_column(Float, nullable=True)
    sugar: Mapped[float | None] = mapped_column(Float, nullable=True)
    vitamin_a: Mapped[float | None] = mapped_column(Float, nullable=True)
    vitamin_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    iron: Mapped[float | None] = mapped_column(Float, nullable=True)
    calcium: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Composite field for nutritional facts
    nutri_facts: Mapped[NutriFactsTestSaModel] = composite(
        NutriFactsTestSaModel,
        "calories",
        "protein",
        "carbohydrate",
        "total_fat",
        "saturated_fat",
        "trans_fat",
        "dietary_fiber",
        "sodium",
        "sugar",
        "vitamin_a",
        "vitamin_c",
        "iron",
        "calcium",
    )

    # Relationships with real foreign keys
    ingredients: Mapped[list[IngredientSaTestModel]] = relationship(
        "IngredientSaTestModel",
        lazy="selectin",
        order_by="IngredientSaTestModel.position",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list[TagSaTestModel]] = relationship(
        secondary=test_recipes_tags_association,
        lazy="selectin",
        cascade="save-update, merge",
    )
    ratings: Mapped[list[RatingSaTestModel]] = relationship(
        "RatingSaTestModel",
        lazy="selectin",
        order_by="RatingSaTestModel.created_at",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("total_time >= 0", name="check_positive_total_time"),
        CheckConstraint("weight_in_grams > 0", name="check_positive_weight"),
        Index("idx_recipe_author_created", "author_id", "created_at"),
        {"schema": TEST_SCHEMA, "extend_existing": True},
    )


class MealSaTestModel(SaBase):
    """
    Test meal model replicating full complexity:
    - 25+ columns including composite nutri_facts
    - Multiple relationships: recipes, tags
    - Foreign key to menu (optional)
    - All column types with proper constraints
    """

    __tablename__ = "test_meals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    preprocessed_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    author_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    menu_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # FK to menu if needed
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    total_time: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    like: Mapped[bool | None] = mapped_column(Boolean, nullable=True, index=True)
    weight_in_grams: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )
    calorie_density: Mapped[float | None] = mapped_column(
        Float, nullable=True, index=True
    )
    carbo_percentage: Mapped[float | None] = mapped_column(
        Float, nullable=True, index=True
    )
    protein_percentage: Mapped[float | None] = mapped_column(
        Float, nullable=True, index=True
    )
    total_fat_percentage: Mapped[float | None] = mapped_column(
        Float, nullable=True, index=True
    )
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[sa_field.datetime_tz_created]
    updated_at: Mapped[sa_field.datetime_tz_updated]
    discarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Individual columns for composite field
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbohydrate: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    saturated_fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    trans_fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    dietary_fiber: Mapped[float | None] = mapped_column(Float, nullable=True)
    sodium: Mapped[float | None] = mapped_column(Float, nullable=True)
    sugar: Mapped[float | None] = mapped_column(Float, nullable=True)
    vitamin_a: Mapped[float | None] = mapped_column(Float, nullable=True)
    vitamin_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    iron: Mapped[float | None] = mapped_column(Float, nullable=True)
    calcium: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Composite field for nutritional facts
    nutri_facts: Mapped[NutriFactsTestSaModel] = composite(
        NutriFactsTestSaModel,
        "calories",
        "protein",
        "carbohydrate",
        "total_fat",
        "saturated_fat",
        "trans_fat",
        "dietary_fiber",
        "sodium",
        "sugar",
        "vitamin_a",
        "vitamin_c",
        "iron",
        "calcium",
    )

    # Relationships with real foreign keys
    recipes: Mapped[list[RecipeSaTestModel]] = relationship(
        "RecipeSaTestModel",
        lazy="selectin",
        cascade="save-update, merge",
    )
    tags: Mapped[list[TagSaTestModel]] = relationship(
        secondary=test_meals_tags_association,
        lazy="selectin",
        cascade="save-update, merge",
    )

    __table_args__ = (
        CheckConstraint("total_time >= 0", name="check_positive_meal_total_time"),
        CheckConstraint("weight_in_grams > 0", name="check_positive_meal_weight"),
        Index("idx_meal_author_created", "author_id", "created_at"),
        {"schema": TEST_SCHEMA, "extend_existing": True},
    )


# =============================================================================
# EDGE CASE MODELS (Circular relationships, self-referential)
# =============================================================================


class CircularTestModelA(SaBase):
    """Test model for circular relationships (A -> B -> A)"""

    __tablename__ = "test_circular_a"
    __table_args__ = ({"schema": TEST_SCHEMA, "extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    b_ref_id: Mapped[str | None] = mapped_column(
        String, ForeignKey(f"{TEST_SCHEMA}.test_circular_b.id"), nullable=True
    )

    b_ref: Mapped[CircularTestModelB | None] = relationship(
        "CircularTestModelB", back_populates="a_refs", lazy="selectin"
    )


class CircularTestModelB(SaBase):
    """Test model for circular relationships (B -> A -> B)"""

    __tablename__ = "test_circular_b"
    __table_args__ = ({"schema": TEST_SCHEMA, "extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    a_refs: Mapped[list[CircularTestModelA]] = relationship(
        "CircularTestModelA", back_populates="b_ref", lazy="selectin"
    )


class SelfReferentialTestModel(SaBase):
    """Test model for self-referential relationships"""

    __tablename__ = "test_self_ref"
    __table_args__ = ({"schema": TEST_SCHEMA, "extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        String, ForeignKey(f"{TEST_SCHEMA}.test_self_ref.id"), nullable=True
    )
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    parent: Mapped[SelfReferentialTestModel | None] = relationship(
        "SelfReferentialTestModel",
        remote_side="SelfReferentialTestModel.id",
        back_populates="children",
        lazy="selectin",
    )

    children: Mapped[list[SelfReferentialTestModel]] = relationship(
        "SelfReferentialTestModel", back_populates="parent", lazy="selectin"
    )

    friends: Mapped[list[SelfReferentialTestModel]] = relationship(
        "SelfReferentialTestModel",
        secondary=test_self_ref_friends_association,
        primaryjoin=id == test_self_ref_friends_association.c.user_id,
        secondaryjoin=id == test_self_ref_friends_association.c.friend_id,
        lazy="selectin",
    )


# =============================================================================
# COMPLEX MULTI-TABLE JOIN TEST MODELS
# =============================================================================


class SupplierSaTestModel(SaBase):
    """Test supplier model for complex joins"""

    __tablename__ = "test_suppliers"
    __table_args__ = ({"schema": TEST_SCHEMA, "extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    country: Mapped[str] = mapped_column(String, nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[sa_field.datetime_tz_created]


class ProductSaTestModel(SaBase):
    """Test product model for complex joins"""

    __tablename__ = "test_products"
    __table_args__ = ({"schema": TEST_SCHEMA, "extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    category_id: Mapped[str] = mapped_column(
        String, ForeignKey(f"{TEST_SCHEMA}.test_categories.id"), nullable=False
    )
    supplier_id: Mapped[str] = mapped_column(
        String, ForeignKey(f"{TEST_SCHEMA}.test_suppliers.id"), nullable=False
    )
    price: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[sa_field.datetime_tz_created]

    # Relationships
    category: Mapped[CategorySaTestModel] = relationship(
        "CategorySaTestModel", lazy="selectin"
    )
    supplier: Mapped[SupplierSaTestModel] = relationship(
        "SupplierSaTestModel", lazy="selectin"
    )


class CategorySaTestModel(SaBase):
    """Test category model for complex joins"""

    __tablename__ = "test_categories"
    __table_args__ = ({"schema": TEST_SCHEMA, "extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    parent_id: Mapped[str | None] = mapped_column(
        String, ForeignKey(f"{TEST_SCHEMA}.test_categories.id"), nullable=True
    )

    # Self-referential relationship
    parent: Mapped[CategorySaTestModel | None] = relationship(
        "CategorySaTestModel", remote_side="CategorySaTestModel.id", lazy="selectin"
    )


class OrderSaTestModel(SaBase):
    """Test order model for complex joins"""

    __tablename__ = "test_orders"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    product_id: Mapped[str] = mapped_column(
        String, ForeignKey(f"{TEST_SCHEMA}.test_products.id"), nullable=False
    )
    customer_id: Mapped[str] = mapped_column(
        String, ForeignKey(f"{TEST_SCHEMA}.test_customers.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    order_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(UTC)
    )
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)

    # Relationships
    product: Mapped[ProductSaTestModel] = relationship(
        "ProductSaTestModel", lazy="selectin"
    )
    customer: Mapped[CustomerSaTestModel] = relationship(
        "CustomerSaTestModel", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_positive_order_quantity"),
        CheckConstraint("total_price > 0", name="check_positive_order_price"),
        {"schema": TEST_SCHEMA, "extend_existing": True},
    )


class CustomerSaTestModel(SaBase):
    """Test customer model for complex joins"""

    __tablename__ = "test_customers"
    __table_args__ = ({"schema": TEST_SCHEMA, "extend_existing": True},)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    country: Mapped[str] = mapped_column(String, nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[sa_field.datetime_tz_created]
