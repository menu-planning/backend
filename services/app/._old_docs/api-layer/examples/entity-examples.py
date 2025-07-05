"""
API Entity Examples

This module demonstrates practical implementation of API entity patterns following 
the documented BaseApiEntity inheritance and serialization methods.

All examples are working code that demonstrate the entity patterns used in the actual codebase.

IMPORT STRATEGY:
- ACTUAL CODEBASE IMPORTS: Base classes, infrastructure, and shared types
  (BaseApiEntity, Entity, ORM models, etc.) - These define the framework
- SIMULATED EXAMPLES: Domain entities and value objects specific to examples
  (ExampleDomainRecipe, ExampleIngredient, etc.) - These demonstrate usage

This hybrid approach ensures examples stay synchronized with the actual API
while providing clear, focused demonstrations without coupling to real business logic.

MAINTENANCE NOTES:
- If base classes change, examples may need updates
- Keep simulated objects simple and focused on demonstrating patterns
- Real imports should be limited to stable, framework-level classes
"""

from __future__ import annotations
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, FrozenSet
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated

# Actual imports from the codebase
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.ingredient_sa_model import IngredientSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import RecipeSaModel
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiEntity

from src.contexts.seedwork.shared.domain.entity import Entity
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import TagSaModel
from src.contexts.shared_kernel.domain.value_objects.tag import Tag

# For examples (simulated domain entities)
from enum import Enum
from attrs import frozen


# =============================================================================
# SIMULATED DOMAIN ENTITIES (for examples)
# =============================================================================

class ExamplePrivacy(Enum):
    PUBLIC = "public"
    PRIVATE = "private"

class ExampleMeasureUnit(Enum):
    GRAMS = "grams"
    MILLILITERS = "milliliters"
    LITERS = "liters"
    OUNCES = "ounces"
    POUNDS = "pounds"

@frozen(kw_only=True)
class ExampleIngredient:
    name: str
    unit: ExampleMeasureUnit
    quantity: float
    position: int
    full_text: str | None = None
    product_id: str | None = None

@frozen(kw_only=True)
class ExampleNutriFacts:
    """Simulated nutrition facts value object."""
    calories: float
    protein: float
    carbs: float
    fat: float
    
    def __add__(self, other: 'ExampleNutriFacts') -> 'ExampleNutriFacts':
        return ExampleNutriFacts(
            calories=self.calories + other.calories,
            protein=self.protein + other.protein,
            carbs=self.carbs + other.carbs,
            fat=self.fat + other.fat,
        )

