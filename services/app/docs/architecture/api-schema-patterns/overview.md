# API Schema Patterns: Comprehensive Guide

## Table of Contents
- [Overview](#overview)
- [The Four-Layer Conversion Pattern](#the-four-layer-conversion-pattern)
- [When to Use Each Layer](#when-to-use-each-layer)
- [Pattern Decision Flowchart](#pattern-decision-flowchart)
- [Type Conversion Strategies](#type-conversion-strategies)
- [Performance Considerations](#performance-considerations)
- [Best Practices](#best-practices)
- [Common Anti-Patterns](#common-anti-patterns)
- [Examples and Walkthroughs](#examples-and-walkthroughs)

## Overview

This documentation provides comprehensive guidance for implementing API schemas in the menu planning application. Our API schema patterns follow a **Test-Driven Documentation (TDD-D)** approach where all examples are validated by automated tests to ensure accuracy and production readiness.

### Core Principles

1. **Four-Layer Conversion Pattern**: Clean separation between API, Domain, and ORM layers
2. **Type Safety**: Leveraging Pydantic v2 for robust validation and type conversion
3. **Performance First**: TypeAdapter patterns optimized for production workloads
4. **General-Purpose Solutions**: All patterns work correctly for all valid inputs, not just test cases

### Key Design Goals

- **AI Agent Success Rate**: 90% of AI agents can implement new schemas without clarification
- **Performance Standards**: TypeAdapter validation <3ms for 10 items from JSON
- **Maintainability**: Clear patterns that scale across 90+ schema files
- **Security**: Input sanitization and validation at every layer

## The Four-Layer Conversion Pattern

The four-layer conversion pattern provides clean separation of concerns across our application architecture:

```
┌─────────────────┐    to_domain()     ┌─────────────────┐
│   Client JSON   │ ──────────────────► │  Domain Object  │
│   (API Request) │                     │ (Business Logic)│
└─────────────────┘                     └─────────────────┘
         ▲                                         │
         │ from_domain()                           │ 
         │                                         ▼
┌─────────────────┐                     ┌─────────────────┐
│   API Schema    │                     │   Domain Layer  │
│  (Serialized)   │                     │   (Pure Logic)  │
└─────────────────┘                     └─────────────────┘
         ▲                                         │
         │ from_orm_model()                        │ to_orm_model()
         │                                         ▼
┌─────────────────┐    to_orm_kwargs() ┌─────────────────┐
│  SQLAlchemy     │ ◄──────────────────│   Domain Object │
│   ORM Model     │                     │    (for ORM)    │
└─────────────────┘                     └─────────────────┘
```

### Layer Responsibilities

#### 1. `to_domain()` - API Request → Domain Object
**Purpose**: Convert incoming API request data to domain objects for business logic  
**Usage**: Command/Query creation from client input  
**Validation**: Apply business rules and domain constraints

```python
def to_domain(self) -> Meal:
    """Convert API meal to domain meal with business validation."""
    recipes = [recipe.to_domain() for recipe in self.recipes]
    tags = {tag.to_domain() for tag in self.tags}
    
    # Business rule: meal must have at least one recipe
    if not recipes:
        raise ValidationError("Meal must contain at least one recipe")
        
    return Meal(
        id=self.id,
        name=self.name.strip(),  # Domain business rule: normalize names
        recipes=recipes,
        tags=tags
    )
```

#### 2. `from_domain()` - Domain Object → API Response
**Purpose**: Convert domain objects to API response format  
**Usage**: Query responses, command results  
**Processing**: Materialize computed properties, apply view logic

```python
@classmethod
def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
    """Convert domain meal to API representation with materialized computed values."""
    return cls(
        id=domain_obj.id,
        name=domain_obj.name,
        recipes=frozenset(ApiRecipe.from_domain(r) for r in domain_obj.recipes),
        tags=frozenset(ApiTag.from_domain(t) for t in domain_obj.tags),
        # Materialize computed property
        nutri_facts=domain_obj.nutri_facts,  # @cached_property becomes regular field
        created_at=domain_obj.created_at,
        updated_at=domain_obj.updated_at
    )
```

#### 3. `from_orm_model()` - ORM Model → API Schema
**Purpose**: Convert SQLAlchemy models to API schemas  
**Usage**: Database query results to API responses  
**Handling**: Convert ORM relationships and composite types

```python
@classmethod
def from_orm_model(cls, orm_model: MealSaModel) -> "ApiMeal":
    """Convert SQLAlchemy model to API schema."""
    return cls(
        id=orm_model.id,
        name=orm_model.name,
        # Convert ORM relationships to frozensets
        recipes=frozenset(
            ApiRecipe.from_orm_model(recipe) 
            for recipe in orm_model.recipes
        ),
        tags=frozenset(
            ApiTag.from_orm_model(tag) 
            for tag in orm_model.tags
        ),
        # Handle composite types
        nutri_facts=MealNutriFacts.from_orm_composite(orm_model.nutri_facts) 
                   if orm_model.nutri_facts else None,
        created_at=orm_model.created_at,
        updated_at=orm_model.updated_at
    )
```

#### 4. `to_orm_kwargs()` - API Schema → ORM Creation Data
**Purpose**: Convert API schemas to ORM model creation parameters  
**Usage**: Persisting new entities to database  
**Transformation**: Handle relationship IDs and composite field flattening

```python
def to_orm_kwargs(self) -> dict[str, Any]:
    """Convert API schema to ORM model creation arguments."""
    kwargs = {
        "id": self.id,
        "name": self.name,
        "created_at": self.created_at,
        "updated_at": self.updated_at
    }
    
    # Handle composite fields - flatten for SQLAlchemy composite()
    if self.nutri_facts:
        kwargs.update(self.nutri_facts.to_orm_composite_kwargs())
    
    # Note: Relationships handled separately by repository layer
    # to manage foreign key constraints and transaction boundaries
    
    return kwargs
```

## When to Use Each Layer

### Decision Matrix

| Scenario | Method | Rationale |
|----------|--------|-----------|
| **API Request → Business Logic** | `to_domain()` | Apply business validation, create domain objects for use cases |
| **Business Logic → API Response** | `from_domain()` | Materialize computed properties, apply view transformations |
| **Database Query → API Response** | `from_orm_model()` | Direct conversion without business logic, handle ORM specifics |
| **API Request → Database Insert** | `to_orm_kwargs()` | Prepare data for persistence, handle composite fields |

### Performance Considerations

```python
# ❌ ANTI-PATTERN: Unnecessary conversions
def get_meal_api_response(meal_id: str) -> ApiMeal:
    orm_model = repository.get_meal(meal_id)
    domain_obj = orm_model.to_domain()  # Unnecessary step
    return ApiMeal.from_domain(domain_obj)

# ✅ CORRECT: Direct conversion
def get_meal_api_response(meal_id: str) -> ApiMeal:
    orm_model = repository.get_meal(meal_id)
    return ApiMeal.from_orm_model(orm_model)  # Direct, efficient
```

## Pattern Decision Flowchart

```
Start: Do I need to convert between layers?
│
├─ YES: What's the source and destination?
│  │
│  ├─ Client JSON → Business Logic
│  │  └─ Use: to_domain()
│  │     • Apply business validation
│  │     • Create domain objects
│  │     • Handle business rules
│  │
│  ├─ Business Logic → Client JSON
│  │  └─ Use: from_domain()
│  │     • Materialize computed properties
│  │     • Apply view transformations
│  │     • Format for API response
│  │
│  ├─ Database → Client JSON
│  │  └─ Use: from_orm_model()
│  │     • Direct ORM to API conversion
│  │     • Handle relationships
│  │     • Convert composite types
│  │
│  └─ Client JSON → Database
│     └─ Use: to_orm_kwargs()
│        • Prepare for persistence
│        • Flatten composite fields
│        • Generate creation parameters
│
└─ NO: Use TypeAdapter for validation only
   └─ RecipeListAdapter.validate_json(data)
```

## Type Conversion Strategies

### Collection Type Transformations

Our schemas use specific collection types at each layer for different purposes:

| Domain Type | API Type | ORM Type | Rationale |
|-------------|----------|----------|-----------|
| `set[Tag]` | `frozenset[ApiTag]` | `list[TagSaModel]` | Domain: uniqueness, API: immutability, ORM: relational order |
| `list[Recipe]` | `frozenset[ApiRecipe]` | `list[RecipeSaModel]` | Domain: ordered, API: immutable set, ORM: foreign key list |
| `Optional[NutriFacts]` | `Optional[MealNutriFacts]` | `NutriFactsSaModel` | Domain: computed, API: materialized, ORM: composite |

### Type Conversion Examples

```python
# Domain → API: Set to Frozenset
domain_tags: set[Tag] = {Tag(name="italian"), Tag(name="quick")}
api_tags: frozenset[ApiTag] = frozenset(
    ApiTag.from_domain(tag) for tag in domain_tags
)

# API → ORM: Frozenset to List (for relationships)
api_recipes: frozenset[ApiRecipe] = frozenset([...])
orm_recipe_ids: list[str] = [recipe.id for recipe in api_recipes]

# Computed Property Materialization
class Meal:  # Domain
    @cached_property
    def nutri_facts(self) -> NutriFacts | None:
        """Computed at runtime from recipes"""
        return self._compute_nutritional_facts()

class ApiMeal:  # API
    nutri_facts: MealNutriFacts | None  # Materialized value
    
    @classmethod
    def from_domain(cls, meal: Meal) -> "ApiMeal":
        return cls(
            # ... other fields ...
            nutri_facts=meal.nutri_facts,  # Triggers computation once
        )
```

### Validation Strategy

```python
# Field-level validation with BeforeValidator
MealName = Annotated[
    str,
    BeforeValidator(validate_optional_text),  # Trim whitespace, handle empty
    Field(..., min_length=1, max_length=255)
]

# Business logic validation with field_validator
@field_validator('tags')
@classmethod
def validate_tags_unique(cls, v: frozenset[ApiTag]) -> frozenset[ApiTag]:
    """Ensure no duplicate tags by name."""
    tag_names = [tag.name for tag in v]
    if len(tag_names) != len(set(tag_names)):
        raise ValueError("Duplicate tag names are not allowed")
    return v

# Type conversion with AfterValidator
PercentageFloat = Annotated[
    float,
    AfterValidator(lambda x: max(0.0, min(100.0, x))),  # Clamp to 0-100
    Field(..., ge=0.0, le=100.0)
]
```

## Performance Considerations

### TypeAdapter Singleton Pattern

```python
# ✅ CORRECT: Module-level singleton (recommended)
RecipeListAdapter = TypeAdapter(list[ApiRecipe])
TagFrozensetAdapter = TypeAdapter(frozenset[ApiTag])

def validate_recipes(recipes_data: list[dict]) -> list[ApiRecipe]:
    return RecipeListAdapter.validate_python(recipes_data)

# ❌ ANTI-PATTERN: Creating adapters in functions
def validate_recipes(recipes_data: list[dict]) -> list[ApiRecipe]:
    adapter = TypeAdapter(list[ApiRecipe])  # Creates new adapter each call
    return adapter.validate_python(recipes_data)
```

### Performance Benchmarks

Based on our performance baseline tests:

- **RecipeListAdapter (10 items)**: < 3ms validation from JSON
- **Memory growth**: < 5MB for repeated validations
- **Singleton benefit**: 2-10x faster than recreation pattern
- **Thread safety**: Concurrent access validated up to 20 threads

### Memory Usage Patterns

```python
# Efficient pattern for large collections
def process_large_recipe_list(recipe_data: list[dict]) -> list[ApiRecipe]:
    # Single validation call, not per-item validation
    return RecipeListAdapter.validate_python(recipe_data)

# Instead of:
def process_large_recipe_list_inefficient(recipe_data: list[dict]) -> list[ApiRecipe]:
    results = []
    for item in recipe_data:
        # Creates validation overhead per item
        recipe = ApiRecipe.model_validate(item)
        results.append(recipe)
    return results
```

## Best Practices

### 1. Always Use the Correct Conversion Method

```python
# ✅ CORRECT: Route-specific conversion
@router.post("/meals", response_model=ApiMeal)
async def create_meal(meal_data: ApiMeal) -> ApiMeal:
    # API → Domain for business logic
    domain_meal = meal_data.to_domain()
    
    # Business logic
    created_meal = meal_service.create_meal(domain_meal)
    
    # Domain → API for response
    return ApiMeal.from_domain(created_meal)

@router.get("/meals/{meal_id}", response_model=ApiMeal)
async def get_meal(meal_id: str) -> ApiMeal:
    # Database → API (skip domain layer for simple queries)
    orm_meal = repository.get_meal(meal_id)
    return ApiMeal.from_orm_model(orm_meal)
```

### 2. Handle Computed Properties Correctly

```python
# Domain: Lazy computation
class Meal:
    @cached_property
    def nutri_facts(self) -> NutriFacts | None:
        """Computed from recipes - expensive operation."""
        if not self.recipes:
            return None
        return sum(recipe.nutri_facts for recipe in self.recipes if recipe.nutri_facts)

# API: Materialized value
class ApiMeal(BaseApiModel[Meal, MealSaModel]):
    nutri_facts: MealNutriFacts | None  # Regular field, not computed
    
    @classmethod
    def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
        return cls(
            # ... other fields ...
            nutri_facts=domain_obj.nutri_facts,  # Triggers computation once
        )
```

### 3. Proper Error Handling

```python
def to_domain(self) -> Meal:
    """Convert with comprehensive error handling."""
    try:
        recipes = [recipe.to_domain() for recipe in self.recipes]
    except ValidationError as e:
        raise ValueError(f"Invalid recipe data in meal: {e}")
    
    # Business validation
    if not recipes:
        raise ValueError("Meal must contain at least one recipe")
    
    if len(recipes) > 50:  # Business rule
        raise ValueError("Meal cannot contain more than 50 recipes")
    
    return Meal(
        id=self.id,
        name=self.name.strip(),
        recipes=recipes,
        tags={tag.to_domain() for tag in self.tags}
    )
```

## Common Anti-Patterns

### ❌ Anti-Pattern 1: Skipping Validation Layers

```python
# BAD: Direct dict to domain conversion
def create_meal_bad(meal_dict: dict) -> Meal:
    return Meal(**meal_dict)  # No validation, type conversion, or error handling

# GOOD: Proper layered validation
def create_meal_good(meal_dict: dict) -> Meal:
    api_meal = ApiMeal.model_validate(meal_dict)  # Pydantic validation
    return api_meal.to_domain()  # Business validation
```

### ❌ Anti-Pattern 2: Inefficient TypeAdapter Usage

```python
# BAD: Recreation pattern
def validate_multiple_collections(data):
    for collection in data:
        adapter = TypeAdapter(list[ApiRecipe])  # Creates new adapter each time
        result = adapter.validate_python(collection)

# GOOD: Singleton pattern
RecipeListAdapter = TypeAdapter(list[ApiRecipe])  # Module level

def validate_multiple_collections(data):
    for collection in data:
        result = RecipeListAdapter.validate_python(collection)  # Reuse
```

### ❌ Anti-Pattern 3: Inconsistent Type Usage

```python
# BAD: Inconsistent collection types
class ApiMeal:
    recipes: list[ApiRecipe]     # Mutable, ordered
    tags: set[ApiTag]           # Mutable, unordered
    ingredients: tuple[ApiIngredient]  # Immutable, ordered

# GOOD: Consistent API layer patterns
class ApiMeal:
    recipes: frozenset[ApiRecipe]     # Immutable, unordered (consistent)
    tags: frozenset[ApiTag]          # Immutable, unordered (consistent)
    ingredients: frozenset[ApiIngredient]  # Immutable, unordered (consistent)
```

## Examples and Walkthroughs

### Complete Implementation Example

See our detailed walkthrough: [ApiMeal Complete Implementation](examples/meal-schema-complete.md)

### Pattern-Specific Guides

- [Type Conversion Strategies](patterns/type-conversions.md)
- [Computed Properties Handling](patterns/computed-properties.md)
- [TypeAdapter Best Practices](patterns/typeadapter-usage.md)
- [Field Validation Patterns](patterns/field-validation.md)

### Testing Your Implementation

All patterns in this documentation are validated by our test suite:

```bash
# Run pattern validation tests
poetry run python -m pytest tests/documentation/api_patterns/test_pattern_validation.py

# Run performance regression tests
poetry run python -m pytest tests/documentation/api_patterns/test_performance_regression.py

# Run complete four-layer conversion tests
poetry run python -m pytest tests/documentation/api_patterns/test_meal_four_layer_conversion.py
```

---

**Next Steps**: Review the detailed implementation examples and begin applying these patterns to your schema implementations. All examples in this documentation are tested and production-ready. 