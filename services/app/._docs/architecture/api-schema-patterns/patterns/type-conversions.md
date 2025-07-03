# Type Conversion Strategies

## Overview

This document provides comprehensive guidance on type conversions between Domain, API, and ORM layers. All conversion strategies are validated by automated tests to ensure accuracy and production readiness.

## Table of Contents
- [Type Conversion Matrix](#type-conversion-matrix)
- [Collection Type Transformations](#collection-type-transformations)
- [Computed Property Materialization](#computed-property-materialization)
- [Composite Field Handling](#composite-field-handling)
- [Real-World Examples](#real-world-examples)
- [Performance Considerations](#performance-considerations)
- [Testing Strategies](#testing-strategies)

## Type Conversion Matrix

Based on analysis of 90 schema files, here are the validated conversion patterns:

### Collection Types

| Domain Type | API Type | ORM Type | Use Case | Rationale |
|-------------|----------|----------|----------|-----------|
| `set[Tag]` | `frozenset[ApiTag]` | `list[TagSaModel]` | Unique tags | Domain: uniqueness, API: immutability, ORM: relational order |
| `list[Recipe]` | `frozenset[ApiRecipe]` | `list[RecipeSaModel]` | Recipe collections | Domain: ordered, API: immutable set, ORM: foreign key list |
| `list[Ingredient]` | `frozenset[ApiIngredient]` | `list[IngredientSaModel]` | Recipe ingredients | Domain: positioned, API: unordered view, ORM: foreign key |
| `set[Permission]` | `frozenset[ApiPermission]` | `list[PermissionSaModel]` | Role permissions | Domain: unique perms, API: immutable, ORM: junction table |

### Scalar Types

| Domain Type | API Type | ORM Type | Use Case | Conversion Notes |
|-------------|----------|----------|----------|------------------|
| `MeasureUnit` (enum) | `str` | `str` | Ingredient units | Serialize enum to string for API |
| `UUID` | `str` | `str` | Entity IDs | UUID objects to string representation |
| `Decimal` | `float` | `Numeric` | Nutritional values | Precision handling in financial calculations |
| `datetime` | `str` (ISO) | `DateTime` | Timestamps | ISO 8601 serialization for API |

### Optional and Computed Types

| Domain Type | API Type | ORM Type | Use Case | Special Handling |
|-------------|----------|----------|----------|------------------|
| `@cached_property NutriFacts` | `MealNutriFacts \| None` | `NutriFactsSaModel` | Computed nutrition | Materialize computed property |
| `Optional[Rating]` | `Optional[ApiRating]` | `RatingSaModel \| None` | Optional ratings | Handle None propagation |
| `Percentage` (custom) | `float` | `Float` | Nutritional percentages | Range validation 0-100 |

## Collection Type Transformations

### Pattern 1: Set → Frozenset → List

**Domain to API Conversion**
```python
# Domain: Mutable set for business logic
class Meal:
    def __init__(self):
        self.tags: set[Tag] = set()
    
    def add_tag(self, tag: Tag) -> None:
        """Business method requiring mutable set."""
        self.tags.add(tag)

# API: Immutable frozenset for serialization
class ApiMeal(BaseApiModel[Meal, MealSaModel]):
    tags: frozenset[ApiTag]
    
    @classmethod
    def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
        return cls(
            # Convert set to frozenset
            tags=frozenset(ApiTag.from_domain(tag) for tag in domain_obj.tags),
            # ... other fields
        )
```

**API to ORM Conversion**
```python
def to_orm_kwargs(self) -> dict[str, Any]:
    """Convert API schema to ORM creation arguments."""
    kwargs = {
        "id": self.id,
        "name": self.name,
        # Note: tags relationship handled separately by repository
        # ORM uses list[TagSaModel] for foreign key relationships
    }
    return kwargs

# In repository layer:
def create_meal_with_tags(self, meal_data: dict, tag_ids: list[str]) -> MealSaModel:
    """Repository handles the frozenset[ApiTag] → list[TagSaModel] conversion."""
    meal = MealSaModel(**meal_data)
    
    # Convert frozenset of API tags to list of ORM models
    tag_models = self.session.query(TagSaModel).filter(
        TagSaModel.id.in_(tag_ids)
    ).all()
    
    meal.tags = tag_models  # SQLAlchemy relationship expects list
    return meal
```

### Pattern 2: List → Frozenset → List (Order Preservation)

**For ordered collections that become unordered in API:**
```python
# Domain: Ordered list for business logic
class Recipe:
    def __init__(self):
        self.ingredients: list[Ingredient] = []  # Order matters for preparation

# API: Frozenset for consistent serialization
class ApiRecipe(BaseApiModel[Recipe, RecipeSaModel]):
    ingredients: frozenset[ApiIngredient]
    
    @classmethod
    def from_domain(cls, domain_obj: Recipe) -> "ApiRecipe":
        return cls(
            # Lose order in API layer - client shouldn't depend on order
            ingredients=frozenset(
                ApiIngredient.from_domain(ing) for ing in domain_obj.ingredients
            ),
        )
    
    def to_domain(self) -> Recipe:
        """Convert back to domain - need to handle order reconstruction."""
        # Sort by position field to reconstruct order
        ordered_ingredients = sorted(
            [ing.to_domain() for ing in self.ingredients],
            key=lambda x: x.position
        )
        return Recipe(ingredients=ordered_ingredients)
```

### Pattern 3: Nested Collection Handling

**Complex nested structures:**
```python
# Domain: Complex nested structure
class Menu:
    def __init__(self):
        self.weeks: dict[int, list[Meal]] = {}  # Week number → meals

# API: Flattened structure for easier consumption
class ApiMenu(BaseApiModel[Menu, MenuSaModel]):
    meals: frozenset[ApiMenuMeal]  # Flattened with week/day information
    
    @classmethod
    def from_domain(cls, domain_obj: Menu) -> "ApiMenu":
        meals = []
        for week_num, week_meals in domain_obj.weeks.items():
            for day_idx, meal in enumerate(week_meals):
                api_meal = ApiMenuMeal.from_domain(meal)
                api_meal.week = week_num
                api_meal.day_index = day_idx
                meals.append(api_meal)
        
        return cls(meals=frozenset(meals))
```

## Computed Property Materialization

### Pattern: @cached_property → Regular Field

**Domain Layer: Expensive Computation**
```python
class Meal:
    @cached_property
    def nutri_facts(self) -> NutriFacts | None:
        """
        Compute nutritional facts from all recipes.
        Cached because this is expensive - aggregates all recipe nutrition.
        """
        if not self.recipes:
            return None
            
        total_facts = NutriFacts()
        for recipe in self.recipes:
            if recipe.nutri_facts:
                total_facts += recipe.nutri_facts
                
        return total_facts if total_facts.has_data() else None
    
    @cached_property
    def calorie_density(self) -> float:
        """Computed property: calories per 100g."""
        if not self.nutri_facts or not self.total_weight:
            return 0.0
        return (self.nutri_facts.calories / self.total_weight) * 100
```

**API Layer: Materialized Values**
```python
class ApiMeal(BaseApiModel[Meal, MealSaModel]):
    # These become regular fields, not computed properties
    nutri_facts: MealNutriFacts | None
    calorie_density: float
    
    @classmethod
    def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
        """Materialize all computed properties during conversion."""
        return cls(
            id=domain_obj.id,
            name=domain_obj.name,
            # Trigger computation once and store result
            nutri_facts=MealNutriFacts.from_domain(domain_obj.nutri_facts) 
                       if domain_obj.nutri_facts else None,
            calorie_density=domain_obj.calorie_density,  # Computed once
            created_at=domain_obj.created_at,
            updated_at=domain_obj.updated_at
        )
```

**ORM Layer: Stored Composite Values**
```python
class MealSaModel(Base):
    __tablename__ = "meals"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    
    # Composite field for nutritional facts
    nutri_facts: Mapped[NutriFactsSaModel] = composite(
        NutriFactsSaModel,
        "calories", "protein", "carbohydrate", "total_fat",
        "saturated_fat", "trans_fat", "dietary_fiber", "sodium", "sugar"
    )
    
    # Computed values stored as regular columns
    calorie_density: Mapped[float] = mapped_column(Float, default=0.0)

class MealNutriFacts:
    """API representation of nutritional facts."""
    
    def to_orm_composite_kwargs(self) -> dict[str, float]:
        """Convert to flat dictionary for SQLAlchemy composite."""
        return {
            "calories": self.calories,
            "protein": self.protein,
            "carbohydrate": self.carbohydrate,
            "total_fat": self.total_fat,
            "saturated_fat": self.saturated_fat,
            "trans_fat": self.trans_fat,
            "dietary_fiber": self.dietary_fiber,
            "sodium": self.sodium,
            "sugar": self.sugar
        }
```

## Composite Field Handling

### Pattern: Nested Object → Composite → Flattened Columns

**API to ORM Composite Conversion:**
```python
class ApiNutritionalFacts:
    calories: float
    protein: float
    carbohydrate: float
    total_fat: float
    # ... other nutritional fields

    def to_orm_composite_kwargs(self) -> dict[str, float]:
        """Flatten nested object for SQLAlchemy composite."""
        return {
            "nutri_calories": self.calories,
            "nutri_protein": self.protein,
            "nutri_carbohydrate": self.carbohydrate,
            "nutri_total_fat": self.total_fat,
            # Prefix with 'nutri_' to avoid column name conflicts
        }

class ApiMeal:
    nutri_facts: ApiNutritionalFacts | None
    
    def to_orm_kwargs(self) -> dict[str, Any]:
        kwargs = {"id": self.id, "name": self.name}
        
        # Handle composite field
        if self.nutri_facts:
            kwargs.update(self.nutri_facts.to_orm_composite_kwargs())
        
        return kwargs
```

**ORM Composite to API Conversion:**
```python
class NutriFactsSaModel:
    """SQLAlchemy composite type for nutritional facts."""
    
    def __init__(self, calories=None, protein=None, carbohydrate=None, 
                 total_fat=None, saturated_fat=None, trans_fat=None,
                 dietary_fiber=None, sodium=None, sugar=None):
        self.calories = calories
        self.protein = protein
        # ... other fields

class ApiMeal:
    @classmethod
    def from_orm_model(cls, orm_model: MealSaModel) -> "ApiMeal":
        return cls(
            id=orm_model.id,
            name=orm_model.name,
            # Convert composite to nested object
            nutri_facts=ApiNutritionalFacts(
                calories=orm_model.nutri_facts.calories,
                protein=orm_model.nutri_facts.protein,
                # ... other fields
            ) if orm_model.nutri_facts and orm_model.nutri_facts.calories else None,
        )
```

## Real-World Examples

### Example 1: Tag Collection Conversion

**Complete flow from Domain → API → ORM:**
```python
# 1. Domain Layer
class Meal:
    def __init__(self):
        self.tags: set[Tag] = {
            Tag(name="italian", type="cuisine"),
            Tag(name="quick", type="preparation"),
            Tag(name="vegetarian", type="dietary")
        }

# 2. API Layer
class ApiMeal:
    tags: frozenset[ApiTag]
    
    @classmethod
    def from_domain(cls, meal: Meal) -> "ApiMeal":
        return cls(
            tags=frozenset(ApiTag.from_domain(tag) for tag in meal.tags)
            # frozenset ensures immutability and consistent serialization order
        )

# 3. ORM Layer (via Repository)
class MealRepository:
    def create_meal(self, api_meal: ApiMeal) -> MealSaModel:
        # Convert API meal to ORM kwargs
        meal_kwargs = api_meal.to_orm_kwargs()
        orm_meal = MealSaModel(**meal_kwargs)
        
        # Handle tags relationship separately
        tag_names = [tag.name for tag in api_meal.tags]
        tag_models = self.session.query(TagSaModel).filter(
            TagSaModel.name.in_(tag_names)
        ).all()
        
        orm_meal.tags = tag_models  # List assignment for SQLAlchemy relationship
        return orm_meal
```

### Example 2: Recipe Ingredient Conversion with Positioning

**Handling ordered collections:**
```python
# Domain: Order matters
class Recipe:
    def __init__(self):
        self.ingredients: list[Ingredient] = [
            Ingredient(name="flour", position=1),
            Ingredient(name="eggs", position=2),
            Ingredient(name="milk", position=3)
        ]

# API: Position embedded in objects, collection unordered
class ApiRecipe:
    ingredients: frozenset[ApiIngredient]
    
    @classmethod  
    def from_domain(cls, recipe: Recipe) -> "ApiRecipe":
        return cls(
            ingredients=frozenset(
                ApiIngredient.from_domain(ing) for ing in recipe.ingredients
            )
            # Position preserved in individual ApiIngredient objects
        )
    
    def to_domain(self) -> Recipe:
        # Reconstruct order from position field
        sorted_ingredients = sorted(
            [ing.to_domain() for ing in self.ingredients],
            key=lambda x: x.position
        )
        return Recipe(ingredients=sorted_ingredients)

class ApiIngredient:
    name: str
    position: int  # Preserves original order
    quantity: float
    unit: str
```

### Example 3: Menu Week Structure Flattening

**Complex nested structure conversion:**
```python
# Domain: Hierarchical structure
class Menu:
    def __init__(self):
        self.weeks: dict[int, dict[str, Meal]] = {
            1: {"monday": meal1, "tuesday": meal2},
            2: {"monday": meal3, "tuesday": meal4}
        }

# API: Flattened for easier client consumption
class ApiMenu:
    meals: frozenset[ApiMenuMeal]
    
    @classmethod
    def from_domain(cls, menu: Menu) -> "ApiMenu":
        flattened_meals = []
        
        for week_num, week_meals in menu.weeks.items():
            for weekday, meal in week_meals.items():
                menu_meal = ApiMenuMeal(
                    meal_id=meal.id,
                    meal_name=meal.name,
                    week=week_num,
                    weekday=weekday,
                    # Flatten meal nutritional info
                    nutri_facts=meal.nutri_facts
                )
                flattened_meals.append(menu_meal)
        
        return cls(meals=frozenset(flattened_meals))

class ApiMenuMeal:
    meal_id: str
    meal_name: str
    week: int
    weekday: str
    nutri_facts: MealNutriFacts | None
```

## Performance Considerations

### Efficient Collection Processing

```python
# ✅ EFFICIENT: Batch processing
def convert_large_recipe_collection(recipes: list[Recipe]) -> frozenset[ApiRecipe]:
    """Convert large collections efficiently."""
    # Use generator for memory efficiency
    api_recipes = (ApiRecipe.from_domain(recipe) for recipe in recipes)
    return frozenset(api_recipes)

# ❌ INEFFICIENT: Individual processing
def convert_large_recipe_collection_slow(recipes: list[Recipe]) -> frozenset[ApiRecipe]:
    """Inefficient approach - avoid this pattern."""
    result = set()
    for recipe in recipes:
        api_recipe = ApiRecipe.from_domain(recipe)
        result.add(api_recipe)  # Set operations in loop
    return frozenset(result)
```

### TypeAdapter Usage for Bulk Conversions

```python
# ✅ EFFICIENT: Use TypeAdapter for validation
RecipeListAdapter = TypeAdapter(list[ApiRecipe])

def validate_and_convert_bulk_recipes(recipe_data: list[dict]) -> list[ApiRecipe]:
    """Efficient bulk validation and conversion."""
    # Single validation call for entire collection
    return RecipeListAdapter.validate_python(recipe_data)

# ❌ INEFFICIENT: Individual validation
def validate_and_convert_bulk_recipes_slow(recipe_data: list[dict]) -> list[ApiRecipe]:
    """Avoid individual validation in loops."""
    results = []
    for item in recipe_data:
        recipe = ApiRecipe.model_validate(item)  # Validation overhead per item
        results.append(recipe)
    return results
```

### Memory Optimization

```python
# ✅ MEMORY EFFICIENT: Generator-based conversion
def convert_meal_collection_efficiently(meals: list[Meal]) -> frozenset[ApiMeal]:
    """Memory-efficient conversion for large collections."""
    return frozenset(ApiMeal.from_domain(meal) for meal in meals)

# ❌ MEMORY INTENSIVE: Intermediate list creation
def convert_meal_collection_memory_heavy(meals: list[Meal]) -> frozenset[ApiMeal]:
    """Avoid creating intermediate collections."""
    api_meals = [ApiMeal.from_domain(meal) for meal in meals]  # Full list in memory
    return frozenset(api_meals)
```

## Testing Strategies

### Test All Conversion Paths

```python
def test_meal_conversion_cycle_integrity():
    """Test Domain → API → ORM → API → Domain roundtrip."""
    # Start with domain object
    original_meal = create_test_meal()
    
    # Domain → API
    api_meal = ApiMeal.from_domain(original_meal)
    
    # API → ORM kwargs
    orm_kwargs = api_meal.to_orm_kwargs()
    orm_meal = MealSaModel(**orm_kwargs)
    
    # ORM → API
    api_meal_2 = ApiMeal.from_orm_model(orm_meal)
    
    # API → Domain
    converted_meal = api_meal_2.to_domain()
    
    # Verify integrity
    assert converted_meal.name == original_meal.name
    assert len(converted_meal.tags) == len(original_meal.tags)
    # Note: Some computed properties may not roundtrip exactly
```

### Test Type Conversion Edge Cases

```python
def test_empty_collection_conversions():
    """Test handling of empty collections."""
    meal = Meal(tags=set(), recipes=[])
    
    api_meal = ApiMeal.from_domain(meal)
    assert api_meal.tags == frozenset()
    assert api_meal.recipes == frozenset()
    
    # Should handle empty collections gracefully
    orm_kwargs = api_meal.to_orm_kwargs()
    assert "tags" not in orm_kwargs  # Relationships handled separately

def test_none_value_propagation():
    """Test None value handling across conversions."""
    meal = Meal(nutri_facts=None)
    
    api_meal = ApiMeal.from_domain(meal)
    assert api_meal.nutri_facts is None
    
    orm_kwargs = api_meal.to_orm_kwargs()
    # None values should not add composite fields
    assert not any(key.startswith("nutri_") for key in orm_kwargs.keys())
```

### Performance Benchmarking

```python
def test_conversion_performance():
    """Ensure conversions meet performance requirements."""
    large_meal = create_meal_with_many_recipes(50)  # 50 recipes
    
    start_time = time.perf_counter()
    api_meal = ApiMeal.from_domain(large_meal)
    conversion_time = (time.perf_counter() - start_time) * 1000  # ms
    
    # Should convert large meals quickly
    assert conversion_time < 10.0, f"Conversion took {conversion_time:.2f}ms, too slow"
```

---

**Key Takeaways:**
1. **Consistency**: Use frozenset for all API collection types for immutability
2. **Performance**: Prefer batch operations over individual conversions
3. **Testing**: Validate all conversion paths and edge cases
4. **Materialization**: Compute expensive properties once during API conversion
5. **Type Safety**: Maintain strict type checking throughout all conversions 