class _ExampleDomainRecipe(Entity):
    """Simulated domain recipe entity with key patterns."""
    
    def __init__(
        self,
        *,
        id: str,
        name: str,
        author_id: str,
        meal_id: str,
        ingredients: List[ExampleIngredient],
        instructions: str,
        privacy: ExamplePrivacy = ExamplePrivacy.PRIVATE,
        nutri_facts: ExampleNutriFacts | None = None,
        total_time: int | None = None,
        tags: set[Tag] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Simplified domain recipe constructor."""
        super().__init__(id=id, discarded=discarded, version=version, created_at=created_at, updated_at=updated_at)
        self._name = name
        self._author_id = author_id
        self._meal_id = meal_id
        self._ingredients = ingredients
        self._instructions = instructions
        self._privacy = privacy
        self._nutri_facts = nutri_facts
        self._total_time = total_time
        self._tags = tags or set()

    @property
    def name(self) -> str:
        return self._name

    def _set_name(self, value: str) -> None:
        """Protected setter for name."""
        if self._name != value:
            self._name = value
            self._increment_version()

    @property
    def author_id(self) -> str:
        return self._author_id

    @property
    def meal_id(self) -> str:
        return self._meal_id

    @property
    def ingredients(self) -> List[ExampleIngredient]:
        return self._ingredients

    def _set_ingredients(self, value: List[ExampleIngredient]) -> None:
        """Protected setter for ingredients."""
        self._ingredients = value
        self._increment_version()

    @property
    def instructions(self) -> str:
        return self._instructions

    def _set_instructions(self, value: str) -> None:
        """Protected setter for instructions."""
        if self._instructions != value:
            self._instructions = value
            self._increment_version()

    @property
    def privacy(self) -> ExamplePrivacy:
        return self._privacy

    def _set_privacy(self, value: ExamplePrivacy) -> None:
        """Protected setter for privacy."""
        if self._privacy != value:
            self._privacy = value
            self._increment_version()

    @property
    def nutri_facts(self) -> ExampleNutriFacts | None:
        return self._nutri_facts

    def _set_nutri_facts(self, value: ExampleNutriFacts | None) -> None:
        """Protected setter for nutri_facts."""
        if self._nutri_facts != value:
            self._nutri_facts = value
            self._increment_version()

    @property
    def total_time(self) -> int | None:
        return self._total_time

    def _set_total_time(self, value: int | None) -> None:
        """Protected setter for total_time."""
        if self._total_time != value:
            self._total_time = value
            self._increment_version()

    @property
    def tags(self) -> set[Tag]:
        return self._tags

    def _set_tags(self, value: set[Tag]) -> None:
        """Protected setter for tags."""
        self._tags = value or set()
        self._increment_version()

    def update_properties(self, **kwargs) -> None:
        """Update multiple properties atomically through protected setters."""
        if not kwargs:
            return
        
        # Store original version for single increment
        original_version = self.version
        
        # Apply property updates using protected setters
        for key, value in kwargs.items():
            setter_method_name = f"_set_{key}"
            if hasattr(self, setter_method_name):
                setter_method = getattr(self, setter_method_name)
                setter_method(value)
            else:
                raise AttributeError(f"Recipe has no updatable property '{key}'")
        
        # Set version manually to avoid multiple increments
        self._version = original_version + 1


class ExampleDomainMeal(Entity):
    """Simulated domain meal entity with cached properties and update methods."""
    
    def __init__(
        self,
        *,
        id: str,
        name: str,
        author_id: str,
        menu_id: str | None = None,
        recipes: list[_ExampleDomainRecipe] | None = None,
        tags: set[Tag] | None = None,
        description: str | None = None,
        notes: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Simplified domain meal constructor."""
        super().__init__(id=id, discarded=discarded, version=version, created_at=created_at, updated_at=updated_at)
        self._name = name
        self._author_id = author_id
        self._menu_id = menu_id
        self._recipes = recipes if recipes else []
        self._tags = tags if tags else set()
        self._description = description
        self._notes = notes

    @property
    def name(self) -> str:
        return self._name

    def _set_name(self, value: str) -> None:
        """Protected setter for name."""
        if self._name != value:
            self._name = value
            self._increment_version()

    @property
    def author_id(self) -> str:
        return self._author_id

    @property
    def menu_id(self) -> str | None:
        return self._menu_id

    def _set_menu_id(self, value: str | None) -> None:
        """Protected setter for menu_id."""
        if self._menu_id != value:
            self._menu_id = value
            self._increment_version()

    @property
    def recipes(self) -> List[_ExampleDomainRecipe]:
        return [recipe for recipe in self._recipes if not recipe.discarded]

    def _set_recipes(self, value: List[_ExampleDomainRecipe]) -> None:
        """Protected setter for recipes."""
        self._recipes = value if value else []
        self._increment_version()
        # Invalidate cached properties that depend on recipes
        if hasattr(self, '_cached_nutri_facts'):
            delattr(self, '_cached_nutri_facts')

    @property
    def tags(self) -> set[Tag]:
        return self._tags

    def _set_tags(self, value: set[Tag]) -> None:
        """Protected setter for tags."""
        self._tags = value if value else set()
        self._increment_version()

    @property
    def description(self) -> str | None:
        return self._description

    def _set_description(self, value: str | None) -> None:
        """Protected setter for description."""
        if self._description != value:
            self._description = value
            self._increment_version()

    @property
    def notes(self) -> str | None:
        return self._notes

    def _set_notes(self, value: str | None) -> None:
        """Protected setter for notes."""
        if self._notes != value:
            self._notes = value
            self._increment_version()

    @property
    def nutri_facts(self) -> ExampleNutriFacts | None:
        """
        Cached property that aggregates nutritional facts from all recipes.
        
        This simulates the cached_property pattern used in the real domain classes.
        """
        if not hasattr(self, '_cached_nutri_facts'):
            total_nutri_facts = None
            
            for recipe in self.recipes:
                if recipe.nutri_facts:
                    if total_nutri_facts is None:
                        total_nutri_facts = recipe.nutri_facts
                    else:
                        total_nutri_facts = total_nutri_facts + recipe.nutri_facts
            
            self._cached_nutri_facts = total_nutri_facts
        
        return self._cached_nutri_facts

    @property
    def total_time(self) -> int | None:
        """Computed property: maximum time from all recipes."""
        times = [recipe.total_time for recipe in self.recipes if recipe.total_time]
        return max(times) if times else None

    @property
    def recipe_count(self) -> int:
        """Computed property: count of non-discarded recipes."""
        return len(self.recipes)

    def update_properties(self, **kwargs) -> None:
        """Update multiple properties atomically through protected setters."""
        if not kwargs:
            return
        
        # Store original version for single increment
        original_version = self.version
        
        # Handle recipes separately if present (special processing)
        if "recipes" in kwargs:
            recipes_value = kwargs.pop("recipes")
            self._set_recipes(recipes_value)
        
        # Apply remaining property updates using protected setters
        for key, value in kwargs.items():
            setter_method_name = f"_set_{key}"
            if hasattr(self, setter_method_name):
                setter_method = getattr(self, setter_method_name)
                setter_method(value)
            else:
                raise AttributeError(f"Meal has no updatable property '{key}'")
        
        # Set version manually to avoid multiple increments
        self._version = original_version + 1

    def add_recipe(self, recipe: _ExampleDomainRecipe) -> None:
        """Add a recipe to the meal."""
        self._recipes.append(recipe)
        self._increment_version()
        # Invalidate cached properties
        if hasattr(self, '_cached_nutri_facts'):
            delattr(self, '_cached_nutri_facts')

    def remove_recipe(self, recipe_id: str) -> None:
        """Remove a recipe from the meal."""
        for recipe in self._recipes:
            if recipe.id == recipe_id:
                recipe._discard()  # Soft delete
                break
        self._increment_version()
        # Invalidate cached properties
        if hasattr(self, '_cached_nutri_facts'):
            delattr(self, '_cached_nutri_facts')


# =============================================================================
# FIELD TYPE DEFINITIONS
# =============================================================================

def validate_uuid_format(v: str) -> str:
    """Validate UUID format."""
    try:
        UUID(v, version=4)
        return v
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid UUID4 format: {str(e)}") from e

UUIDId = Annotated[
    str,
    Field(..., description="Unique identifier for the entity"),
]

RecipeName = Annotated[
    str,
    Field(..., min_length=1, max_length=255, description="Name of the recipe"),
]

MealName = Annotated[
    str,
    Field(..., min_length=1, max_length=255, description="Name of the meal"),
]

# =============================================================================
# API ENTITY EXAMPLES
# =============================================================================

class ApiExampleNutriFacts(BaseModel):
    """API representation of a nutri facts value object."""
    calories: float
    protein: float
    carbs: float
    fat: float

    @classmethod
    def from_domain(cls, domain_obj: ExampleNutriFacts) -> "ApiExampleNutriFacts":
        """Creates an instance from a domain model object."""
        return cls(
            calories=domain_obj.calories,
            protein=domain_obj.protein,
            carbs=domain_obj.carbs,
            fat=domain_obj.fat,
        )

    def to_domain(self) -> ExampleNutriFacts:
        """Converts the instance to a domain model object."""
        return ExampleNutriFacts(
            calories=self.calories,
            protein=self.protein,
            carbs=self.carbs,
            fat=self.fat,
        )
    
    @classmethod
    def from_orm_model(cls, orm_model: NutriFactsSaModel) -> "ApiExampleNutriFacts":
        """Convert from ORM model."""
        return cls.model_validate(orm_model)
    
    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs."""
        return {
            "calories": self.calories,
            "protein": self.protein,
            "carbs": self.carbs,
            "fat": self.fat,
        }




class ApiExampleTag(BaseModel):
    """API representation of a tag value object."""
    
    key: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1, max_length=200)
    author_id: UUIDId
    type: str = Field(..., min_length=1, max_length=50)

    @classmethod
    def from_domain(cls, domain_obj: Tag) -> "ApiExampleTag":
        """Creates an instance from a domain model object."""
        return cls(
            key=domain_obj.key,
            value=domain_obj.value,
            author_id=domain_obj.author_id,
            type=domain_obj.type,
        )

    def to_domain(self) -> Tag:
        """Converts the instance to a domain model object."""
        return Tag(
            key=self.key,
            value=self.value,
            author_id=self.author_id,
            type=self.type,
        )
    
    @classmethod
    def from_orm_model(cls, orm_model: TagSaModel) -> "ApiExampleTag":
        """Convert from ORM model."""
        return cls.model_validate(orm_model)
    
    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs."""
        return {
            "key": self.key,
            "value": self.value,
            "author_id": self.author_id,
            "type": self.type,
        }


class ApiExampleIngredient(BaseModel):
    """API representation of an ingredient value object."""
    
    name: str = Field(..., min_length=1, max_length=200)
    unit: ExampleMeasureUnit
    quantity: float = Field(..., gt=0)
    position: int = Field(..., ge=0)
    full_text: str | None = Field(None, max_length=500)
    product_id: UUIDId | None = None

    @classmethod
    def from_domain(cls, domain_obj: ExampleIngredient) -> "ApiExampleIngredient":
        """Creates an instance from a domain model object."""
        return cls(
            name=domain_obj.name,
            unit=domain_obj.unit,
            quantity=domain_obj.quantity,
            position=domain_obj.position,
            full_text=domain_obj.full_text,
            product_id=domain_obj.product_id,
        )

    def to_domain(self) -> ExampleIngredient:
        """Converts the instance to a domain model object."""
        return ExampleIngredient(
            name=self.name,
            # Api config converts enun to string
            unit=ExampleMeasureUnit(self.unit),
            quantity=self.quantity,
            position=self.position,
            full_text=self.full_text,
            product_id=self.product_id,
        )
    
    @classmethod
    def from_orm_model(cls, orm_model: IngredientSaModel) -> "ApiExampleIngredient":
        """Convert from ORM model."""
        return cls(
            name=orm_model.name,
            unit=ExampleMeasureUnit(orm_model.unit),
            quantity=orm_model.quantity,
            position=orm_model.position,
            full_text=orm_model.full_text,
            product_id=orm_model.product_id,
        )
    
    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs."""
        return {
            "name": self.name,
            "unit": self.unit,
            "quantity": self.quantity,
            "position": self.position,
            "full_text": self.full_text,
            "product_id": self.product_id,
        }

class ApiExampleDomainRecipe(BaseApiEntity[_ExampleDomainRecipe, RecipeSaModel]):
    """
    Example API entity for recipes following the actual codebase patterns.
    
    Demonstrates:
    - BaseApiEntity inheritance with proper generics
    - from_domain class method
    - custom_dump_json method for client responses
    - Proper type annotations and field definitions
    - Error handling in conversions
    """
    
    model_config = ConfigDict(
        # Inherit from BaseApiEntity configuration
        frozen=True,
        strict=True,
        extra='forbid',
        validate_assignment=True,
        from_attributes=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,
    )
    
    # Entity fields
    id: UUIDId = Field(..., description="Unique recipe identifier")
    name: RecipeName
    author_id: UUIDId
    meal_id: UUIDId
    ingredients: List[ApiExampleIngredient] = Field(default_factory=list)
    instructions: str = Field(..., min_length=10, max_length=5000)
    privacy: ExamplePrivacy = ExamplePrivacy.PRIVATE
    
    # Metadata fields
    created_at: datetime = Field(..., description="Recipe creation timestamp")
    updated_at: datetime = Field(..., description="Last modification timestamp")
    version: int = Field(..., ge=1, description="Entity version for optimistic locking")
    discarded: bool = Field(False, description="Soft delete flag")
    
    # Optional fields with defaults
    total_time: int | None = Field(None, ge=1, le=480, description="Total time in minutes")
    tags: FrozenSet[ApiExampleTag] = Field(default_factory=frozenset)
    nutri_facts: ApiExampleNutriFacts | None = Field(None, description="Nutritional facts")

    @classmethod
    def from_domain(cls, domain_obj: _ExampleDomainRecipe) -> "ApiExampleDomainRecipe":
        """
        Creates an instance from a domain model object.
        
        This method handles the conversion from domain entity to API representation,
        including nested value objects and collections.
        """
        return cls(
            id=domain_obj.id,
            name=domain_obj.name,
            author_id=domain_obj.author_id,
            meal_id=domain_obj.meal_id,
            ingredients=[ApiExampleIngredient.from_domain(ing) for ing in domain_obj.ingredients],
            instructions=domain_obj.instructions,
            privacy=domain_obj.privacy,
            created_at=domain_obj.created_at or datetime.now(),
            updated_at=domain_obj.updated_at or datetime.now(),
            version=domain_obj.version,
            discarded=domain_obj.discarded,
            total_time=domain_obj.total_time,
            tags=frozenset(ApiExampleTag.from_domain(tag) for tag in domain_obj.tags),
            nutri_facts=ApiExampleNutriFacts.from_domain(domain_obj.nutri_facts) if domain_obj.nutri_facts else None,
        )

    @classmethod
    def from_orm_model(cls, orm_model: RecipeSaModel) -> "ApiExampleDomainRecipe":
        """
        Creates an instance from an ORM model.
        
        Handles potential None values and mismatches between ORM and API models.
        """
        return cls(
            id=orm_model.id,
            name=orm_model.name,
            author_id=orm_model.author_id,
            meal_id=orm_model.meal_id,
            ingredients=[ApiExampleIngredient.from_orm_model(i) for i in orm_model.ingredients],
            instructions=orm_model.instructions,
            privacy=ExamplePrivacy(orm_model.privacy) if orm_model.privacy else ExamplePrivacy.PRIVATE,
            created_at=orm_model.created_at or datetime.now(),
            updated_at=orm_model.updated_at or datetime.now(),
            version=orm_model.version,
            discarded=orm_model.discarded,
            total_time=orm_model.total_time,
            tags=frozenset(ApiExampleTag.from_orm_model(t) for t in orm_model.tags),
            nutri_facts=ApiExampleNutriFacts(**asdict(orm_model.nutri_facts)) if orm_model.nutri_facts else None,
        )

    def to_domain(self) -> _ExampleDomainRecipe:
        """
        Converts the instance to a domain model object.
        
        Note: This is typically not needed for entities (unlike commands/queries)
        since entities usually flow FROM domain TO API, not the reverse.
        """
        return _ExampleDomainRecipe(
            id=self.id,
            name=self.name,
            author_id=self.author_id,
            meal_id=self.meal_id,
            ingredients=[ing.to_domain() for ing in self.ingredients],
            instructions=self.instructions,
            privacy=ExamplePrivacy(self.privacy) if self.privacy else ExamplePrivacy.PRIVATE,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            discarded=self.discarded,
            total_time=self.total_time,
            tags=set(tag.to_domain() for tag in self.tags),
            nutri_facts=self.nutri_facts.to_domain() if self.nutri_facts else None,
        )

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """
        Converts the instance to ORM model kwargs.
        
        This method prepares data for ORM model creation or updates.
        """
        return {
            "id": self.id,
            "name": self.name,
            "author_id": self.author_id,
            "meal_id": self.meal_id,
            "ingredients": [ing.to_orm_kwargs() for ing in self.ingredients],
            "instructions": self.instructions,
            "privacy": self.privacy,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "discarded": self.discarded,
            "total_time": self.total_time,
            "tags": [tag.to_orm_kwargs() for tag in self.tags],
            "nutri_facts": NutriFactsSaModel(**self.nutri_facts.to_orm_kwargs()) if self.nutri_facts else None,
        }

    def custom_dump_json(self, **kwargs) -> str:
        """
        Custom JSON serialization for client responses.
        
        This method provides optimized JSON output for API responses,
        excluding internal metadata and formatting fields appropriately.
        """
        # Define fields to exclude from client responses
        exclude_fields = {"version", "discarded"}
        
        # Use pydantic v2 model_dump_json for direct JSON serialization
        return self.model_dump_json(
            exclude=exclude_fields,
            by_alias=True,
            exclude_none=True,
            **kwargs
        )


class ApiExampleDomainMeal(BaseApiEntity[ExampleDomainMeal, MealSaModel]):
    """
    Example API entity for meals demonstrating aggregate root patterns.
    
    Demonstrates:
    - Aggregate root entity with child entities
    - Complex nested relationships
    - Batch operations and collection handling
    - Performance considerations for large collections
    """
    
    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra='forbid',
        validate_assignment=True,
        from_attributes=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,
    )
    
    # Entity fields
    id: UUIDId = Field(..., description="Unique meal identifier")
    name: MealName
    author_id: UUIDId
    menu_id: UUIDId | None = Field(None, description="Optional menu identifier")
    recipes: List[ApiExampleDomainRecipe] = Field(default_factory=list)
    tags: FrozenSet[ApiExampleTag] = Field(default_factory=frozenset)
    
    # Optional fields
    description: str | None = Field(None, max_length=1000)
    notes: str | None = Field(None, max_length=2000)
    image_url: str | None = Field(None, max_length=500)
    nutri_facts: ApiExampleNutriFacts | None = Field(None, description="Nutritional facts")
    
    # Metadata fields
    created_at: datetime = Field(..., description="Meal creation timestamp")
    updated_at: datetime = Field(..., description="Last modification timestamp")
    version: int = Field(..., ge=1, description="Entity version for optimistic locking")
    discarded: bool = Field(False, description="Soft delete flag")

    @classmethod
    def from_domain(cls, domain_obj: ExampleDomainMeal) -> "ApiExampleDomainMeal":
        """
        Creates an instance from a domain aggregate root.
        
        Handles conversion of the entire aggregate including all child entities.
        """
        return cls(
            id=domain_obj.id,
            name=domain_obj.name,
            author_id=domain_obj.author_id,
            menu_id=domain_obj.menu_id,
            recipes=[ApiExampleDomainRecipe.from_domain(recipe) for recipe in domain_obj.recipes],
            tags=frozenset(ApiExampleTag.from_domain(tag) for tag in domain_obj.tags),
            description=domain_obj.description,
            notes=domain_obj.notes,
            image_url=getattr(domain_obj, 'image_url', None),  # Handle missing attribute
            nutri_facts=ApiExampleNutriFacts.from_domain(domain_obj.nutri_facts) if domain_obj.nutri_facts else None,
            created_at=domain_obj.created_at or datetime.now(),
            updated_at=domain_obj.updated_at or datetime.now(),
            version=domain_obj.version,
            discarded=domain_obj.discarded,
        )

    @classmethod
    def from_orm_model(cls, orm_model: MealSaModel) -> "ApiExampleDomainMeal":
        """
        Creates an instance from an ORM model with eager loading.
        
        Assumes relationships are properly loaded to avoid N+1 queries.
        """
        return cls(
            id=orm_model.id,
            name=orm_model.name,
            author_id=orm_model.author_id,
            menu_id=orm_model.menu_id,
            recipes=[ApiExampleDomainRecipe.from_orm_model(r) for r in orm_model.recipes],
            tags=frozenset(ApiExampleTag.from_orm_model(t) for t in orm_model.tags),
            description=orm_model.description,
            notes=orm_model.notes,
            image_url=getattr(orm_model, 'image_url', None),  # Handle missing attribute
            nutri_facts=ApiExampleNutriFacts(**asdict(orm_model.nutri_facts)) if orm_model.nutri_facts else None,
            created_at=orm_model.created_at or datetime.now(),
            updated_at=orm_model.updated_at or datetime.now(),
            version=orm_model.version,
            discarded=orm_model.discarded,
        )

    def to_domain(self) -> ExampleDomainMeal:
        """
        Converts the instance to a domain aggregate root.
        
        Reconstructs the full aggregate with all child entities.
        """
        return ExampleDomainMeal(
            id=self.id,
            name=self.name,
            author_id=self.author_id,
            menu_id=self.menu_id,
            recipes=[recipe.to_domain() for recipe in self.recipes],
            tags=set(tag.to_domain() for tag in self.tags),
            description=self.description,
            notes=self.notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
            discarded=self.discarded,
        )

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """
        Converts the instance to ORM model kwargs.
        
        Handles nested relationships appropriately for ORM persistence.
        """
        return {
            "id": self.id,
            "name": self.name,
            "author_id": self.author_id,
            "menu_id": self.menu_id,
            "recipes": [recipe.to_orm_kwargs() for recipe in self.recipes],
            "tags": [tag.to_orm_kwargs() for tag in self.tags],
            "description": self.description,
            "notes": self.notes,
            "image_url": self.image_url,
            "nutri_facts": NutriFactsSaModel(**self.nutri_facts.to_orm_kwargs()) if self.nutri_facts else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "discarded": self.discarded,
        }

    def custom_dump_json(self, include_recipes: bool = True, **kwargs) -> str:
        """
        Custom JSON serialization with performance optimizations.
        
        Args:
            include_recipes: Whether to include full recipe details (performance option)
            **kwargs: Additional arguments for model_dump_json
        """
        # Define fields to exclude from client responses
        exclude_fields = {"version", "discarded"}
        
        # Performance optimization: optionally exclude recipes for list views
        if not include_recipes:
            exclude_fields.add("recipes")
        
        # Use pydantic v2 model_dump_json for direct JSON serialization
        return self.model_dump_json(
            exclude=exclude_fields,
            by_alias=True,
            exclude_none=True,
            **kwargs
        )

    def get_recipes_summary(self) -> List[Dict[str, Any]]:
        """
        Returns a lightweight summary of recipes for list views.
        
        This method provides a performance optimization for cases where
        full recipe details are not needed.
        """
        try:
            return [
                {
                    "id": recipe.id,
                    "name": recipe.name,
                    "ingredient_count": len(recipe.ingredients),
                    "privacy": recipe.privacy.value,
                    "total_time": recipe.total_time,
                }
                for recipe in self.recipes
            ]
        except Exception as e:
            raise ValueError(f"Failed to generate recipe summary: {e}") from e


# =============================================================================
# USAGE EXAMPLES AND PATTERNS
# =============================================================================

def example_recipe_entity_conversion():
    """
    Example: Converting between domain and API recipe entities.
    
    Demonstrates the full entity lifecycle and conversion patterns.
    """
    # Create sample domain entity
    domain_recipe = _ExampleDomainRecipe(
        id=str(uuid4()),
        name="Chicken Tikka Masala",
        author_id=str(uuid4()),
        meal_id=str(uuid4()),
        ingredients=[
            ExampleIngredient(
                name="chicken breast",
                unit=ExampleMeasureUnit.POUNDS,
                quantity=1.5,
                position=0,
                full_text="1.5 lbs chicken breast, cut into chunks",
                product_id=str(uuid4())
            ),
            ExampleIngredient(
                name="yogurt",
                unit=ExampleMeasureUnit.OUNCES,
                quantity=8,
                position=1,
                full_text="8 oz plain yogurt",
                product_id=str(uuid4())
            ),
        ],
        instructions="Marinate chicken in yogurt and spices, then cook in tomato sauce.",
        privacy=ExamplePrivacy.PUBLIC,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        version=1,
        discarded=False,
        total_time=45,
        tags=set([
            Tag(key="cuisine", value="indian", author_id=str(uuid4()), type="cuisine"),
            Tag(key="difficulty", value="medium", author_id=str(uuid4()), type="difficulty"),
        ]),
    )
    
    # Convert to API entity
    api_recipe = ApiExampleDomainRecipe.from_domain(domain_recipe)
    
    # Demonstrate JSON serialization
    json_output = api_recipe.custom_dump_json()
    
    # Convert back to domain (if needed)
    domain_recipe_back = api_recipe.to_domain()
    
    print(f"Original domain recipe: {domain_recipe.name}")
    print(f"API recipe ID: {api_recipe.id}")
    print(f"Ingredient count: {len(api_recipe.ingredients)}")
    print(f"JSON length: {len(json_output)} characters")
    print(f"Round-trip successful: {domain_recipe_back.name == domain_recipe.name}")
    
    return api_recipe


def example_meal_aggregate_conversion():
    """
    Example: Converting a complex meal aggregate with multiple recipes.
    
    Demonstrates aggregate root patterns and nested entity handling.
    """
    # Create sample recipes for the meal
    recipes = [
        _ExampleDomainRecipe(
            id=str(uuid4()),
            name="Chicken Tikka Masala",
            author_id=str(uuid4()),
            meal_id=str(uuid4()),
            ingredients=[
                ExampleIngredient(
                    name="chicken breast",
                    unit=ExampleMeasureUnit.POUNDS,
                    quantity=1.5,
                    position=0,
                    product_id=str(uuid4())
                ),
            ],
            instructions="Marinate and cook chicken in spiced tomato sauce.",
            privacy=ExamplePrivacy.PUBLIC,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=1,
        ),
        _ExampleDomainRecipe(
            id=str(uuid4()),
            name="Basmati Rice",
            author_id=str(uuid4()),
            meal_id=str(uuid4()),
            ingredients=[
                ExampleIngredient(
                    name="basmati rice",
                    unit=ExampleMeasureUnit.GRAMS,
                    quantity=200,
                    position=0,
                    product_id=str(uuid4())
                ),
            ],
            instructions="Rinse rice and cook with aromatic spices.",
            privacy=ExamplePrivacy.PUBLIC,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=1,
        ),
    ]
    
    # Create domain meal aggregate
    domain_meal = ExampleDomainMeal(
        id=str(uuid4()),
        name="Indian Dinner",
        author_id=str(uuid4()),
        menu_id=str(uuid4()),
        recipes=recipes,
        tags=set([
            Tag(key="cuisine", value="indian", author_id=str(uuid4()), type="cuisine"),
            Tag(key="meal_type", value="dinner", author_id=str(uuid4()), type="meal_type"),
        ]),
        description="A complete Indian dinner experience",
        notes="Serve with naan bread and mango lassi",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        version=1,
        discarded=False,
    )
    
    # Convert to API entity
    api_meal = ApiExampleDomainMeal.from_domain(domain_meal)
    
    # Demonstrate different JSON serialization options
    full_json = api_meal.custom_dump_json(include_recipes=True)
    summary_json = api_meal.custom_dump_json(include_recipes=False)
    
    # Get recipe summary
    recipe_summary = api_meal.get_recipes_summary()
    
    print(f"Meal: {api_meal.name}")
    print(f"Recipe count: {len(api_meal.recipes)}")
    print(f"Tag count: {len(api_meal.tags)}")
    print(f"Full JSON length: {len(full_json)} characters")
    print(f"Summary JSON length: {len(summary_json)} characters")
    print(f"Recipe summary: {recipe_summary}")
    
    return api_meal


def example_performance_considerations():
    """
    Example: Performance considerations for large entity collections.
    
    Demonstrates optimization strategies for entity serialization.
    """
    # Create a meal with many recipes (simulating a large aggregate)
    large_meal_recipes = []
    for i in range(20):  # 20 recipes
        ingredients = [
            ExampleIngredient(
                name=f"ingredient_{j}",
                unit=ExampleMeasureUnit.GRAMS,
                quantity=100.0,
                position=j,
                product_id=str(uuid4())
            )
            for j in range(5)  # 5 ingredients per recipe
        ]
        
        recipe = _ExampleDomainRecipe(
            id=str(uuid4()),
            name=f"Recipe {i+1}",
            author_id=str(uuid4()),
            meal_id=str(uuid4()),
            ingredients=ingredients,
            instructions=f"Instructions for recipe {i+1}",
            privacy=ExamplePrivacy.PUBLIC,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version=1,
        )
        large_meal_recipes.append(recipe)
    
    # Create large meal aggregate
    large_meal = ExampleDomainMeal(
        id=str(uuid4()),
        name="Large Meal Collection",
        author_id=str(uuid4()),
        menu_id=str(uuid4()),
        recipes=large_meal_recipes,
        tags=set([
            Tag(key="size", value="large", author_id=str(uuid4()), type="size"),
        ]),
        description="A meal with many recipes for testing performance",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        version=1,
    )
    
    # Convert to API entity
    api_large_meal = ApiExampleDomainMeal.from_domain(large_meal)
    
    # Measure serialization performance
    import time
    
    start_time = time.time()
    full_json = api_large_meal.custom_dump_json(include_recipes=True)
    full_time = time.time() - start_time
    
    start_time = time.time()
    summary_json = api_large_meal.custom_dump_json(include_recipes=False)
    summary_time = time.time() - start_time
    
    start_time = time.time()
    api_large_meal.get_recipes_summary()
    summary_method_time = time.time() - start_time
    
    print(f"Large meal with {len(api_large_meal.recipes)} recipes:")
    print(f"Full JSON serialization: {full_time:.4f}s ({len(full_json)} chars)")
    print(f"Summary JSON serialization: {summary_time:.4f}s ({len(summary_json)} chars)")
    print(f"Recipe summary method: {summary_method_time:.4f}s")
    print(f"Performance improvement: {full_time/summary_time:.2f}x faster")
    
    return api_large_meal


if __name__ == "__main__":
    """
    Run all examples to demonstrate entity patterns.
    """
    print("=== API Entity Examples ===\n")
    
    print("1. Recipe Entity Conversion:")
    example_recipe_entity_conversion()
    print()
    
    print("2. Meal Aggregate Conversion:")
    example_meal_aggregate_conversion()
    print()
    
    print("3. Performance Considerations:")
    example_performance_considerations()
    print()
    
    print("All entity examples completed!") 