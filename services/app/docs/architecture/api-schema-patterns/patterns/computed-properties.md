# Computed Properties Materialization Pattern

**Documentation for Phase 2.2.1: Computed Properties Pattern**

## Overview

This pattern handles the conversion of expensive domain computations into efficient, materialized values across the three architectural layers. Computed properties in the domain layer are materialized as regular fields in the API layer and stored as simple values in the ORM layer.

## Core Principle

**Domain computes, API materializes, ORM stores**

- **Domain Layer**: Expensive computations using `@cached_property` or regular computed properties
- **API Layer**: Materialized values as regular fields (no computation)
- **ORM Layer**: Stored materialized values as regular columns or composite fields

## Pattern Types

### 1. Cached Property Pattern (`@cached_property`)

For expensive computations that benefit from caching within a single domain object instance.

**Use Cases:**
- Aggregations across collections (nutrition facts from recipes)
- Complex calculations with multiple dependencies
- Operations with significant computational cost

**Domain Implementation:**
```python
class Meal(Entity):
    @cached_property
    def nutri_facts(self) -> NutriFacts | None:
        """
        Calculate aggregated nutritional facts for all recipes.
        
        Performance: O(n) computation where n = number of recipes,
        O(1) on subsequent accesses until cache invalidation.
        
        Cache invalidation triggers:
        - recipes setter: When the recipes collection is replaced
        - create_recipe(): When a new recipe is added
        - delete_recipe(): When a recipe is removed
        - update_recipes(): When recipe properties are updated
        """
        self._check_not_discarded()
        nutri_facts = NutriFacts()
        has_any_nutri_facts = False
        
        for recipe in self.recipes:
            if recipe.nutri_facts is not None:
                nutri_facts += recipe.nutri_facts
                has_any_nutri_facts = True
                
        return nutri_facts if has_any_nutri_facts else None
```

**API Materialization:**
```python
class ApiMeal(BaseApiModel[Meal, MealSaModel]):
    nutri_facts: MealNutriFacts  # Regular field, not computed
    
    @classmethod
    def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
        return cls(
            # ... other fields ...
            nutri_facts=ApiNutriFacts.from_domain(domain_obj.nutri_facts) if domain_obj.nutri_facts else None,
            # Materialize the computed value ↑
        )
```

**ORM Storage:**
```python
class MealSaModel(Base):
    nutri_facts: Mapped[NutriFactsSaModel] = composite(
        NutriFactsSaModel,
        "nutri_facts_calories",
        "nutri_facts_protein", 
        "nutri_facts_carbohydrate",
        "nutri_facts_total_fat",
        "nutri_facts_saturated_fat",
        "nutri_facts_trans_fat",
        "nutri_facts_dietary_fiber",
        "nutri_facts_sodium",
        "nutri_facts_sugar"
    )
```

### 2. Regular Computed Property Pattern

For lightweight computations that don't require caching.

**Use Cases:**
- Simple mathematical calculations
- Derived values from other properties
- Format conversions or unit calculations

**Domain Implementation:**
```python
class Meal(Entity):
    @property
    def calorie_density(self) -> float | None:
        """Calculate calories per 100g."""
        self._check_not_discarded()
        if self.nutri_facts and self.nutri_facts.calories.value is not None and self.weight_in_grams:
            return (self.nutri_facts.calories.value / self.weight_in_grams) * 100
        return None

    @property
    def carbo_percentage(self) -> float | None:
        """Carbohydrate percentage from macro division."""
        self._check_not_discarded()
        if self.macro_division:
            return self.macro_division.carbohydrate
        return None
```

**API Materialization:**
```python
class ApiMeal(BaseApiModel[Meal, MealSaModel]):
    calorie_density: MealCalorieDensity      # Materialized float value
    carbo_percentage: MealCarboPercentage    # Materialized percentage
    protein_percentage: MealProteinPercentage
    total_fat_percentage: MealTotalFatPercentage
    
    @classmethod
    def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
        return cls(
            # ... other fields ...
            calorie_density=domain_obj.calorie_density,           # Computed once, materialized
            carbo_percentage=domain_obj.carbo_percentage,         # Computed once, materialized
            protein_percentage=domain_obj.protein_percentage,     # Computed once, materialized
            total_fat_percentage=domain_obj.total_fat_percentage, # Computed once, materialized
        )
```

