"""
Shared fixtures and mock models for SaGenericRepository testing

This module contains all the mock models, mappers, entities, and fixtures
used across the SaGenericRepository test suite. It replicates the complexity
of real models without database dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column, composite, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.seedwork.shared.adapters.seedwork_repository import (
    SaGenericRepository, FilterColumnMapper
)
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.seedwork.shared.domain.entity import Entity

# Create mock base for testing
MockBase = declarative_base()

# MOCK COMPOSITE TYPES (replicating NutriFactsSaModel complexity)
@dataclass 
class MockNutriFactsSaModel:
    """Mock composite type replicating the complexity of NutriFactsSaModel with 80+ fields"""
    calories: float | None = None
    protein: float | None = None
    carbohydrate: float | None = None
    total_fat: float | None = None
    saturated_fat: float | None = None
    trans_fat: float | None = None
    dietary_fiber: float | None = None
    sodium: float | None = None
    sugar: float | None = None
    # Add more fields to replicate full complexity...
    vitamin_a: float | None = None
    vitamin_c: float | None = None
    iron: float | None = None
    calcium: float | None = None


# MOCK ASSOCIATION TABLES (replicating meals_tags_association complexity)
mock_meals_tags_association = Table(
    "mock_meals_tags_association",
    MockBase.metadata,
    Column("meal_id", String, ForeignKey("mock_meals.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("mock_tags.id"), primary_key=True),
)

mock_recipes_tags_association = Table(
    "mock_recipes_tags_association", 
    MockBase.metadata,
    Column("recipe_id", String, ForeignKey("mock_recipes.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("mock_tags.id"), primary_key=True),
)

# ASSOCIATION TABLE FOR SELF-REFERENTIAL MANY-TO-MANY
mock_self_ref_friends_association = Table(
    "mock_self_ref_friends",
    MockBase.metadata,
    Column("user_id", String, ForeignKey("mock_self_ref.id"), primary_key=True),
    Column("friend_id", String, ForeignKey("mock_self_ref.id"), primary_key=True),
)


# MOCK SA MODELS (replicating exact relationship complexity)
class MockTagSaModel(MockBase):
    """Mock TagSaModel replicating exact structure and relationships"""
    __tablename__ = "mock_tags"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String)
    value: Mapped[str] = mapped_column(String) 
    author_id: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)  # "meal", "recipe", etc.


class MockRatingSaModel(MockBase):
    """Mock RatingSaModel for testing recipe relationships"""
    __tablename__ = "mock_ratings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String)
    recipe_id: Mapped[str] = mapped_column(String, ForeignKey("mock_recipes.id"))
    taste: Mapped[int] = mapped_column(Integer)
    convenience: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class MockIngredientSaModel(MockBase):
    """Mock IngredientSaModel for testing recipe relationships"""
    __tablename__ = "mock_ingredients"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    quantity: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String)
    recipe_id: Mapped[str] = mapped_column(String, ForeignKey("mock_recipes.id"))
    position: Mapped[int] = mapped_column(Integer)
    product_id: Mapped[str] = mapped_column(String, nullable=True)


class MockRecipeSaModel(MockBase):
    """
    Mock RecipeSaModel replicating full complexity:
    - 20+ columns including composite nutri_facts
    - Multiple relationships: ingredients, ratings, tags
    - Foreign key to meal
    - Complex column types (str, int, float, bool, datetime, composite)
    """
    __tablename__ = "mock_recipes"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    preprocessed_name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, nullable=True)
    instructions: Mapped[str] = mapped_column(String)
    author_id: Mapped[str] = mapped_column(String, index=True)
    meal_id: Mapped[str] = mapped_column(String, ForeignKey("mock_meals.id"))
    utensils: Mapped[str] = mapped_column(String, nullable=True)
    total_time: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    notes: Mapped[str] = mapped_column(String, nullable=True)
    privacy: Mapped[str] = mapped_column(String, nullable=True)
    weight_in_grams: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    calorie_density: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    carbo_percentage: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    protein_percentage: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    total_fat_percentage: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    image_url: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    discarded: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    average_taste_rating: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    average_convenience_rating: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    
    # INDIVIDUAL COLUMNS FOR COMPOSITE FIELD (these must exist as actual columns)
    calories: Mapped[float] = mapped_column(Float, nullable=True)
    protein: Mapped[float] = mapped_column(Float, nullable=True)
    carbohydrate: Mapped[float] = mapped_column(Float, nullable=True)
    total_fat: Mapped[float] = mapped_column(Float, nullable=True)
    saturated_fat: Mapped[float] = mapped_column(Float, nullable=True)
    trans_fat: Mapped[float] = mapped_column(Float, nullable=True)
    dietary_fiber: Mapped[float] = mapped_column(Float, nullable=True)
    sodium: Mapped[float] = mapped_column(Float, nullable=True)
    sugar: Mapped[float] = mapped_column(Float, nullable=True)
    vitamin_a: Mapped[float] = mapped_column(Float, nullable=True)
    vitamin_c: Mapped[float] = mapped_column(Float, nullable=True)
    iron: Mapped[float] = mapped_column(Float, nullable=True)
    calcium: Mapped[float] = mapped_column(Float, nullable=True)
    
    # COMPLEX COMPOSITE FIELD (replicating nutri_facts complexity)
    nutri_facts: Mapped[MockNutriFactsSaModel] = composite(
        MockNutriFactsSaModel,
        "calories", "protein", "carbohydrate", "total_fat", "saturated_fat",
        "trans_fat", "dietary_fiber", "sodium", "sugar", "vitamin_a", "vitamin_c", "iron", "calcium"
    )
    
    # COMPLEX RELATIONSHIPS (replicating SQLAlchemy ORM complexity)
    ingredients: Mapped[list[MockIngredientSaModel]] = relationship(
        "MockIngredientSaModel",
        lazy="selectin",
        order_by="MockIngredientSaModel.position",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list[MockTagSaModel]] = relationship(
        secondary=mock_recipes_tags_association,
        lazy="selectin",
        cascade="save-update, merge",
    )
    ratings: Mapped[list[MockRatingSaModel]] = relationship(
        "MockRatingSaModel",
        lazy="selectin", 
        order_by="MockRatingSaModel.created_at",
        cascade="all, delete-orphan",
    )


class MockMealSaModel(MockBase):
    """
    Mock MealSaModel replicating full complexity:
    - 25+ columns including composite nutri_facts  
    - Multiple relationships: recipes, tags
    - Foreign key to menu
    - All column types: str, int, float, bool, datetime, composite
    - Complex association table relationships
    """
    __tablename__ = "mock_meals"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    preprocessed_name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, nullable=True)
    author_id: Mapped[str] = mapped_column(String, index=True)
    menu_id: Mapped[str] = mapped_column(String, nullable=True, index=True)  # ForeignKey omitted for simplicity
    notes: Mapped[str] = mapped_column(String, nullable=True)
    total_time: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    like: Mapped[bool] = mapped_column(Boolean, nullable=True, index=True)
    weight_in_grams: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    calorie_density: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    carbo_percentage: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    protein_percentage: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    total_fat_percentage: Mapped[float] = mapped_column(Float, nullable=True, index=True)
    image_url: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    discarded: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # INDIVIDUAL COLUMNS FOR COMPOSITE FIELD (these must exist as actual columns)
    calories: Mapped[float] = mapped_column(Float, nullable=True)
    protein: Mapped[float] = mapped_column(Float, nullable=True)
    carbohydrate: Mapped[float] = mapped_column(Float, nullable=True)
    total_fat: Mapped[float] = mapped_column(Float, nullable=True)
    saturated_fat: Mapped[float] = mapped_column(Float, nullable=True)
    trans_fat: Mapped[float] = mapped_column(Float, nullable=True)
    dietary_fiber: Mapped[float] = mapped_column(Float, nullable=True)
    sodium: Mapped[float] = mapped_column(Float, nullable=True)
    sugar: Mapped[float] = mapped_column(Float, nullable=True)
    vitamin_a: Mapped[float] = mapped_column(Float, nullable=True)
    vitamin_c: Mapped[float] = mapped_column(Float, nullable=True)
    iron: Mapped[float] = mapped_column(Float, nullable=True)
    calcium: Mapped[float] = mapped_column(Float, nullable=True)
    
    # COMPLEX COMPOSITE FIELD (replicating nutri_facts complexity)
    nutri_facts: Mapped[MockNutriFactsSaModel] = composite(
        MockNutriFactsSaModel,
        "calories", "protein", "carbohydrate", "total_fat", "saturated_fat",
        "trans_fat", "dietary_fiber", "sodium", "sugar", "vitamin_a", "vitamin_c", "iron", "calcium"
    )
    
    # COMPLEX RELATIONSHIPS (replicating SQLAlchemy ORM complexity)
    recipes: Mapped[list[MockRecipeSaModel]] = relationship(
        "MockRecipeSaModel",
        lazy="selectin",
        cascade="save-update, merge",
    )
    tags: Mapped[list[MockTagSaModel]] = relationship(
        secondary=mock_meals_tags_association,
        lazy="selectin",
        cascade="save-update, merge",
    )


# EDGE CASE MODELS
class MockCircularModelA(MockBase):
    """
    Mock model for testing circular relationships (A -> B -> A)
    
    This tests scenarios where Model A references Model B,
    and Model B also references Model A, creating potential infinite loops
    in join resolution and query building.
    """
    __tablename__ = "mock_circular_a"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    b_ref_id: Mapped[str] = mapped_column(String, ForeignKey("mock_circular_b.id"), nullable=True)
    
    # Forward reference to avoid circular import issues
    b_ref: Mapped["MockCircularModelB"] = relationship(
        "MockCircularModelB",
        foreign_keys=[b_ref_id],
        back_populates="a_refs",
        lazy="selectin"
    )


class MockCircularModelB(MockBase):
    """
    Mock model for testing circular relationships (B -> A -> B)
    
    This completes the circular reference with Model A,
    testing repository behavior with bidirectional relationships.
    """
    __tablename__ = "mock_circular_b"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    
    # Back reference to Model A
    a_refs: Mapped[list["MockCircularModelA"]] = relationship(
        "MockCircularModelA",
        foreign_keys="MockCircularModelA.b_ref_id",
        back_populates="b_ref",
        lazy="selectin"
    )


class MockSelfReferentialModel(MockBase):
    """
    Mock model for testing self-referential relationships
    
    Common patterns:
    - Parent/child hierarchies (categories, comments, organizational structure)
    - Friend/follower relationships 
    - Related products or recommendations
    
    This tests repository behavior with same-table joins and recursive queries.
    """
    __tablename__ = "mock_self_ref"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    parent_id: Mapped[str] = mapped_column(String, ForeignKey("mock_self_ref.id"), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=0)  # For hierarchy depth testing
    
    # Self-referential relationships
    parent: Mapped["MockSelfReferentialModel"] = relationship(
        "MockSelfReferentialModel",
        remote_side="MockSelfReferentialModel.id",
        back_populates="children",
        lazy="selectin"
    )
    
    children: Mapped[list["MockSelfReferentialModel"]] = relationship(
        "MockSelfReferentialModel",
        back_populates="parent",
        lazy="selectin",
        cascade="all, delete-orphan"
    )


class MockComplexJoinModel(MockBase):
    """
    Mock model for testing complex join scenarios that stress-test the repository
    
    This model has relationships to ALL other mock models, creating scenarios where:
    - Multiple join paths exist to the same target
    - Deep join chains (4+ levels) are required
    - Ambiguous join resolution must be handled
    """
    __tablename__ = "mock_complex_join"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    
    # References to main models
    meal_id: Mapped[str] = mapped_column(String, ForeignKey("mock_meals.id"), nullable=True)
    recipe_id: Mapped[str] = mapped_column(String, ForeignKey("mock_recipes.id"), nullable=True)
    ingredient_id: Mapped[int] = mapped_column(Integer, ForeignKey("mock_ingredients.id"), nullable=True)
    
    # References to edge case models
    circular_a_id: Mapped[str] = mapped_column(String, ForeignKey("mock_circular_a.id"), nullable=True)
    circular_b_id: Mapped[str] = mapped_column(String, ForeignKey("mock_circular_b.id"), nullable=True)
    self_ref_id: Mapped[str] = mapped_column(String, ForeignKey("mock_self_ref.id"), nullable=True)
    
    # Multiple paths to same data (stress test for join deduplication)
    primary_tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("mock_tags.id"), nullable=True)
    secondary_tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("mock_tags.id"), nullable=True)
    
    # Relationships (testing multiple join paths)
    meal: Mapped[MockMealSaModel] = relationship("MockMealSaModel", lazy="selectin")
    recipe: Mapped[MockRecipeSaModel] = relationship("MockRecipeSaModel", lazy="selectin")
    ingredient: Mapped[MockIngredientSaModel] = relationship("MockIngredientSaModel", lazy="selectin")
    circular_a: Mapped[MockCircularModelA] = relationship("MockCircularModelA", lazy="selectin")
    circular_b: Mapped[MockCircularModelB] = relationship("MockCircularModelB", lazy="selectin")
    self_ref: Mapped[MockSelfReferentialModel] = relationship("MockSelfReferentialModel", lazy="selectin")
    primary_tag: Mapped[MockTagSaModel] = relationship("MockTagSaModel", foreign_keys=[primary_tag_id], lazy="selectin")
    secondary_tag: Mapped[MockTagSaModel] = relationship("MockTagSaModel", foreign_keys=[secondary_tag_id], lazy="selectin")


# Update MockSelfReferentialModel to include many-to-many self-reference
# Move this code before the class definition that references it

# MOCK DOMAIN ENTITIES
class MockMealEntity(Entity):
    """Mock domain entity for testing"""
    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(id)
        self.name = name
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def _update_properties(self, **kwargs):
        """Implementation of abstract method"""
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockRecipeEntity(Entity):
    """Mock domain entity for testing"""
    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(id)
        self.name = name
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def _update_properties(self, **kwargs):
        """Implementation of abstract method"""
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockCircularEntityA(Entity):
    """Mock domain entity for circular model A"""
    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(id)
        self.name = name
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def _update_properties(self, **kwargs):
        """Implementation of abstract method"""
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockSelfReferentialEntity(Entity):
    """Mock domain entity for self-referential model"""
    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(id)
        self.name = name
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def _update_properties(self, **kwargs):
        """Implementation of abstract method"""
        for k, v in kwargs.items():
            setattr(self, k, v)


# MOCK MAPPERS 
class MockMealMapper(ModelMapper):
    """Mock mapper that avoids database dependencies"""
    
    @staticmethod
    async def map_domain_to_sa(session, domain_obj):
        return MockMealSaModel(id=domain_obj.id, name=domain_obj.name)
    
    @staticmethod 
    def map_sa_to_domain(sa_obj):
        return MockMealEntity(id=sa_obj.id, name=sa_obj.name)


class MockRecipeMapper(ModelMapper):
    """Mock mapper that avoids database dependencies"""
    
    @staticmethod
    async def map_domain_to_sa(session, domain_obj):
        return MockRecipeSaModel(id=domain_obj.id, name=domain_obj.name)
    
    @staticmethod
    def map_sa_to_domain(sa_obj): 
        return MockRecipeEntity(id=sa_obj.id, name=sa_obj.name)


class MockCircularMapperA(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(session, domain_obj):
        return MockCircularModelA(id=domain_obj.id, name=domain_obj.name)
    
    @staticmethod 
    def map_sa_to_domain(sa_obj):
        return MockCircularEntityA(id=sa_obj.id, name=sa_obj.name)


class MockSelfReferentialMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(session, domain_obj):
        return MockSelfReferentialModel(id=domain_obj.id, name=domain_obj.name)
    
    @staticmethod 
    def map_sa_to_domain(sa_obj):
        return MockSelfReferentialEntity(id=sa_obj.id, name=sa_obj.name)


# MOCK FILTER COLUMN MAPPERS (replicating real complexity)
MOCK_MEAL_FILTER_MAPPERS = [
    FilterColumnMapper(
        sa_model_type=MockMealSaModel,
        filter_key_to_column_name={
            "id": "id",
            "name": "name", 
            "description": "description",
            "author_id": "author_id",
            "menu_id": "menu_id",
            "total_time": "total_time",
            "weight_in_grams": "weight_in_grams",
            "created_at": "created_at",
            "updated_at": "updated_at",
            "like": "like",
            "calories": "calories",
            "protein": "protein",
            "carbohydrate": "carbohydrate",
            "total_fat": "total_fat",
            "calorie_density": "calorie_density",
            "carbo_percentage": "carbo_percentage",
            "protein_percentage": "protein_percentage",
            "total_fat_percentage": "total_fat_percentage",
            # Removed "tags" and "tags_not_exists" - these require special domain logic
            # Tag filtering cannot be handled by generic filter_stmt method
        },
    ),
    FilterColumnMapper(
        sa_model_type=MockRecipeSaModel,
        filter_key_to_column_name={
            "recipe_id": "id",
            "recipe_name": "name",
        },
        join_target_and_on_clause=[(MockRecipeSaModel, MockMealSaModel.recipes)],
    ),
    FilterColumnMapper(
        sa_model_type=MockIngredientSaModel,
        filter_key_to_column_name={"products": "product_id"},
        join_target_and_on_clause=[
            (MockRecipeSaModel, MockMealSaModel.recipes),
            (MockIngredientSaModel, MockRecipeSaModel.ingredients),
        ],
    ),
]


# FILTER MAPPERS FOR EDGE CASE MODELS
MOCK_EDGE_CASE_FILTER_MAPPERS = [
    # Circular Model A
    FilterColumnMapper(
        sa_model_type=MockCircularModelA,
        filter_key_to_column_name={
            "circular_a_id": "id",
            "circular_a_name": "name",
            "circular_a_b_ref": "b_ref_id",
        },
    ),
    # Circular Model B  
    FilterColumnMapper(
        sa_model_type=MockCircularModelB,
        filter_key_to_column_name={
            "circular_b_id": "id", 
            "circular_b_name": "name",
        },
        join_target_and_on_clause=[(MockCircularModelB, MockCircularModelA.b_ref)],
    ),
    # Self-referential with parent join
    FilterColumnMapper(
        sa_model_type=MockSelfReferentialModel,
        filter_key_to_column_name={
            "self_ref_id": "id",
            "self_ref_name": "name",
            "self_ref_level": "level",
            "parent_name": "name",  # Filter by parent's name
        },
        join_target_and_on_clause=[(MockSelfReferentialModel, MockSelfReferentialModel.parent)],
    ),
    # Complex join model accessing deep relationships
    FilterColumnMapper(
        sa_model_type=MockComplexJoinModel,
        filter_key_to_column_name={
            "complex_id": "id",
            "complex_name": "name",
            "complex_meal_name": "name",  # Via meal relationship
        },
        join_target_and_on_clause=[
            (MockMealSaModel, MockComplexJoinModel.meal),
        ],
    ),
    # Deep join: Complex -> Meal -> Recipe -> Ingredient
    FilterColumnMapper(
        sa_model_type=MockIngredientSaModel,
        filter_key_to_column_name={
            "deep_ingredient_name": "name",
            "deep_ingredient_product": "product_id",
        },
        join_target_and_on_clause=[
            (MockMealSaModel, MockComplexJoinModel.meal),
            (MockRecipeSaModel, MockMealSaModel.recipes),
            (MockIngredientSaModel, MockRecipeSaModel.ingredients),
        ],
    ),
]


# PYTEST FIXTURES
@pytest.fixture
def mock_session():
    """Mock AsyncSession to avoid database dependencies"""
    session = AsyncMock(spec=AsyncSession)
    
    # Create a proper mock result structure
    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = []  # Empty list by default
    mock_result.scalars.return_value = mock_scalars
    
    # Make execute return the mock result directly (not a coroutine)
    session.execute.return_value = mock_result
    
    return session


@pytest.fixture
def meal_repository(mock_session):
    """Create repository with mock meal models and mappers"""
    return SaGenericRepository(
        db_session=mock_session,
        data_mapper=MockMealMapper,
        domain_model_type=MockMealEntity,
        sa_model_type=MockMealSaModel,
        filter_to_column_mappers=MOCK_MEAL_FILTER_MAPPERS,
    )


@pytest.fixture
def circular_repository(mock_session):
    """Repository using circular model A as base"""
    return SaGenericRepository(
        db_session=mock_session,
        data_mapper=MockCircularMapperA,
        domain_model_type=MockCircularEntityA,
        sa_model_type=MockCircularModelA,
        filter_to_column_mappers=MOCK_EDGE_CASE_FILTER_MAPPERS,
    )


@pytest.fixture
def self_ref_repository(mock_session):
    """Repository using self-referential model"""
    return SaGenericRepository(
        db_session=mock_session,
        data_mapper=MockSelfReferentialMapper,
        domain_model_type=MockSelfReferentialEntity,
        sa_model_type=MockSelfReferentialModel,
        filter_to_column_mappers=MOCK_EDGE_CASE_FILTER_MAPPERS,
    ) 