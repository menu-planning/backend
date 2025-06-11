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

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Table, 
    UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column, composite

from src.db.base import SaBase

# Test schema - isolate from production
TEST_SCHEMA = "test_seedwork"

# =============================================================================
# TEST COMPOSITE TYPES (Real DB models for edge cases)
# =============================================================================

class TestNutriFactsSaModel:
    """Test composite type replicating NutriFactsSaModel complexity"""
    def __init__(
        self,
        calories: Optional[float] = None,
        protein: Optional[float] = None,
        carbohydrate: Optional[float] = None,
        total_fat: Optional[float] = None,
        saturated_fat: Optional[float] = None,
        trans_fat: Optional[float] = None,
        dietary_fiber: Optional[float] = None,
        sodium: Optional[float] = None,
        sugar: Optional[float] = None,
        vitamin_a: Optional[float] = None,
        vitamin_c: Optional[float] = None,
        iron: Optional[float] = None,
        calcium: Optional[float] = None,
    ):
        self.calories = calories
        self.protein = protein
        self.carbohydrate = carbohydrate
        self.total_fat = total_fat
        self.saturated_fat = saturated_fat
        self.trans_fat = trans_fat
        self.dietary_fiber = dietary_fiber
        self.sodium = sodium
        self.sugar = sugar
        self.vitamin_a = vitamin_a
        self.vitamin_c = vitamin_c
        self.iron = iron
        self.calcium = calcium

# =============================================================================
# ASSOCIATION TABLES (Real DB with proper constraints)
# =============================================================================