**ORM Storage:**
```python
class MealSaModel(Base):
    calorie_density: Mapped[float | None] = mapped_column()
    carbo_percentage: Mapped[float | None] = mapped_column()
    protein_percentage: Mapped[float | None] = mapped_column() 
    total_fat_percentage: Mapped[float | None] = mapped_column()
```

### 3. Dependency Chain Pattern

For computed properties that depend on other computed properties.

**Domain Implementation:**
```python
class Meal(Entity):
    @cached_property
    def nutri_facts(self) -> NutriFacts | None:
        """Base computation - expensive aggregation."""
        # ... expensive computation ...
        return aggregated_nutrition
        
    @property
    def macro_division(self) -> MacroDivision | None:
        """Depends on nutri_facts - lightweight computation."""
        self._check_not_discarded()
        if not self.nutri_facts:
            return None
            
        carb = self.nutri_facts.carbohydrate.value
        protein = self.nutri_facts.protein.value  
        fat = self.nutri_facts.total_fat.value
        
        if carb is None or protein is None or fat is None:
            return None
            
        denominator = carb + protein + fat
        if denominator == 0:
            return None
            
        return MacroDivision(
            carbohydrate=(carb / denominator) * 100,
            protein=(protein / denominator) * 100,
            fat=(fat / denominator) * 100,
        )
    
    @property
    def carbo_percentage(self) -> float | None:
        """Depends on macro_division."""
        if self.macro_division:
            return self.macro_division.carbohydrate
        return None
```

**API Materialization - Flattened Dependency Chain:**
```python
class ApiMeal(BaseApiModel[Meal, MealSaModel]):
    nutri_facts: MealNutriFacts              # Base computation materialized
    carbo_percentage: MealCarboPercentage    # Dependent computation materialized
    protein_percentage: MealProteinPercentage # Dependent computation materialized
    total_fat_percentage: MealTotalFatPercentage # Dependent computation materialized
    
    @classmethod
    def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
        # All computations happen once during conversion
        # Dependency chain is resolved and flattened
        return cls(
            nutri_facts=ApiNutriFacts.from_domain(domain_obj.nutri_facts) if domain_obj.nutri_facts else None,
            carbo_percentage=domain_obj.carbo_percentage,      # Resolved dependency
            protein_percentage=domain_obj.protein_percentage,  # Resolved dependency
            total_fat_percentage=domain_obj.total_fat_percentage, # Resolved dependency
        )
```

## Performance Characteristics

### Domain Layer Performance

**Cached Properties (`@cached_property`):**
- **First access**: O(n) where n = complexity of computation
- **Subsequent access**: O(1) until cache invalidation
- **Memory**: Cached value stored per instance
- **Baseline**: nutri_facts computation ~0.02ms (cached), ~2ms (first calculation)

**Regular Computed Properties:**
- **Every access**: O(1) for simple calculations
- **Memory**: No caching overhead
- **Baseline**: calorie_density ~0.2μs per access

### API Layer Performance

**Materialization During Conversion:**
- **from_domain()**: All computations executed once
- **Property access**: O(1) - direct field access
- **Memory**: Values stored as regular fields
- **Baseline**: Complete meal validation ~59μs including all materialized values

### Cache Behavior vs Materialization

```python
# Domain: Computed with caching
domain_meal.nutri_facts  # First access: expensive computation + caching
domain_meal.nutri_facts  # Subsequent access: O(1) cached retrieval

# API: Materialized values
api_meal = ApiMeal.from_domain(domain_meal)  # Computation happens here
api_meal.nutri_facts  # O(1) field access - no computation
api_meal.nutri_facts  # O(1) field access - always fast

# Cache invalidation in domain doesn't affect already materialized API values
domain_meal.create_recipe(new_recipe)  # Invalidates domain cache
api_meal.nutri_facts  # Still returns original materialized value
```

## Testing Strategy

### Validation Tests

**Pattern Compliance:**
```python
def test_computed_property_materialization(sample_meal):
    """Validate three-layer materialization pattern."""
    # Domain: Test computation behavior
    computed_value = sample_meal.nutri_facts
    assert isinstance(computed_value, NutriFacts)
    
    # API: Test materialization
    api_meal = ApiMeal.from_domain(sample_meal)
    materialized_value = api_meal.nutri_facts
    assert materialized_value.calories == computed_value.calories.value
    
    # ORM: Test storage
    orm_kwargs = api_meal.to_orm_kwargs()
    stored_value = orm_kwargs["nutri_facts"]
    assert stored_value.calories == computed_value.calories.value
```