test_meals_tags_association = Table(
    "test_meals_tags_association",
    SaBase.metadata,
    Column("meal_id", String, ForeignKey(f"{TEST_SCHEMA}.test_meals.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey(f"{TEST_SCHEMA}.test_tags.id"), primary_key=True),
    schema=TEST_SCHEMA
)

test_recipes_tags_association = Table(
    "test_recipes_tags_association", 
    SaBase.metadata,
    Column("recipe_id", String, ForeignKey(f"{TEST_SCHEMA}.test_recipes.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey(f"{TEST_SCHEMA}.test_tags.id"), primary_key=True),
    schema=TEST_SCHEMA
)

test_self_ref_friends_association = Table(
    "test_self_ref_friends",
    SaBase.metadata,
    Column("user_id", String, ForeignKey(f"{TEST_SCHEMA}.test_self_ref.id"), primary_key=True),
    Column("friend_id", String, ForeignKey(f"{TEST_SCHEMA}.test_self_ref.id"), primary_key=True),
    schema=TEST_SCHEMA
)

# =============================================================================
# TEST SA MODELS (Real database models for comprehensive testing)
# =============================================================================

class TestTagSaModel(SaBase):
    """Test tag model replicating exact structure and relationships"""
    __tablename__ = "test_tags"
    __table_args__ = {"schema": TEST_SCHEMA}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False) 
    author_id: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # "meal", "recipe", etc.
    
    __table_args__ = (
        UniqueConstraint('key', 'value', 'author_id', 'type', name='unique_tag_per_author_type'),
        {"schema": TEST_SCHEMA}
    )

class TestRatingSaModel(SaBase):
    """Test rating model for testing recipe relationships"""
    __tablename__ = "test_ratings"
    __table_args__ = {"schema": TEST_SCHEMA}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    recipe_id: Mapped[str] = mapped_column(String, ForeignKey(f"{TEST_SCHEMA}.test_recipes.id"), nullable=False)
    taste: Mapped[int] = mapped_column(Integer, nullable=False)
    convenience: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('taste >= 0 AND taste <= 5', name='check_taste_rating'),
        CheckConstraint('convenience >= 0 AND convenience <= 5', name='check_convenience_rating'),
        {"schema": TEST_SCHEMA}
    )

class TestIngredientSaModel(SaBase):
    """Test ingredient model for testing recipe relationships"""
    __tablename__ = "test_ingredients"
    __table_args__ = {"schema": TEST_SCHEMA}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    recipe_id: Mapped[str] = mapped_column(String, ForeignKey(f"{TEST_SCHEMA}.test_recipes.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    product_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_positive_quantity'),
        {"schema": TEST_SCHEMA}
    )

class TestRecipeSaModel(SaBase):
    """
    Test recipe model replicating full complexity:
    - 20+ columns including composite nutri_facts
    - Multiple relationships: ingredients, ratings, tags
    - Foreign key to meal
    - Complex column types and constraints
    """
    __tablename__ = "test_recipes"
    __table_args__ = {"schema": TEST_SCHEMA}
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    preprocessed_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    instructions: Mapped[str] = mapped_column(String, nullable=False)
    author_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    meal_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey(f"{TEST_SCHEMA}.test_meals.id"), nullable=True)
    utensils: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    total_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    privacy: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    weight_in_grams: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    calorie_density: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    carbo_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    protein_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    total_fat_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    discarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    average_taste_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    average_convenience_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    
    # Individual columns for composite field
    calories: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    protein: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    carbohydrate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_fat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    saturated_fat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    trans_fat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dietary_fiber: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sodium: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sugar: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vitamin_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vitamin_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    iron: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    calcium: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Composite field for nutritional facts
    nutri_facts: Mapped[TestNutriFactsSaModel] = composite(
        TestNutriFactsSaModel,
        "calories", "protein", "carbohydrate", "total_fat", "saturated_fat",
        "trans_fat", "dietary_fiber", "sodium", "sugar", "vitamin_a", "vitamin_c", "iron", "calcium"
    )
    
    # Relationships with real foreign keys
    ingredients: Mapped[list[TestIngredientSaModel]] = relationship(
        "TestIngredientSaModel",
        lazy="selectin",
        order_by="TestIngredientSaModel.position",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list[TestTagSaModel]] = relationship(
        secondary=test_recipes_tags_association,
        lazy="selectin",
        cascade="save-update, merge",
    )
    ratings: Mapped[list[TestRatingSaModel]] = relationship(
        "TestRatingSaModel",
        lazy="selectin", 
        order_by="TestRatingSaModel.created_at",
        cascade="all, delete-orphan",
    )
    
    __table_args__ = (
        CheckConstraint('total_time >= 0', name='check_positive_total_time'),
        CheckConstraint('weight_in_grams > 0', name='check_positive_weight'),
        Index('idx_recipe_author_created', 'author_id', 'created_at'),
        {"schema": TEST_SCHEMA}
    )

class TestMealSaModel(SaBase):
    """
    Test meal model replicating full complexity:
    - 25+ columns including composite nutri_facts  
    - Multiple relationships: recipes, tags
    - Foreign key to menu (optional)
    - All column types with proper constraints
    """
    __tablename__ = "test_meals"
    __table_args__ = {"schema": TEST_SCHEMA}
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    preprocessed_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    author_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    menu_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # FK to menu if needed
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    total_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    like: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, index=True)
    weight_in_grams: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    calorie_density: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    carbo_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    protein_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    total_fat_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    discarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Individual columns for composite field
    calories: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    protein: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    carbohydrate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_fat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    saturated_fat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    trans_fat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dietary_fiber: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sodium: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sugar: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vitamin_a: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vitamin_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    iron: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    calcium: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Composite field for nutritional facts
    nutri_facts: Mapped[TestNutriFactsSaModel] = composite(
        TestNutriFactsSaModel,
        "calories", "protein", "carbohydrate", "total_fat", "saturated_fat",
        "trans_fat", "dietary_fiber", "sodium", "sugar", "vitamin_a", "vitamin_c", "iron", "calcium"
    )
    
    # Relationships with real foreign keys
    recipes: Mapped[list[TestRecipeSaModel]] = relationship(
        "TestRecipeSaModel",
        lazy="selectin",
        cascade="save-update, merge",
    )
    tags: Mapped[list[TestTagSaModel]] = relationship(
        secondary=test_meals_tags_association,
        lazy="selectin",
        cascade="save-update, merge",
    )
    
    __table_args__ = (
        CheckConstraint('total_time >= 0', name='check_positive_meal_total_time'),
        CheckConstraint('weight_in_grams > 0', name='check_positive_meal_weight'),
        Index('idx_meal_author_created', 'author_id', 'created_at'),
        {"schema": TEST_SCHEMA}
    )

# =============================================================================
# EDGE CASE MODELS (Circular relationships, self-referential)
# =============================================================================

class TestCircularModelA(SaBase):
    """Test model for circular relationships (A -> B -> A)"""
    __tablename__ = "test_circular_a"
    __table_args__ = {"schema": TEST_SCHEMA}
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    b_ref_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey(f"{TEST_SCHEMA}.test_circular_b.id"), nullable=True)
    
    b_ref: Mapped[Optional["TestCircularModelB"]] = relationship(
        "TestCircularModelB", 
        back_populates="a_refs",
        lazy="selectin"
    )

class TestCircularModelB(SaBase):
    """Test model for circular relationships (B -> A -> B)"""
    __tablename__ = "test_circular_b"
    __table_args__ = {"schema": TEST_SCHEMA}
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    
    a_refs: Mapped[list[TestCircularModelA]] = relationship(
        "TestCircularModelA",
        back_populates="b_ref",
        lazy="selectin"
    )

class TestSelfReferentialModel(SaBase):
    """Test model for self-referential relationships"""
    __tablename__ = "test_self_ref"
    __table_args__ = {"schema": TEST_SCHEMA}
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey(f"{TEST_SCHEMA}.test_self_ref.id"), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    parent: Mapped[Optional["TestSelfReferentialModel"]] = relationship(
        "TestSelfReferentialModel",
        remote_side="TestSelfReferentialModel.id",
        back_populates="children",
        lazy="selectin"
    )
    
    children: Mapped[list["TestSelfReferentialModel"]] = relationship(
        "TestSelfReferentialModel",
        back_populates="parent",
        lazy="selectin"
    )
    
    friends: Mapped[list["TestSelfReferentialModel"]] = relationship(
        "TestSelfReferentialModel",
        secondary=test_self_ref_friends_association,
        primaryjoin=id == test_self_ref_friends_association.c.user_id,
        secondaryjoin=id == test_self_ref_friends_association.c.friend_id,
        lazy="selectin"
    )