**Cache Behavior:**
```python
def test_cache_invalidation_vs_materialization():
    """Test that cache invalidation doesn't affect materialized values."""
    meal = create_sample_meal()
    
    # Create API snapshot
    api_meal_before = ApiMeal.from_domain(meal)
    calories_before = api_meal_before.nutri_facts.calories
    
    # Modify domain (invalidates cache)
    meal.create_recipe(additional_recipe)
    
    # API snapshot remains unchanged
    assert api_meal_before.nutri_facts.calories == calories_before
    
    # New API conversion captures updated values
    api_meal_after = ApiMeal.from_domain(meal)
    assert api_meal_after.nutri_facts.calories > calories_before
```

### Performance Tests

```python
def test_performance_computed_vs_materialized():
    """Compare performance characteristics."""
    meal = create_complex_meal()
    
    # Domain: First access (computation)
    start = time.perf_counter()
    computed_nutri_facts = meal.nutri_facts
    first_access_time = time.perf_counter() - start
    
    # Domain: Cached access
    start = time.perf_counter()
    cached_nutri_facts = meal.nutri_facts
    cached_access_time = time.perf_counter() - start
    
    # API: Materialized access
    api_meal = ApiMeal.from_domain(meal)
    start = time.perf_counter()
    materialized_nutri_facts = api_meal.nutri_facts
    materialized_access_time = time.perf_counter() - start
    
    assert cached_access_time < first_access_time  # Caching benefit
    assert materialized_access_time < first_access_time  # Materialization benefit
    assert computed_nutri_facts is cached_nutri_facts  # Cache identity
```

## Error Handling

### Domain Layer Error Handling

```python
@cached_property
def nutri_facts(self) -> NutriFacts | None:
    """Handle computation failures gracefully."""
    try:
        self._check_not_discarded()
        if not self.recipes:
            return None
            
        total_facts = NutriFacts()
        has_data = False
        
        for recipe in self.recipes:
            if recipe.nutri_facts is not None:
                total_facts += recipe.nutri_facts
                has_data = True
                
        return total_facts if has_data else None
        
    except Exception as e:
        logger.warning(f"Failed to compute nutri_facts for meal {self.id}: {e}")
        return None  # Graceful degradation
```

### API Layer Error Handling

```python
@classmethod
def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
    """Handle materialization failures."""
    try:
        return cls(
            # Safe materialization with fallbacks
            nutri_facts=ApiNutriFacts.from_domain(domain_obj.nutri_facts) if domain_obj.nutri_facts else None,
            calorie_density=domain_obj.calorie_density,  # Returns None if computation fails
            carbo_percentage=domain_obj.carbo_percentage,  # Returns None if computation fails
        )
    except ValidationError as e:
        logger.error(f"Failed to materialize computed properties for meal {domain_obj.id}: {e}")
        raise ValueError(f"Invalid computed property values: {e}")
```

## Common Patterns and Anti-Patterns

### ✅ Correct Patterns

**Expensive Computation with Caching:**
```python
@cached_property
def nutri_facts(self) -> NutriFacts | None:
    """Heavy computation - cache it."""
    # Expensive aggregation logic
    return aggregated_result
```

**Lightweight Computation without Caching:**
```python
@property  
def calorie_density(self) -> float | None:
    """Simple calculation - compute every time."""
    if self.nutri_facts and self.weight_in_grams:
        return (self.nutri_facts.calories.value / self.weight_in_grams) * 100
    return None
```

**Proper Materialization:**
```python
@classmethod
def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
    return cls(
        nutri_facts=ApiNutriFacts.from_domain(domain_obj.nutri_facts) if domain_obj.nutri_facts else None,
        calorie_density=domain_obj.calorie_density,  # Computed once, materialized
    )
```

### ❌ Anti-Patterns

**Computing in API Layer:**
```python
# DON'T DO THIS
class ApiMeal(BaseApiModel):
    @property
    def nutri_facts(self) -> ApiNutriFacts:
        """❌ Computing in API layer - breaks pattern."""
        return self._compute_nutrition()  # Wrong layer for computation
```

**Caching Simple Calculations:**
```python
# DON'T DO THIS  
@cached_property
def calorie_density(self) -> float:
    """❌ Unnecessary caching for simple calculation."""
    return self.calories / self.weight  # Too simple to cache
```

**Missing Materialization:**
```python
# DON'T DO THIS
@classmethod
def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
    return cls(
        nutri_facts=domain_obj.nutri_facts,  # ❌ Not materialized - domain object leaked
    )
```

## Integration with Other Patterns

### Type Conversion Integration

```python
# Domain: Rich domain object
@cached_property  
def nutri_facts(self) -> NutriFacts:  # Domain value object
    return computed_nutrition

# API: Flattened structure
nutri_facts: ApiNutriFacts  # API value object

# ORM: Stored composite
nutri_facts: Mapped[NutriFactsSaModel]  # Composite field
```

### Collection Handling Integration

```python
# Domain: Working with domain collections
@cached_property
def nutri_facts(self) -> NutriFacts:
    for recipe in self.recipes:  # set[Recipe] in domain
        # Aggregate nutrition from recipe collection
        
# API: Materialized with proper collections
recipes: frozenset[ApiRecipe]  # Converted collection
nutri_facts: ApiNutriFacts     # Materialized computation result

# ORM: Stored relationships
recipes: Mapped[list[RecipeSaModel]]  # ORM relationship
nutri_facts: Mapped[NutriFactsSaModel]  # Stored composite
```

## Decision Guide

### When to Use `@cached_property`

**Use for:**
- Aggregations across collections
- Database queries or expensive I/O
- Complex mathematical computations
- Operations with > 1ms execution time

**Example Decision:**
```python
# ✅ Use @cached_property - expensive aggregation
@cached_property
def nutri_facts(self) -> NutriFacts:
    """Aggregates nutrition from all recipes - O(n) complexity."""
    
# ✅ Use regular @property - simple calculation  
@property
def calorie_density(self) -> float:
    """Simple division - O(1) complexity."""
```

### When to Materialize in API

**Always materialize:**
- All computed properties (cached or not)
- Values that will be used in API responses
- Data needed for serialization/deserialization

**Never materialize:**
- Simple getter/setter properties
- Internal domain state
- Framework-specific metadata

## Performance Benchmarks

Based on current implementation testing:

| Operation | Performance | Notes |
|-----------|-------------|--------|
| `nutri_facts` first access | ~2ms | Heavy aggregation computation |
| `nutri_facts` cached access | ~0.02ms | @cached_property benefit |
| `calorie_density` computation | ~0.2μs | Simple calculation |
| Complete meal materialization | ~59μs | All computed properties materialized |
| Complete meal validation | ~59μs | Includes all field validation |

**Performance Goals:**
- Cached property access: < 0.1ms
- Simple property computation: < 1μs  
- Complete materialization: < 100μs
- Full meal validation: < 200μs

## Maintenance Guidelines

### Cache Invalidation Management

**Explicit Invalidation:**
```python
def create_recipe(self, recipe_data):
    """Adding recipe invalidates nutrition cache."""
    self._recipes.append(new_recipe)
    # Cache invalidation handled automatically by @cached_property
    # when dependent data changes
```

**Documentation Requirements:**
```python
@cached_property
def nutri_facts(self) -> NutriFacts | None:
    """
    REQUIRED DOCUMENTATION:
    
    Cache invalidation triggers:
    - recipes setter: When recipes collection changes
    - create_recipe(): When new recipe added
    - delete_recipe(): When recipe removed
    
    Performance: O(n) first access, O(1) subsequent
    Dependencies: self.recipes collection
    """
```

### Testing Requirements

**Every computed property must have:**
1. **Unit test** validating computation logic
2. **Materialization test** validating API conversion
3. **Storage test** validating ORM persistence
4. **Performance test** validating acceptable speed
5. **Edge case test** validating None/empty handling

**Example test structure:**
```python
class TestNutriFacts:
    def test_computation_accuracy(self):
        """Test domain computation logic."""
        
    def test_materialization(self):
        """Test API materialization."""
        
    def test_storage(self):
        """Test ORM storage."""
        
    def test_performance(self):
        """Test performance characteristics."""
        
    def test_edge_cases(self):
        """Test None/empty handling."""
```

---

**Related Documentation:**
- [Four-Layer Conversion Pattern](../overview.md)
- [Type Conversion Strategies](./type-conversions.md)
- [Performance Guidelines](../performance.md)

**Testing Commands:**
```bash
# Run computed property validation tests
poetry run python pytest tests/documentation/api_patterns/test_computed_property_materialization.py -v

# Run performance baseline tests
poetry run python pytest tests/documentation/api_patterns/test_performance_baselines.py -v

# Run four-layer conversion tests
poetry run python pytest tests/documentation/api_patterns/test_meal_four_layer_conversion.py -v
``` 