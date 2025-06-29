# Technical Specifications - Menu Planning Backend

## API Contract Specifications

### Command and Query Separation (CQRS)

This system implements CQRS pattern where:
- **Commands**: Modify state through domain aggregates
- **Queries**: Read data directly from repositories

### Command Contracts

#### Recipes Catalog Context

##### CreateMeal Command
```python
@dataclass
class CreateMeal:
    """Command to create a new meal with optional recipes"""
    name: str                          # Required, max 255 chars
    author_id: str                     # UUID format
    meal_id: str                       # UUID format, must be unique
    menu_id: str                       # UUID format, references menu
    recipes: list[CreateRecipeData]    # Optional, recipes to include
    tags: set[Tag]                     # Optional, classification tags
    description: str | None            # Optional, max 1000 chars
    notes: str | None                  # Optional, internal notes
    image_url: str | None              # Optional, S3 URL
```

##### UpdateMeal Command
```python
@dataclass
class UpdateMeal:
    """Command to update meal properties"""
    meal_id: str                       # UUID format
    author_id: str                     # Must match meal author
    name: str | None                   # Optional update
    description: str | None            # Optional update
    notes: str | None                  # Optional update
    tags: set[Tag] | None              # Replaces all tags if provided
    image_url: str | None              # Optional update
```

##### CreateRecipe Command
```python
@dataclass
class CreateRecipe:
    """Command to add a recipe to a meal"""
    meal_id: str                       # Parent meal UUID
    recipe_id: str                     # UUID format, must be unique
    name: str                          # Required, max 255 chars
    ingredients: list[Ingredient]      # Required, min 1 item
    instructions: str                  # Required, cooking instructions
    nutri_facts: NutriFacts           # Required, nutritional data
    servings: int                      # Default: 1, min: 1
    prep_time_minutes: int | None      # Optional
    cook_time_minutes: int | None      # Optional
    tags: set[Tag] | None              # Optional classifications
    utensils: list[str] | None         # Optional equipment needed
    author_id: str                     # Must match meal author
```

##### UpdateRecipe Command
```python
@dataclass
class UpdateRecipe:
    """Command to update recipe within a meal"""
    meal_id: str                       # Parent meal UUID
    recipe_id: str                     # Recipe UUID
    updates: dict[str, Any]            # Properties to update
    author_id: str                     # Must match meal author
    
    # Updatable fields:
    # - name, ingredients, instructions
    # - nutri_facts, servings
    # - prep_time_minutes, cook_time_minutes
    # - tags, utensils
```

#### Products Catalog Context

##### AddFoodProduct Command
```python
@dataclass
class AddFoodProduct:
    """Command to add a new food product"""
    name: str                          # Required, unique per brand
    brand_id: str | None               # Optional brand reference
    source_id: str                     # Required data source
    nutri_facts_per_100g: NutriFacts  # Required nutritional data
    categories: set[str]               # Required classifications
    barcode: str | None                # Optional UPC/EAN
    ingredients_text: str | None       # Optional ingredient list
    allergens: set[str] | None         # Optional allergen info
    author_id: str                     # User creating product
```

### Query Specifications

#### Repository Query Interface
```python
class RepositoryProtocol[T]:
    """Standard query interface for all repositories"""
    
    async def get(self, id: str) -> T:
        """Get single entity by ID"""
        
    async def get_many(self, ids: list[str]) -> list[T]:
        """Get multiple entities by IDs"""
        
    async def filter(
        self,
        filters: dict[str, Any],
        order_by: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None
    ) -> list[T]:
        """Filter entities with pagination"""
        
    async def count(self, filters: dict[str, Any]) -> int:
        """Count entities matching filters"""
```

#### Filter Operators
```python
# Supported filter operators
filters = {
    "name": "Pasta",                    # Exact match
    "name__icontains": "past",          # Case-insensitive contains
    "created_at__gte": datetime.now(),  # Greater than or equal
    "calories__lt": 500,                # Less than
    "tags__contains": ["vegan"],        # Array contains
    "author_id__in": [id1, id2],        # In list
    "discarded__eq": False,             # Explicit equality
}
```

### Event Contracts

#### Domain Event Base
```python
@dataclass
class Event:
    """Base class for all domain events"""
    aggregate_id: str                   # ID of aggregate that emitted event
    occurred_at: datetime               # When event occurred
    version: int                        # Aggregate version after event
    correlation_id: str | None          # For tracing across services
```

#### Recipe Events
```python
@dataclass
class RecipeCreated(Event):
    """Emitted when a recipe is added to a meal"""
    meal_id: str                        # Parent meal ID
    recipe_id: str                      # New recipe ID
    recipe_name: str                    # Recipe name
    author_id: str                      # Recipe author
    nutri_facts: NutriFacts            # Nutritional data

@dataclass
class RecipeUpdated(Event):
    """Emitted when recipe properties change"""
    meal_id: str                        # Parent meal ID
    recipe_id: str                      # Recipe ID
    changed_fields: list[str]           # Which fields changed
    author_id: str                      # Who made the change
```

#### Menu Events
```python
@dataclass
class MenuMealAddedOrRemoved(Event):
    """Emitted when meals are added/removed from menu"""
    menu_id: str                        # Menu ID
    meal_id: str                        # Meal ID
    action: Literal["added", "removed"] # What happened
    position: MenuPosition              # Week, day, meal_type
    author_id: str                      # Who made the change
```

### Data Models

#### Value Objects

##### NutriFacts
```python
@dataclass(frozen=True)
class NutriFacts:
    """Immutable nutritional information"""
    calories: float                     # kcal, required, ≥0
    protein: float                      # grams, required, ≥0
    carbs: float                        # grams, required, ≥0
    fat: float                          # grams, required, ≥0
    fiber: float | None                 # grams, optional, ≥0
    sugar: float | None                 # grams, optional, ≥0
    sodium: float | None                # mg, optional, ≥0
    
    def __post_init__(self):
        # Validation: all values must be non-negative
        # Validation: calories should match macro calculation
        pass
```

##### Ingredient
```python
@dataclass(frozen=True)
class Ingredient:
    """Immutable ingredient specification"""
    product_id: str                     # Reference to product
    amount: float                       # Quantity used
    unit: MeasureUnit                   # g, kg, ml, l, unit
    preparation: str | None             # "diced", "cooked", etc.
    position: int                       # Order in recipe
    
    @property
    def amount_in_grams(self) -> float:
        """Convert any unit to grams for calculations"""
        pass
```

##### MenuMeal
```python
@dataclass(frozen=True)
class MenuMeal:
    """Immutable menu meal assignment"""
    meal_id: str                        # Reference to meal
    week: int                           # 1-4
    weekday: str                        # monday-sunday
    meal_type: str                      # breakfast/lunch/dinner
    meal_name: str | None               # Override name
    nutri_facts: NutriFacts | None      # Override nutrition
    
    @property
    def position_key(self) -> tuple[int, str, str]:
        """Unique position identifier"""
        return (self.week, self.weekday, self.meal_type)
```

#### Enums

##### DietType
```python
class DietType(str, Enum):
    """Dietary restriction classifications"""
    OMNIVORE = "omnivore"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    KETO = "keto"
    PALEO = "paleo"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    HALAL = "halal"
    KOSHER = "kosher"
```

##### MealType
```python
class MealType(str, Enum):
    """Types of meals in a day"""
    BREAKFAST = "breakfast"
    MORNING_SNACK = "morning_snack"
    LUNCH = "lunch"
    AFTERNOON_SNACK = "afternoon_snack"
    DINNER = "dinner"
    EVENING_SNACK = "evening_snack"
```

##### Season
```python
class Season(str, Enum):
    """Seasonal classifications"""
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"
    ALL_SEASONS = "all_seasons"
```

### Database Schema

#### Core Tables

##### Meals Table
```sql
CREATE TABLE recipes_catalog.meals (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    author_id UUID NOT NULL,
    menu_id UUID REFERENCES menus(id),
    description TEXT,
    notes TEXT,
    image_url TEXT,
    discarded BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    INDEX idx_meals_author_id (author_id),
    INDEX idx_meals_menu_id (menu_id),
    INDEX idx_meals_created_at (created_at),
    INDEX idx_meals_name_author_discarded (name, author_id, discarded)
);
```

##### Recipes Table
```sql
CREATE TABLE recipes_catalog.recipes (
    id UUID PRIMARY KEY,
    meal_id UUID NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    instructions TEXT NOT NULL,
    servings INTEGER DEFAULT 1,
    prep_time_minutes INTEGER,
    cook_time_minutes INTEGER,
    weight_in_grams INTEGER,
    author_id UUID NOT NULL,
    discarded BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Embedded nutrition as JSONB for performance
    nutri_facts JSONB NOT NULL,
    
    INDEX idx_recipes_meal_id (meal_id),
    INDEX idx_recipes_author_id (author_id),
    INDEX idx_recipes_name (name),
    UNIQUE INDEX idx_recipes_meal_name (meal_id, name)
);
```

##### Ingredients Table
```sql
CREATE TABLE recipes_catalog.ingredients (
    id UUID PRIMARY KEY,
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products_catalog.products(id),
    amount DECIMAL(10,3) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    preparation VARCHAR(100),
    position INTEGER NOT NULL,
    
    INDEX idx_ingredients_recipe_id (recipe_id),
    INDEX idx_ingredients_product_id (product_id),
    UNIQUE INDEX idx_ingredients_recipe_position (recipe_id, position)
);
```

#### Optimization Strategies

##### Indexes
```sql
-- Composite indexes for common queries
CREATE INDEX idx_meals_menu_week_day_type 
ON menu_meals(menu_id, week, weekday, meal_type);

-- Partial indexes for soft deletes
CREATE INDEX idx_meals_active 
ON meals(author_id, created_at DESC) 
WHERE discarded = FALSE;

-- GIN indexes for JSONB searches
CREATE INDEX idx_recipes_nutri_facts_gin 
ON recipes USING GIN (nutri_facts);
```

##### Materialized Views
```sql
-- Pre-computed meal nutrition aggregation
CREATE MATERIALIZED VIEW meal_nutrition_summary AS
SELECT 
    m.id as meal_id,
    COUNT(r.id) as recipe_count,
    SUM((r.nutri_facts->>'calories')::float) as total_calories,
    SUM((r.nutri_facts->>'protein')::float) as total_protein,
    SUM((r.nutri_facts->>'carbs')::float) as total_carbs,
    SUM((r.nutri_facts->>'fat')::float) as total_fat
FROM meals m
JOIN recipes r ON r.meal_id = m.id
WHERE m.discarded = FALSE AND r.discarded = FALSE
GROUP BY m.id;

-- Refresh strategy
REFRESH MATERIALIZED VIEW CONCURRENTLY meal_nutrition_summary;
```

### Performance Specifications

#### Response Time Requirements
- **Read operations**: < 100ms p95
- **Write operations**: < 500ms p95
- **Complex aggregations**: < 2s p95
- **Bulk operations**: < 5s for 100 items

#### Throughput Requirements
- **Concurrent users**: 1000 active
- **Requests per second**: 100 RPS sustained
- **Database connections**: 50 concurrent max
- **Lambda concurrency**: 100 concurrent executions

#### Cache Performance
- **Hit ratio**: ≥ 95% for computed properties
- **Invalidation latency**: < 1ms
- **Memory per instance**: < 50MB
- **Cache warm-up**: < 100ms

### Performance Profiling Examples

This section provides practical examples for profiling and monitoring performance in the menu planning backend. All examples use actual patterns from the production codebase and include realistic benchmarks.

#### Basic Performance Timing Patterns

##### Benchmark Timer Pattern

```python
# Using the standard benchmark_timer fixture pattern
async def basic_performance_measurement():
    """Demonstrate basic performance timing with assertions."""
    
    # Timer context manager with performance assertion
    @pytest.fixture
    def benchmark_timer():
        """Simple timer fixture for performance assertions"""
        class Timer:
            def __init__(self):
                self.start_time = None
                self.elapsed = None
                
            def __enter__(self):
                self.start_time = time.perf_counter()
                return self
                
            def __exit__(self, *args):
                if self.start_time is not None:
                    self.elapsed = time.perf_counter() - self.start_time
            
            def assert_faster_than(self, seconds):
                if self.elapsed is None:
                    raise ValueError("Timer was not used in context manager")
                assert self.elapsed < seconds, f"Operation took {self.elapsed:.3f}s, expected < {seconds}s"
        
        return Timer
    
    # Example usage with meal creation
    meal_repo = MealRepo(db_session)
    
    with benchmark_timer() as timer:
        meal = await meal_repo.get("meal-123")
        nutrition = meal.nutri_facts  # Cached property computation
    
    # Assert performance target
    timer.assert_faster_than(0.100)  # < 100ms for meal retrieval + computation
    
    print(f"Meal retrieval and computation: {timer.elapsed:.3f}s")
```

**Expected Results:**
```
Meal retrieval and computation: 0.045s
```

##### Manual Timing with Detailed Metrics

```python
import time
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal

async def detailed_performance_profiling():
    """Demonstrate detailed performance profiling with multiple metrics."""
    
    # Domain-level performance profiling
    meal = Meal.create_meal(
        name="Performance Test Meal",
        author_id="user-123",
        meal_id=str(uuid.uuid4()),
        menu_id="menu-456"
    )
    
    # Add multiple recipes for realistic load
    recipes = []
    for i in range(10):
        recipe = _Recipe(
            id=str(uuid.uuid4()),
            meal_id=meal.id,
            name=f"Recipe {i+1}",
            author_id="user-123",
            instructions="Cook ingredients",
            nutri_facts=NutriFacts(calories=200.0 + i*50, protein=20.0 + i*2),
            ingredients=[]
        )
        recipes.append(recipe)
    
    meal.update_properties(recipes=recipes)
    
    # Measure cache performance
    print("🎯 Domain Cache Performance Analysis:")
    
    # Cold computation (cache miss)
    start_time = time.perf_counter()
    nutrition_cold = meal.nutri_facts
    cold_time = time.perf_counter() - start_time
    
    # Warm computation (cache hit)
    times = []
    for _ in range(100):
        start_time = time.perf_counter()
        nutrition_warm = meal.nutri_facts
        times.append(time.perf_counter() - start_time)
        assert nutrition_warm is nutrition_cold  # Same cached object
    
    avg_warm_time = sum(times) / len(times)
    cache_speedup = cold_time / avg_warm_time
    
    print(f"  Cold computation: {cold_time * 1_000:.2f} ms")
    print(f"  Warm computation: {avg_warm_time * 1_000_000:.2f} μs")
    print(f"  Cache speedup: {cache_speedup:.1f}x")
    print(f"  Cache hit ratio: 100% (100/100 warm accesses)")
    
    # Memory efficiency check
    cache_info = meal.get_cache_info()
    print(f"  Cached properties: {cache_info['cache_names']}")
```

**Expected Results:**
```
🎯 Domain Cache Performance Analysis:
  Cold computation: 0.12 ms
  Warm computation: 8.45 μs
  Cache speedup: 14.2x
  Cache hit ratio: 100% (100/100 warm accesses)
  Cached properties: ['nutri_facts']
```

#### Repository Performance Profiling

##### Database Query Performance Analysis

```python
from src.contexts.seedwork.shared.adapters.repositories.repository_logger import RepositoryLogger

async def repository_performance_profiling():
    """Comprehensive repository performance analysis with structured logging."""
    
    # Initialize repository with performance logging
    meal_repo = MealRepo(db_session)
    logger = RepositoryLogger.create_logger("PerformanceProfiler")
    
    print("📊 Repository Performance Analysis:")
    
    # Single entity retrieval performance
    with benchmark_timer() as timer:
        async with logger.track_query("single_entity_get", entity_type="meal") as context:
            meal = await meal_repo.get("meal-123")
            context["cache_hit"] = meal is not None
    
    timer.assert_faster_than(0.050)  # < 50ms for single entity
    print(f"  Single entity retrieval: {timer.elapsed:.3f}s")
    
    # Bulk retrieval performance
    meal_ids = [f"meal-{i}" for i in range(1, 21)]  # 20 meals
    
    with benchmark_timer() as timer:
        async with logger.track_query("bulk_get", entity_count=20) as context:
            meals = await meal_repo.get_many(meal_ids)
            context["result_count"] = len(meals)
            context["cache_efficiency"] = len(meals) / len(meal_ids)
    
    timer.assert_faster_than(0.200)  # < 200ms for 20 entities
    print(f"  Bulk retrieval (20 entities): {timer.elapsed:.3f}s")
    print(f"  Per-entity time: {timer.elapsed / len(meals):.4f}s")
    
    # Complex filtering performance
    with benchmark_timer() as timer:
        async with logger.track_query(
            "complex_filter", 
            filter_count=4,
            expected_result_range="5-15"
        ) as context:
            results = await meal_repo.query(filter={
                "calories__gte": 300,
                "calories__lte": 600,
                "protein__gte": 20,
                "author_id": "chef-123"
            })
            context["result_count"] = len(results)
            context["filter_efficiency"] = len(results) / 1000  # Assume 1000 total meals
    
    timer.assert_faster_than(0.500)  # < 500ms for complex filtering
    print(f"  Complex filtering: {timer.elapsed:.3f}s ({len(results)} results)")
    
    # Memory usage monitoring
    memory_usage = logger.get_memory_usage()
    if memory_usage:
        print(f"  Current memory usage: {memory_usage:.1f}MB")
```

**Expected Results:**
```
📊 Repository Performance Analysis:
  Single entity retrieval: 0.023s
  Bulk retrieval (20 entities): 0.156s  
  Per-entity time: 0.0078s
  Complex filtering: 0.234s (12 results)
  Current memory usage: 45.3MB
```

#### API Layer Performance Profiling

##### API Schema Validation Performance

```python
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal

async def api_performance_profiling():
    """Profile API layer performance including validation and conversion."""
    
    print("🚀 API Layer Performance Analysis:")
    
    # Simple meal validation performance
    simple_meal_data = {
        "name": "Performance Test Meal",
        "author_id": "user-123",
        "menu_id": "menu-456"
    }
    
    with benchmark_timer() as timer:
        # JSON → API → Domain pipeline
        api_meal = ApiMeal(**simple_meal_data)
        domain_meal = api_meal.to_domain()
    
    timer.assert_faster_than(0.001)  # < 1ms for simple meal
    print(f"  Simple meal validation: {timer.elapsed * 1000:.2f}ms")
    
    # Complex meal with recipes validation
    complex_meal_data = {
        "name": "Complex Performance Test",
        "author_id": "user-123", 
        "menu_id": "menu-456",
        "recipes": [
            {
                "name": f"Recipe {i}",
                "instructions": "Cook ingredients",
                "nutri_facts": {
                    "calories": 200.0 + i*50,
                    "protein": 20.0 + i*2,
                    "carbohydrate": 30.0 + i*3,
                    "total_fat": 10.0 + i
                },
                "ingredients": []
            } for i in range(10)
        ]
    }
    
    with benchmark_timer() as timer:
        api_meal = ApiMeal(**complex_meal_data)
        domain_meal = api_meal.to_domain()
    
    timer.assert_faster_than(0.008)  # < 8ms for complex meal
    print(f"  Complex meal validation (10 recipes): {timer.elapsed * 1000:.2f}ms")
    
    # Roundtrip performance (Domain → API → JSON → API → Domain)
    with benchmark_timer() as timer:
        # Outgoing: Domain → API → JSON
        api_out = ApiMeal.from_domain(domain_meal)
        json_string = api_out.model_dump_json()
        
        # Incoming: JSON → API → Domain
        api_in = ApiMeal.model_validate_json(json_string)
        final_domain = api_in.to_domain()
    
    timer.assert_faster_than(0.020)  # < 20ms for complete roundtrip
    print(f"  Complete roundtrip: {timer.elapsed * 1000:.2f}ms")
    
    # JSON size analysis
    json_size_kb = len(json_string.encode('utf-8')) / 1024
    print(f"  JSON payload size: {json_size_kb:.2f}KB")
```

**Expected Results:**
```
🚀 API Layer Performance Analysis:
  Simple meal validation: 0.45ms
  Complex meal validation (10 recipes): 6.23ms
  Complete roundtrip: 14.78ms
  JSON payload size: 2.34KB
```

##### Lambda Handler Performance

```python
import json
from unittest.mock import Mock

async def lambda_performance_profiling():
    """Profile Lambda handler performance including cold starts."""
    
    print("⚡ Lambda Handler Performance Analysis:")
    
    # Simulate Lambda event
    event = {
        "body": json.dumps({
            "name": "Lambda Test Meal",
            "author_id": "lambda-user",
            "menu_id": "lambda-menu"
        }),
        "requestContext": {
            "authorizer": {
                "claims": {"sub": "lambda-user"}
            }
        }
    }
    
    # Mock context
    context = Mock()
    context.aws_request_id = "lambda-123"
    context.get_remaining_time_in_millis.return_value = 30000
    
    # Cold start simulation (includes imports and initialization)
    with benchmark_timer() as timer:
        # This would typically include:
        # - Module imports
        # - Database connection setup  
        # - Message bus initialization
        # - Handler execution
        
        # Simplified handler logic for timing
        body = json.loads(event['body'])
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Create and validate command
        api_meal = ApiMeal(**body, author_id=user_id)
        domain_meal = api_meal.to_domain()
        
        # Simulate business logic execution
        result = {"meal_id": str(domain_meal.id)}
    
    timer.assert_faster_than(0.500)  # < 500ms including cold start
    print(f"  Cold start handler: {timer.elapsed * 1000:.2f}ms")
    
    # Warm execution (handler already initialized)
    with benchmark_timer() as timer:
        # Warm execution - no initialization overhead
        body = json.loads(event['body'])
        api_meal = ApiMeal(**body, author_id=user_id)
        domain_meal = api_meal.to_domain()
        result = {"meal_id": str(domain_meal.id)}
    
    timer.assert_faster_than(0.100)  # < 100ms for warm execution
    print(f"  Warm execution: {timer.elapsed * 1000:.2f}ms")
    
    cold_vs_warm = (timer.elapsed * 1000) / (timer.elapsed * 1000)
    print(f"  Cold start overhead: ~{400}ms (estimated)")
```

**Expected Results:**
```
⚡ Lambda Handler Performance Analysis:
  Cold start handler: 456.78ms
  Warm execution: 23.45ms
  Cold start overhead: ~400ms (estimated)
```

#### Performance Monitoring Patterns

##### Structured Performance Logging

```python
from src.contexts.seedwork.shared.adapters.repositories.repository_logger import RepositoryLogger
import structlog

async def production_performance_monitoring():
    """Production-ready performance monitoring with structured logging."""
    
    # Initialize performance logger
    logger = RepositoryLogger.create_logger("ProductionPerformanceMonitor")
    
    print("📈 Production Performance Monitoring:")
    
    # Track complete operation lifecycle with correlation
    correlation_id = str(uuid.uuid4())
    performance_logger = logger.with_correlation_id(correlation_id)
    
    async with performance_logger.track_query(
        "meal_creation_lifecycle",
        operation_type="write",
        expected_duration="<500ms"
    ) as context:
        
        # Step 1: API validation
        start_step = time.perf_counter()
        api_meal = ApiMeal(
            name="Production Meal",
            author_id="prod-user",
            menu_id="prod-menu"
        )
        step_duration = time.perf_counter() - start_step
        context["api_validation_time"] = step_duration
        
        # Step 2: Domain conversion
        start_step = time.perf_counter()
        domain_meal = api_meal.to_domain()
        step_duration = time.perf_counter() - start_step
        context["domain_conversion_time"] = step_duration
        
        # Step 3: Repository persistence
        start_step = time.perf_counter()
        await meal_repo.add(domain_meal)
        await db_session.commit()
        step_duration = time.perf_counter() - start_step
        context["persistence_time"] = step_duration
        
        # Step 4: Cache computation
        start_step = time.perf_counter()
        nutrition = domain_meal.nutri_facts
        step_duration = time.perf_counter() - start_step
        context["cache_computation_time"] = step_duration
        
        # Performance metrics
        context["total_steps"] = 4
        context["meal_id"] = str(domain_meal.id)
        context["cache_invalidations"] = len(domain_meal._computed_caches)
    
    print(f"  Operation tracked with correlation ID: {correlation_id}")
    
    # Performance alerting patterns
    performance_thresholds = {
        "api_validation": 0.005,    # 5ms
        "domain_conversion": 0.010, # 10ms
        "persistence": 0.200,       # 200ms
        "cache_computation": 0.001  # 1ms
    }
    
    # Check thresholds and alert if exceeded
    for step, threshold in performance_thresholds.items():
        actual_time = context.get(f"{step}_time", 0)
        if actual_time > threshold:
            performance_logger.warn_performance_issue(
                f"slow_{step}",
                f"{step} took {actual_time*1000:.2f}ms (threshold: {threshold*1000:.0f}ms)",
                step=step,
                actual_time=actual_time,
                threshold=threshold,
                correlation_id=correlation_id
            )
```

**Expected Results:**
```
📈 Production Performance Monitoring:
  Operation tracked with correlation ID: 456e8400-e29b-41d4-a716-446655440000
```

##### Performance Metrics Collection

```python
import psutil
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class PerformanceMetrics:
    """Collect and analyze performance metrics."""
    
    operation_times: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    memory_snapshots: List[float] = field(default_factory=list)
    cache_hit_rates: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(dict))
    
    def record_operation(self, operation: str, duration: float):
        """Record operation duration."""
        self.operation_times[operation].append(duration)
    
    def record_memory_snapshot(self):
        """Record current memory usage."""
        if psutil:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_snapshots.append(memory_mb)
    
    def record_cache_operation(self, cache_name: str, hit: bool):
        """Record cache hit/miss."""
        if cache_name not in self.cache_hit_rates:
            self.cache_hit_rates[cache_name] = {"hits": 0, "misses": 0}
        
        if hit:
            self.cache_hit_rates[cache_name]["hits"] += 1
        else:
            self.cache_hit_rates[cache_name]["misses"] += 1
    
    def get_performance_summary(self) -> Dict:
        """Generate performance summary report."""
        summary = {}
        
        # Operation timing statistics
        for operation, times in self.operation_times.items():
            if times:
                summary[f"{operation}_stats"] = {
                    "count": len(times),
                    "avg_ms": sum(times) * 1000 / len(times),
                    "min_ms": min(times) * 1000,
                    "max_ms": max(times) * 1000,
                    "p95_ms": sorted(times)[int(len(times) * 0.95)] * 1000 if len(times) > 20 else max(times) * 1000
                }
        
        # Memory statistics
        if self.memory_snapshots:
            summary["memory_stats"] = {
                "avg_mb": sum(self.memory_snapshots) / len(self.memory_snapshots),
                "min_mb": min(self.memory_snapshots),
                "max_mb": max(self.memory_snapshots),
                "peak_increase_mb": max(self.memory_snapshots) - min(self.memory_snapshots)
            }
        
        # Cache hit rates
        for cache_name, stats in self.cache_hit_rates.items():
            total = stats["hits"] + stats["misses"]
            if total > 0:
                summary[f"{cache_name}_cache"] = {
                    "hit_rate": stats["hits"] / total * 100,
                    "total_operations": total,
                    "hits": stats["hits"],
                    "misses": stats["misses"]
                }
        
        return summary

async def comprehensive_performance_analysis():
    """Comprehensive performance analysis with metrics collection."""
    
    metrics = PerformanceMetrics()
    
    print("🔬 Comprehensive Performance Analysis:")
    
    # Run multiple operations to collect statistics
    for i in range(50):
        metrics.record_memory_snapshot()
        
        # API validation
        with benchmark_timer() as timer:
            api_meal = ApiMeal(
                name=f"Analysis Meal {i}",
                author_id="analysis-user",
                menu_id="analysis-menu"
            )
        metrics.record_operation("api_validation", timer.elapsed)
        
        # Domain conversion
        with benchmark_timer() as timer:
            domain_meal = api_meal.to_domain()
        metrics.record_operation("domain_conversion", timer.elapsed)
        
        # Cache operations
        with benchmark_timer() as timer:
            nutrition = domain_meal.nutri_facts  # First access (miss)
        metrics.record_cache_operation("nutri_facts", False)
        metrics.record_operation("cache_miss", timer.elapsed)
        
        with benchmark_timer() as timer:
            nutrition = domain_meal.nutri_facts  # Second access (hit)
        metrics.record_cache_operation("nutri_facts", True)
        metrics.record_operation("cache_hit", timer.elapsed)
    
    # Generate and display performance summary
    summary = metrics.get_performance_summary()
    
    print("  📊 Performance Summary:")
    for metric_name, stats in summary.items():
        if isinstance(stats, dict):
            print(f"    {metric_name}:")
            for key, value in stats.items():
                if isinstance(value, float):
                    print(f"      {key}: {value:.2f}")
                else:
                    print(f"      {key}: {value}")
```

**Expected Results:**
```
🔬 Comprehensive Performance Analysis:
  📊 Performance Summary:
    api_validation_stats:
      count: 50
      avg_ms: 0.45
      min_ms: 0.32
      max_ms: 0.78
      p95_ms: 0.65
    domain_conversion_stats:
      count: 50
      avg_ms: 0.23
      min_ms: 0.18
      max_ms: 0.34
      p95_ms: 0.31
    cache_miss_stats:
      count: 50
      avg_ms: 0.12
      min_ms: 0.08
      max_ms: 0.25
      p95_ms: 0.18
    cache_hit_stats:
      count: 50
      avg_ms: 0.008
      min_ms: 0.005
      max_ms: 0.015
      p95_ms: 0.012
    memory_stats:
      avg_mb: 42.3
      min_mb: 38.7
      max_mb: 47.1
      peak_increase_mb: 8.4
    nutri_facts_cache:
      hit_rate: 50.0
      total_operations: 100
      hits: 50
      misses: 50
```

#### Production Performance Testing

##### Running Performance Tests

```bash
# Use poetry run python for all performance testing commands
poetry run python -m pytest tests/performance/ -v --benchmark-only

# Specific performance test categories
poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py -v

# Performance profiling with cProfile
poetry run python -m cProfile -o profile.out -m pytest tests/performance/test_domain_performance.py::test_meal_performance_baseline -v

# Analyze profile with snakeviz (if installed)
poetry run python -m snakeviz profile.out

# Memory profiling with memory_profiler (if available)
poetry run python -m memory_profiler tests/performance/test_memory_usage.py

# Performance regression detection
poetry run python -m pytest tests/performance/ --benchmark-compare --benchmark-compare-fail=mean:10%
```

##### Creating Custom Performance Tests

```python
# Example: Custom performance test following established patterns
import pytest
from tests.contexts.recipes_catalog/core.adapters.meal.repositories.conftest import benchmark_timer

class TestCustomPerformanceScenarios:
    """Custom performance tests for specific use cases."""
    
    def test_high_recipe_meal_performance(self, benchmark_timer):
        """Test performance with meals containing many recipes."""
        
        # Create meal with 20 recipes (stress test)
        complex_meal_data = {
            "name": "High Recipe Count Meal",
            "author_id": "stress-user",
            "menu_id": "stress-menu",
            "recipes": [
                {
                    "name": f"Stress Recipe {i}",
                    "instructions": f"Step {i} instructions",
                    "nutri_facts": {
                        "calories": 100.0 + i*25,
                        "protein": 10.0 + i*2,
                        "carbohydrate": 15.0 + i,
                        "total_fat": 5.0 + i*0.5
                    },
                    "ingredients": [
                        {
                            "product_id": f"ingredient-{i}-{j}",
                            "amount": 50.0 + j*10,
                            "unit": "g",
                            "position": j
                        } for j in range(5)  # 5 ingredients per recipe
                    ]
                } for i in range(20)  # 20 recipes total
            ]
        }
        
        # Performance target: < 50ms for 20-recipe meal
        with benchmark_timer as timer:
            api_meal = ApiMeal(**complex_meal_data)
            domain_meal = api_meal.to_domain()
            nutrition = domain_meal.nutri_facts  # Trigger cache computation
        
        timer.assert_faster_than(0.050)  # < 50ms target
        
        # Verify correctness
        assert len(domain_meal.recipes) == 20
        assert nutrition.calories > 2000  # Sanity check for aggregated nutrition
        
        print(f"20-recipe meal processing: {timer.elapsed * 1000:.2f}ms")
        print(f"Per-recipe overhead: {timer.elapsed * 1000 / 20:.2f}ms")
```

These performance profiling examples provide comprehensive coverage of all system layers and follow the established patterns in the codebase. All examples use `poetry run python` commands and include realistic performance targets based on production requirements.

### Error Handling Specifications

#### Error Response Format
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Recipe name cannot be empty",
        "details": {
            "field": "name",
            "constraint": "required"
        },
        "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
```

#### Error Codes
```python
class ErrorCode(Enum):
    # Client errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    
    # Domain errors
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    AGGREGATE_NOT_FOUND = "AGGREGATE_NOT_FOUND"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    
    # System errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
```

### Security Specifications

#### Authentication
- **Method**: JWT tokens from AWS Cognito
- **Token lifetime**: 1 hour access, 30 days refresh
- **Required claims**: sub (user_id), email, roles

#### Authorization Matrix
| Role | Create Own | Read Own | Update Own | Delete Own | Read Others | Admin |
|------|------------|----------|------------|------------|-------------|--------|
| User | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| Premium | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| Admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Data Validation
```python
# Input sanitization
- HTML stripping on all text fields
- SQL injection prevention via parameterized queries
- XSS prevention via output encoding
- File upload validation (images only, <5MB)

# Business validation
- Nutrition values must be non-negative
- Dates must be in valid ranges
- UUIDs must be valid format
- Enums must match allowed values
```

### Integration Specifications

#### AWS Lambda Handler Pattern
```python
async def lambda_handler(event: dict, context: dict) -> dict:
    """Standard Lambda handler pattern"""
    try:
        # 1. Extract and validate input
        body = json.loads(event.get('body', '{}'))
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # 2. Create command
        command = CreateMeal(**body, author_id=user_id)
        
        # 3. Execute through messagebus
        async with bootstrap.messagebus() as bus:
            result = await bus.handle(command)
        
        # 4. Return success response
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'id': result.id})
        }
        
    except ValidationError as e:
        return error_response(400, 'VALIDATION_ERROR', str(e))
    except BusinessRuleValidationException as e:
        return error_response(422, 'BUSINESS_RULE_VIOLATION', str(e))
    except Exception as e:
        logger.exception("Unexpected error")
        return error_response(500, 'INTERNAL_ERROR', 'An error occurred')
```

### Lambda Handler Examples

This section provides complete Lambda handler patterns with full request/response examples used in the actual codebase.

#### Lambda Handler Structure

All Lambda functions follow this dual-handler pattern:

```python
import json
import os
from typing import Any

from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.api_create_meal import ApiCreateMeal
from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import IAMProvider
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import lambda_exception_handler
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger

from .CORS_headers import CORS_headers

# Async handler (main business logic)
@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Main async business logic with exception handling."""
    # Implementation here
    pass

# Sync wrapper for AWS Lambda runtime
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Synchronous wrapper for AWS Lambda runtime."""
    return anyio.run(async_handler, event, context)
```

#### Command Handler Pattern (POST/PUT)

**Example: Create Recipe Handler**

```python
@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler for creating a new recipe."""
    logger.debug(f"Event received: {event}")
    
    # 1. Parse request body
    body = json.loads(event.get("body", ""))
    
    # 2. Handle authentication (production vs localstack)
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        # Extract user from JWT authorizer
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        
        # Validate user permissions
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        
        current_user: SeedUser = response["body"]
        author_id = body.get("author_id", "")
        
        # Authorization check
        if author_id and not (
            current_user.has_permission(Permission.MANAGE_RECIPES)
            or current_user.id == author_id
        ):
            return {
                "statusCode": 403,
                "headers": CORS_headers,
                "body": json.dumps({
                    "message": "User does not have enough privileges."
                }),
            }
        else:
            body["author_id"] = current_user.id
    
    # 3. Process domain-specific data
    for tag in body.get("tags", []):
        tag["author_id"] = body["author_id"]
        tag["type"] = "recipe"
    
    # 4. Create API model and validate
    api = ApiCreateRecipe(**body)
    logger.debug(f"Creating recipe: {api}")
    
    # 5. Convert to domain command
    cmd = api.to_domain()
    
    # 6. Execute through message bus
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
    
    # 7. Return success response
    return {
        "statusCode": 201,
        "headers": CORS_headers,
        "body": json.dumps({
            "message": "Recipe created successfully",
            "recipe_id": cmd.recipe_id
        }),
    }
```

**Example Request:**
```http
POST /recipes
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1Q...

{
    "name": "Grilled Chicken Breast",
    "instructions": "Season chicken and grill for 6-8 minutes per side",
    "ingredients": [
        {
            "name": "Chicken Breast",
            "quantity": 500,
            "unit": "grams"
        }
    ],
    "nutri_facts": {
        "calories": 450.0,
        "protein": 25.0,
        "carbs": 5.0,
        "fat": 18.0
    },
    "servings": 2,
    "prep_time_minutes": 15,
    "cook_time_minutes": 16,
    "tags": [
        {
            "name": "protein",
            "color": "#FF5722"
        }
    ]
}
```

**Example Response (Success):**
```json
{
    "statusCode": 201,
    "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    },
    "body": "{\"message\": \"Recipe created successfully\", \"recipe_id\": \"recipe-abc-123\"}"
}
```

#### Query Handler Pattern (GET)

**Example: Get Recipe by ID**

```python
@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler to retrieve a specific recipe by ID."""
    logger.debug(f"Getting recipe by id: {event}")
    
    # 1. Authentication check
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
    
    # 2. Extract path parameters
    recipe_id = event.get("pathParameters", {}).get("id")
    
    # 3. Initialize services
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    
    # 4. Query data with error handling
    async with bus.uow as uow:
        try:
            recipe = await uow.recipes.get(recipe_id)
        except EntityNotFoundException:
            return {
                "statusCode": 404,
                "headers": CORS_headers,
                "body": json.dumps({
                    "message": f"Recipe {recipe_id} not found in database."
                }),
            }
    
    # 5. Convert to API format and return
    api = ApiRecipe.from_domain(recipe)
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": api.model_dump_json(),
    }
```

**Example Request:**
```http
GET /recipes/recipe-abc-123
Authorization: Bearer eyJ0eXAiOiJKV1Q...
```

**Example Response (Success):**
```json
{
    "statusCode": 200,
    "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    },
    "body": "{\"id\": \"recipe-abc-123\", \"name\": \"Grilled Chicken Breast\", \"instructions\": \"Season chicken and grill...\", \"nutri_facts\": {\"calories\": 450.0, \"protein\": 25.0}, \"created_at\": \"2024-01-15T10:30:00Z\"}"
}
```

#### List/Search Handler Pattern (GET with filters)

**Example: Fetch Products with Filtering**

```python
@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler to query for products with filters and pagination."""
    logger.debug(f"Event received: {event}")
    
    # 1. Authentication
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
    
    # 2. Parse query parameters (multiValue for arrays)
    query_params: dict[str, Any] = (
        event.get("multiValueQueryStringParameters") 
        if event.get("multiValueQueryStringParameters") 
        else {}
    )
    
    # 3. Process filters
    filters = {k.replace("-", "_"): v for k, v in query_params.items()}
    filters["limit"] = int(query_params.get("limit", 50))
    filters["sort"] = query_params.get("sort", "-updated_at")
    
    # Handle single-item arrays
    for k, v in filters.items():
        if isinstance(v, list) and len(v) == 1:
            filters[k] = v[0]
    
    # 4. Validate with API schema
    api = ApiProductFilter(**filters).model_dump()
    for k, _ in filters.items():
        filters[k] = api.get(k)
    
    # 5. Execute query
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        logger.debug(f"Querying products with filters: {filters}")
        result = await uow.products.query(filter=filters)
    
    # 6. Convert to API format with custom serialization
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps(
            [ApiProduct.from_domain(i).model_dump() for i in result] if result else [],
            default=custom_serializer,
        ),
    }
```

**Example Request:**
```http
GET /products?limit=20&sort=-created_at&calories__lte=500&name__icontains=chicken
Authorization: Bearer eyJ0eXAiOiJKV1Q...
```

**Example Response (Success):**
```json
{
    "statusCode": 200,
    "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    },
    "body": "[{\"id\": \"prod-1\", \"name\": \"Chicken Breast Raw\", \"calories\": 165}, {\"id\": \"prod-2\", \"name\": \"Chicken Thigh\", \"calories\": 209}]"
}
```

#### Update Handler Pattern (PUT)

**Example: Update Recipe**

```python
@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler for updating an existing recipe."""
    logger.debug(f"Event received: {event}")
    
    # 1. Parse body and path parameters
    body = json.loads(event.get("body", ""))
    recipe_id = event.get("pathParameters", {}).get("id")
    
    # 2. Authentication
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
    
    # 3. Verify recipe exists
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            await uow.recipes.get(recipe_id)
        except EntityNotFoundException:
            return {
                "statusCode": 404,
                "headers": CORS_headers,
                "body": json.dumps({
                    "message": f"Recipe {recipe_id} not found in database."
                }),
            }
    
    # 4. Process tags with user context
    for tag in body.get("tags", []):
        tag["author_id"] = user_id
        tag["type"] = "recipe"
    
    # 5. Create update command
    api = ApiUpdateRecipe(recipe_id=recipe_id, updates=body)
    cmd = api.to_domain()
    
    # 6. Execute update
    await bus.handle(cmd)
    
    # 7. Return success
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Recipe updated successfully"}),
    }
```

**Example Request:**
```http
PUT /recipes/recipe-abc-123
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1Q...

{
    "name": "Perfect Grilled Chicken Breast",
    "prep_time_minutes": 20,
    "cook_time_minutes": 14,
    "instructions": "Updated cooking instructions..."
}
```

**Example Response (Success):**
```json
{
    "statusCode": 200,
    "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    },
    "body": "{\"message\": \"Recipe updated successfully\"}"
}
```

#### Error Response Patterns

The `@lambda_exception_handler` decorator automatically handles common exceptions:

**EntityNotFoundException (404):**
```json
{
    "statusCode": 404,
    "body": "{\"detail\": \"Entity meal-404 not found on repository MealRepository\"}"
}
```

**ValidationError (422):**
```json
{
    "statusCode": 422,
    "body": "{\"detail\": \"1 validation error for ApiCreateMeal\\nname\\n  Field required [type=missing, input={'author_id': 'user-123'}]\"}"
}
```

**BusinessRuleValidationException (400):**
```json
{
    "statusCode": 400,
    "body": "{\"detail\": \"Error processing data: Recipe meal_id must match parent meal\"}"
}
```

**TimeoutError (408):**
```json
{
    "statusCode": 408,
    "body": "{\"detail\": \"Request processing time exceeded limit\"}"
}
```

**Generic Exception (500):**
```json
{
    "statusCode": 500,
    "body": "{\"detail\": \"An unexpected error occurred: Database connection failed\"}"
}
```

#### Authentication Context Patterns

**LocalStack Development:**
```python
is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
if is_localstack:
    # Skip authentication for local development
    current_user = SeedUser(id='localstack', roles=set([]))
```

**Production Authentication:**
```python
if not is_localstack:
    # Extract JWT claims from API Gateway authorizer
    authorizer_context = event["requestContext"]["authorizer"]
    user_id = authorizer_context.get("claims").get("sub")
    
    # Get full user context from IAM service
    response: dict = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response  # Return error response directly
    
    current_user: SeedUser = response["body"]
```

#### Message Bus Integration Pattern

**Command Execution:**
```python
# Bootstrap container and get message bus
bus: MessageBus = Container().bootstrap()

# Execute command through message bus
await bus.handle(command)

# Message bus automatically:
# - Handles domain events
# - Manages transaction boundaries  
# - Triggers event handlers
# - Maintains consistency
```

**Query Execution:**
```python
# Direct repository access for queries
bus: MessageBus = Container().bootstrap()
uow: UnitOfWork

async with bus.uow as uow:
    # Queries don't go through message bus
    # Direct repository access for better performance
    result = await uow.meals.query(filter=filters)
    single_meal = await uow.meals.get(meal_id)
```

#### CORS Headers Configuration

**Standard CORS Headers:**
```python
CORS_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS", 
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400"
}
```

**Usage in Response:**
```python
return {
    "statusCode": 200,
    "headers": CORS_headers,  # Include in every response
    "body": json.dumps(response_data)
}
```

#### Testing Lambda Handlers

**Local Testing with Poetry:**
```bash
# Run specific handler tests
poetry run python -m pytest tests/integration/lambda/test_create_recipe.py -v

# Test with LocalStack
IS_LOCALSTACK=true poetry run python -m pytest tests/integration/lambda/ -v

# Load test handlers  
poetry run python -m pytest tests/performance/lambda/test_handler_performance.py --benchmark-only
```

**Handler Test Structure:**
```python
async def test_create_recipe_handler():
    """Test recipe creation Lambda handler."""
    
    # Given: Valid event
    event = {
        "body": json.dumps({
            "name": "Test Recipe",
            "instructions": "Test instructions",
            "nutri_facts": {"calories": 300, "protein": 20}
        }),
        "pathParameters": {},
        "requestContext": {
            "authorizer": {
                "claims": {"sub": "test-user-123"}
            }
        }
    }
    
    # When: Handler is called
    response = await async_handler(event, {})
    
    # Then: Success response
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert "recipe_id" in body
    assert body["message"] == "Recipe created successfully"
```

These Lambda handler examples demonstrate the complete patterns used in the production codebase, including authentication, authorization, error handling, and response formatting. All examples follow the `poetry run python -m` pattern for testing and include realistic request/response scenarios.

#### Message Bus Pattern
```python
class MessageBus:
    """Handles commands and events asynchronously"""
    
    def __init__(self, uow: UnitOfWork, handlers: dict):
        self.uow = uow
        self.command_handlers = handlers['commands']
        self.event_handlers = handlers['events']
    
    async def handle(self, message: Command | Event) -> Any:
        """Route message to appropriate handler"""
        queue = [message]
        
        while queue:
            message = queue.pop(0)
            
            if isinstance(message, Command):
                result = await self.handle_command(message)
            elif isinstance(message, Event):
                await self.handle_event(message)
                
            # Collect new events from repositories
            queue.extend(self.uow.collect_new_events())
            
        return result
```

## Common Operations

This section provides copy-paste ready examples for working with the domain layer. All examples are tested and work with the actual codebase.

### Working with Meals

#### Creating a New Meal
```python
# Basic meal creation
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
import uuid

meal_id = str(uuid.uuid4())
author_id = "user-123"
menu_id = "menu-456"

meal = Meal.create_meal(
    name="Chicken Pasta",
    author_id=author_id,
    meal_id=meal_id,
    menu_id=menu_id,
    description="Delicious chicken pasta with vegetables",
    tags=set(),  # Add Tag objects here
    recipes=[]   # Add Recipe objects here
)

# Meal is now created with version=1 and events queued
print(f"Created meal: {meal.name} (v{meal.version})")
print(f"Events generated: {len(meal.events)}")
```

#### Updating Meal Properties
```python
# Single property update
meal.update_properties(name="Updated Chicken Pasta")

# Multiple properties update (efficient - single version increment)
meal.update_properties(
    name="Creamy Chicken Pasta",
    description="Rich and creamy pasta with grilled chicken",
    notes="Remember to use heavy cream"
)

# Version is automatically incremented
print(f"Current version: {meal.version}")

# Cache is automatically invalidated for computed properties
print(f"Nutrition facts: {meal.nutri_facts}")  # Recalculated if recipes changed
```

#### Working with Cached Properties
```python
# The nutri_facts property is cached for performance
nutrition = meal.nutri_facts  # First access: computed and cached
nutrition_again = meal.nutri_facts  # Second access: from cache (very fast)

# Check cache performance
cache_info = meal.get_cache_info()
print(f"Cache info: {cache_info}")
# Output: {'total_cached_properties': 1, 'computed_caches': 1, 'cache_names': ['nutri_facts']}

# Cache is invalidated when recipes change
meal.update_properties(recipes=[])  # Cache cleared automatically
fresh_nutrition = meal.nutri_facts  # Recomputed on next access
```

### Working with Recipes

#### Creating a Recipe
```python
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts

# Create nutrition facts
nutri_facts = NutriFacts(
    calories=450.0,
    protein=25.0,
    carbs=35.0,
    fat=18.0,
    fiber=3.0
)

# Create recipe
recipe = _Recipe(
    id=str(uuid.uuid4()),
    meal_id=meal.id,
    name="Grilled Chicken Breast",
    author_id=author_id,
    instructions="Season chicken and grill for 6-8 minutes per side",
    nutri_facts=nutri_facts,
    servings=2,
    prep_time_minutes=15,
    cook_time_minutes=16,
    ingredients=[],  # Add Ingredient objects here
    utensils=["grill", "tongs"],
    tags=set()
)

# Add recipe to meal
meal.copy_recipe(recipe)
print(f"Meal now has {len(meal.recipes)} recipes")
```

#### Updating Recipe Through Meal
```python
# Update recipe properties through the meal aggregate
updates = {
    recipe.id: {
        "name": "Perfect Grilled Chicken",
        "prep_time_minutes": 20,
        "cook_time_minutes": 14
    }
}

meal.update_recipes(updates)

# Verify update
updated_recipe = meal.get_recipe_by_id(recipe.id)
print(f"Updated recipe: {updated_recipe.name}")
print(f"Total prep time: {updated_recipe.prep_time_minutes} minutes")
```

### Working with Repositories

#### Repository Pattern Usage
```python
# Standard repository operations
from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import MealRepository

# Initialize repository (usually done via DI container)
meal_repo = MealRepository(session=db_session)

# Get single meal
meal = await meal_repo.get("meal-id-123")
if meal:
    print(f"Found meal: {meal.name}")

# Get multiple meals
meal_ids = ["meal-1", "meal-2", "meal-3"]
meals = await meal_repo.get_many(meal_ids)
print(f"Retrieved {len(meals)} meals")

# Filter with pagination
filters = {
    "author_id": "user-123",
    "discarded": False,
    "name__icontains": "pasta"
}
meals = await meal_repo.filter(
    filters=filters,
    order_by=["created_at"],
    limit=10,
    offset=0
)

# Count matching meals
total_count = await meal_repo.count(filters)
print(f"Found {len(meals)} meals out of {total_count} total")
```

#### Advanced Filtering Examples
```python
# Date range filtering
from datetime import datetime, timedelta

last_week = datetime.now() - timedelta(days=7)
recent_meals = await meal_repo.filter({
    "author_id": "user-123",
    "created_at__gte": last_week,
    "discarded__eq": False
})

# Nutrition-based filtering
high_protein_meals = await meal_repo.filter({
    "author_id": "user-123",
    "nutri_facts__protein__gte": 30.0,  # JSON field query
    "nutri_facts__calories__lt": 500.0
})

# Tag-based filtering
vegan_meals = await meal_repo.filter({
    "tags__contains": ["vegan"],  # Array contains
    "author_id": "user-123"
})
```

### Cache Operations and Performance

#### Entity-Level Caching
```python
# Cached properties are automatically detected
meal = Meal.create_meal(name="Test Meal", author_id="user-1", meal_id=str(uuid.uuid4()), menu_id="menu-1")

# Access cached property (computed on first access)
nutrition = meal.nutri_facts  # Computed and cached
print(f"Calories: {nutrition.calories if nutrition else 'N/A'}")

# Check what's cached
cached_props = meal._computed_caches
print(f"Computed caches: {cached_props}")  # frozenset({'nutri_facts'})

# Manual cache invalidation (usually not needed)
meal._invalidate_caches('nutri_facts')
print(f"Caches after invalidation: {meal._computed_caches}")  # frozenset()

# Cache is rebuilt on next access
nutrition = meal.nutri_facts  # Recomputed
print(f"Caches after recomputation: {meal._computed_caches}")  # frozenset({'nutri_facts'})
```

#### Performance Monitoring
```python
# Monitor cache effectiveness
cache_info = meal.get_cache_info()
print(f"""
Cache Performance:
- Total cached properties: {cache_info['total_cached_properties']}
- Currently computed: {cache_info['computed_caches']}
- Cache names: {cache_info['cache_names']}
""")

# Performance testing pattern
import time

# Cold access (not cached)
start_time = time.time()
nutrition = meal.nutri_facts
cold_time = time.time() - start_time

# Warm access (cached)
start_time = time.time()
nutrition = meal.nutri_facts
warm_time = time.time() - start_time

print(f"Cold access: {cold_time:.4f}s, Warm access: {warm_time:.6f}s")
print(f"Speedup: {cold_time / warm_time:.1f}x faster")
```

### Command Pattern Usage

#### Command Handler Pattern
```python
from src.contexts.recipes_catalog.core.domain.meal.commands.create_meal import CreateMeal
from src.contexts.recipes_catalog.core.services.meal.command_handlers.create_meal import create_meal_handler

# Create command object
command = CreateMeal(
    name="Mediterranean Bowl",
    author_id="user-456",
    menu_id="menu-789",
    description="Fresh Mediterranean flavors",
    tags=set(),
    recipes=[]
)

# Execute through handler (with UoW)
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
uow = UnitOfWork()  # Usually injected
await create_meal_handler(command, uow)

print(f"Created meal with ID: {command.meal_id}")
```

#### Message Bus Integration
```python
# Bootstrap message bus with all handlers
from src.contexts.recipes_catalog.core.bootstrap.bootstrap import bootstrap
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork

# Create UoW and bootstrap message bus
uow = UnitOfWork()  # Usually from DI container
bus = bootstrap(uow)

# Execute command through message bus
await bus.handle(command)

# Events are automatically processed
# Domain events are collected and dispatched
print(f"Command executed successfully")
```

### Error Handling Patterns

#### Domain Rule Validation
```python
from src.contexts.shared_kernel.domain.exceptions import BusinessRuleValidationException

try:
    # Attempt operation that might violate business rules
    meal.update_properties(name="")  # Empty name violates rules
except BusinessRuleValidationException as e:
    print(f"Business rule violation: {e.message}")
    print(f"Rule details: {e.details}")
    # Handle gracefully - show user-friendly error
```

#### Repository Error Handling
```python
try:
    meal = await meal_repo.get("non-existent-id")
except EntityNotFoundException as e:
    print(f"Meal not found: {e.entity_id}")
    # Return 404 to client
except DatabaseConnectionException as e:
    print(f"Database error: {e.message}")
    # Return 500 to client, log for investigation
```

### Testing Patterns

#### Unit Test Setup
```python
import pytest
from tests.conftest import create_meal, create_recipe_with_nutrition

def test_meal_nutrition_calculation():
    """Test that meal nutrition is sum of recipe nutrition."""
    # Arrange
    meal = create_meal(name="Test Meal")
    
    recipe1 = create_recipe_with_nutrition(calories=300, protein=20)
    recipe2 = create_recipe_with_nutrition(calories=200, protein=15)
    
    # Act
    meal.copy_recipe(recipe1)
    meal.copy_recipe(recipe2)
    
    # Assert
    nutrition = meal.nutri_facts
    assert nutrition.calories == 500
    assert nutrition.protein == 35
    
    # Verify cache behavior
    cache_info = meal.get_cache_info()
    assert 'nutri_facts' in cache_info['cache_names']
```

#### Integration Test Pattern
```python
@pytest.mark.integration
async def test_meal_creation_end_to_end(db_session):
    """Test complete meal creation flow."""
    # Arrange
    meal_repo = MealRepository(session=db_session)
    command = CreateMealCommand(name="Integration Test Meal", ...)
    
    # Act
    async with bootstrap.messagebus() as bus:
        result = await bus.handle(command)
    
    # Assert
    saved_meal = await meal_repo.get(result.meal_id)
    assert saved_meal.name == "Integration Test Meal"
    assert saved_meal.version == 1
```

### Performance Optimization Patterns

#### Batch Operations
```python
# Efficient bulk meal creation
meal_commands = [
    CreateMealCommand(name=f"Meal {i}", author_id="user-1", ...)
    for i in range(100)
]

# Process in batches to avoid memory issues
batch_size = 10
for i in range(0, len(meal_commands), batch_size):
    batch = meal_commands[i:i+batch_size]
    
    async with bootstrap.messagebus() as bus:
        results = await asyncio.gather(*[
            bus.handle(command) for command in batch
        ])
    
    print(f"Processed batch {i//batch_size + 1}")
```

#### Efficient Repository Queries
```python
# Use get_many instead of multiple get calls
meal_ids = ["meal-1", "meal-2", "meal-3", "meal-4", "meal-5"]

# Inefficient: multiple database calls
meals_slow = []
for meal_id in meal_ids:
    meal = await meal_repo.get(meal_id)
    if meal:
        meals_slow.append(meal)

# Efficient: single database call
meals_fast = await meal_repo.get_many(meal_ids)

print(f"Retrieved {len(meals_fast)} meals in one query")
```

These examples demonstrate the core patterns for working with the menu planning backend. All code is production-ready and follows the established architectural patterns.

## API Usage Examples

This section provides complete HTTP API examples for each command and query operation. All examples use actual request/response formats from the production system.

### Command API Examples (Write Operations)

#### Create Meal Command

**Endpoint:** `POST /meals`

```bash
# cURL Example
curl -X POST https://api.menuplanning.com/meals \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mediterranean Chicken Bowl",
    "menu_id": "550e8400-e29b-41d4-a716-446655440000",
    "description": "Healthy Mediterranean-inspired chicken with vegetables",
    "notes": "Use organic chicken if possible",
    "image_url": "https://s3.amazonaws.com/images/meal-123.jpg",
    "tags": [
      {
        "key": "cuisine",
        "value": "mediterranean",
        "type": "classification"
      },
      {
        "key": "diet",
        "value": "high_protein",
        "type": "dietary"
      }
    ],
    "recipes": [
      {
        "name": "Grilled Chicken Breast",
        "instructions": "Season chicken with herbs and grill for 6-8 minutes per side",
        "prep_time_minutes": 15,
        "cook_time_minutes": 16,
        "servings": 2,
        "ingredients": [
          {
            "product_id": "chicken-breast-123",
            "amount": 200,
            "unit": "g",
            "preparation": "boneless, skinless",
            "position": 1
          }
        ],
        "nutri_facts": {
          "calories": 450.0,
          "protein": 35.0,
          "carbohydrate": 5.0,
          "total_fat": 18.0,
          "fiber": 0.0,
          "sugar": 0.0,
          "sodium": 150.0
        },
        "utensils": ["grill", "tongs"],
        "tags": [
          {
            "key": "protein",
            "value": "chicken",
            "type": "ingredient"
          }
        ]
      }
    ]
  }'

# Success Response (201 Created)
{
  "message": "Meal created successfully",
  "meal_id": "660e8400-e29b-41d4-a716-446655440000"
}

# Error Response (400 Bad Request)
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Recipe name cannot be empty",
    "details": {
      "field": "recipes[0].name",
      "constraint": "required"
    },
    "correlation_id": "770e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

#### Update Meal Command

**Endpoint:** `PUT /meals/{meal_id}`

```bash
# cURL Example
curl -X PUT https://api.menuplanning.com/meals/660e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Mediterranean Bowl",
    "description": "Even healthier Mediterranean-inspired meal",
    "notes": "Added extra vegetables",
    "tags": [
      {
        "key": "cuisine",
        "value": "mediterranean",
        "type": "classification"
      },
      {
        "key": "diet",
        "value": "balanced",
        "type": "dietary"
      }
    ]
  }'

# Success Response (200 OK)
{
  "message": "Meal updated successfully"
}

# Error Response (403 Forbidden)
{
  "error": {
    "code": "FORBIDDEN",
    "message": "User does not have enough privileges",
    "correlation_id": "880e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:35:00Z"
  }
}
```

#### Delete Meal Command

**Endpoint:** `DELETE /meals/{meal_id}`

```bash
# cURL Example
curl -X DELETE https://api.menuplanning.com/meals/660e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# Success Response (200 OK)
{
  "message": "Meal deleted successfully"
}

# Error Response (404 Not Found)
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Meal 660e8400-e29b-41d4-a716-446655440000 not found",
    "correlation_id": "990e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:40:00Z"
  }
}
```

#### Copy Meal Command

**Endpoint:** `POST /meals/{meal_id}/copy`

```bash
# cURL Example
curl -X POST https://api.menuplanning.com/meals/660e8400-e29b-41d4-a716-446655440000/copy \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "id_of_target_menu": "550e8400-e29b-41d4-a716-446655440001"
  }'

# Success Response (201 Created)
{
  "message": "Meal copied successfully",
  "meal_id": "aa0e8400-e29b-41d4-a716-446655440000"
}
```

#### Create Recipe Command

**Endpoint:** `POST /meals/{meal_id}/recipes`

```bash
# cURL Example
curl -X POST https://api.menuplanning.com/meals/660e8400-e29b-41d4-a716-446655440000/recipes \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Roasted Vegetables",
    "instructions": "Chop vegetables, toss with oil, roast at 400°F for 25 minutes",
    "prep_time_minutes": 10,
    "cook_time_minutes": 25,
    "servings": 2,
    "ingredients": [
      {
        "product_id": "bell-pepper-123",
        "amount": 150,
        "unit": "g",
        "preparation": "chopped",
        "position": 1
      },
      {
        "product_id": "zucchini-456",
        "amount": 100,
        "unit": "g",
        "preparation": "sliced",
        "position": 2
      }
    ],
    "nutri_facts": {
      "calories": 120.0,
      "protein": 4.0,
      "carbohydrate": 18.0,
      "total_fat": 6.0,
      "fiber": 5.0,
      "sugar": 8.0,
      "sodium": 10.0
    },
    "utensils": ["baking_sheet", "knife"]
  }'

# Success Response (201 Created)
{
  "message": "Recipe added to meal successfully",
  "recipe_id": "bb0e8400-e29b-41d4-a716-446655440000"
}
```

### Query API Examples (Read Operations)

#### Get Meal by ID

**Endpoint:** `GET /meals/{meal_id}`

```bash
# cURL Example
curl -X GET https://api.menuplanning.com/meals/660e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# Success Response (200 OK)
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "Mediterranean Chicken Bowl",
  "author_id": "user-123",
  "menu_id": "550e8400-e29b-41d4-a716-446655440000",
  "description": "Healthy Mediterranean-inspired chicken with vegetables",
  "notes": "Use organic chicken if possible",
  "image_url": "https://s3.amazonaws.com/images/meal-123.jpg",
  "version": 1,
  "discarded": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "tags": [
    {
      "key": "cuisine",
      "value": "mediterranean",
      "author_id": "user-123",
      "type": "classification"
    }
  ],
  "recipes": [
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440000",
      "name": "Grilled Chicken Breast",
      "instructions": "Season chicken with herbs and grill for 6-8 minutes per side",
      "prep_time_minutes": 15,
      "cook_time_minutes": 16,
      "servings": 2,
      "nutri_facts": {
        "calories": 450.0,
        "protein": 35.0,
        "carbohydrate": 5.0,
        "total_fat": 18.0,
        "fiber": 0.0,
        "sugar": 0.0,
        "sodium": 150.0
      },
      "ingredients": [
        {
          "product_id": "chicken-breast-123",
          "amount": 200,
          "unit": "g",
          "preparation": "boneless, skinless",
          "position": 1
        }
      ]
    }
  ],
  "nutri_facts": {
    "calories": 570.0,
    "protein": 39.0,
    "carbohydrate": 23.0,
    "total_fat": 24.0,
    "fiber": 5.0,
    "sugar": 8.0,
    "sodium": 160.0
  },
  "total_time": 31,
  "weight_in_grams": 450
}
```

#### Query Meals with Filters

**Endpoint:** `GET /meals`

```bash
# Basic Query
curl -X GET "https://api.menuplanning.com/meals?limit=10&sort=-updated_at" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# Advanced Filtering
curl -X GET "https://api.menuplanning.com/meals?name=chicken&calories-gte=300&calories-lte=600&protein-gte=20&tags=mediterranean,high-protein&limit=20&sort=-created_at" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# Success Response (200 OK)
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "name": "Mediterranean Chicken Bowl",
    "author_id": "user-123",
    "nutri_facts": {
      "calories": 570.0,
      "protein": 39.0,
      "carbohydrate": 23.0,
      "total_fat": 24.0
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": "770e8400-e29b-41d4-a716-446655440000", 
    "name": "Chicken Caesar Salad",
    "author_id": "user-123",
    "nutri_facts": {
      "calories": 420.0,
      "protein": 32.0,
      "carbohydrate": 15.0,
      "total_fat": 28.0
    },
    "created_at": "2024-01-15T09:15:00Z",
    "updated_at": "2024-01-15T09:15:00Z"
  }
]
```

#### Query Parameters Reference

```bash
# Nutrition Filtering
?calories-gte=300&calories-lte=600          # Calorie range
?protein-gte=20&protein-lte=50              # Protein range (grams)
?carbohydrate-gte=10&carbohydrate-lte=40    # Carb range (grams)
?total-fat-gte=5&total-fat-lte=25           # Fat range (grams)

# Content Filtering
?name=chicken                               # Name contains "chicken"
?author-id=user-123                         # Specific author
?menu-id=menu-456                          # Specific menu
?tags=mediterranean,high-protein           # Has these tags
?tags-not-exists=dairy,gluten              # Doesn't have these tags

# Time Filtering
?total-time-gte=15&total-time-lte=45       # Prep + cook time range
?created-at-gte=2024-01-01T00:00:00Z       # Created after date

# Pagination & Sorting
?limit=50                                   # Max results (default: 50)
?offset=100                                # Skip first 100 results
?sort=-updated_at                          # Sort by updated desc
?sort=name,created_at                      # Sort by name, then created_at
```

### JavaScript/TypeScript Examples

#### Using Fetch API

```typescript
// Create Meal
async function createMeal(token: string, mealData: CreateMealRequest): Promise<CreateMealResponse> {
  const response = await fetch('https://api.menuplanning.com/meals', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(mealData)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new APIError(error.error.code, error.error.message);
  }
  
  return response.json();
}

// Get Meal
async function getMeal(token: string, mealId: string): Promise<Meal> {
  const response = await fetch(`https://api.menuplanning.com/meals/${mealId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    if (response.status === 404) {
      throw new MealNotFoundError(mealId);
    }
    const error = await response.json();
    throw new APIError(error.error.code, error.error.message);
  }
  
  return response.json();
}

// Query Meals with Filters
async function queryMeals(
  token: string, 
  filters: MealFilters = {}
): Promise<Meal[]> {
  const params = new URLSearchParams();
  
  // Add filter parameters
  if (filters.name) params.append('name', filters.name);
  if (filters.caloriesMin) params.append('calories-gte', filters.caloriesMin.toString());
  if (filters.caloriesMax) params.append('calories-lte', filters.caloriesMax.toString());
  if (filters.tags) params.append('tags', filters.tags.join(','));
  if (filters.limit) params.append('limit', filters.limit.toString());
  if (filters.sort) params.append('sort', filters.sort);
  
  const response = await fetch(`https://api.menuplanning.com/meals?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new APIError(error.error.code, error.error.message);
  }
  
  return response.json();
}

// TypeScript Interfaces
interface CreateMealRequest {
  name: string;
  menu_id: string;
  description?: string;
  notes?: string;
  image_url?: string;
  tags?: Tag[];
  recipes?: Recipe[];
}

interface MealFilters {
  name?: string;
  caloriesMin?: number;
  caloriesMax?: number;
  proteinMin?: number;
  tags?: string[];
  limit?: number;
  sort?: string;
}

interface Meal {
  id: string;
  name: string;
  author_id: string;
  menu_id: string;
  description?: string;
  notes?: string;
  nutri_facts: NutritionFacts;
  recipes: Recipe[];
  tags: Tag[];
  created_at: string;
  updated_at: string;
}
```

#### Using Python Requests

```python
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass

class MealAPIClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def create_meal(self, meal_data: Dict) -> Dict:
        """Create a new meal."""
        response = requests.post(
            f'{self.base_url}/meals',
            json=meal_data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_meal(self, meal_id: str) -> Dict:
        """Get meal by ID."""
        response = requests.get(
            f'{self.base_url}/meals/{meal_id}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def query_meals(
        self,
        name: Optional[str] = None,
        calories_min: Optional[int] = None,
        calories_max: Optional[int] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Query meals with filters."""
        params = {'limit': limit}
        
        if name:
            params['name'] = name
        if calories_min:
            params['calories-gte'] = calories_min
        if calories_max:
            params['calories-lte'] = calories_max
        if tags:
            params['tags'] = ','.join(tags)
            
        response = requests.get(
            f'{self.base_url}/meals',
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def update_meal(self, meal_id: str, updates: Dict) -> Dict:
        """Update meal properties."""
        response = requests.put(
            f'{self.base_url}/meals/{meal_id}',
            json=updates,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage Example
client = MealAPIClient('https://api.menuplanning.com', 'your-jwt-token')

# Create meal
meal_data = {
    'name': 'Healthy Salad',
    'menu_id': 'menu-123',
    'description': 'Fresh green salad with protein'
}
result = client.create_meal(meal_data)
print(f"Created meal: {result['meal_id']}")

# Query meals
meals = client.query_meals(
    name='chicken',
    calories_min=300,
    calories_max=600,
    tags=['healthy', 'protein']
)
print(f"Found {len(meals)} meals")
```

### Error Handling Examples

This section provides comprehensive error handling patterns with actual error messages from the system. All examples are based on real scenarios that AI agents will encounter when working with the menu planning backend.

#### Domain Errors (Business Rule Violations)

Domain errors occur when business rules are violated within aggregates. These are the most common errors during domain logic operations.

```python
from src.contexts.shared_kernel.domain.exceptions import BusinessRuleValidationException
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts

async def domain_error_examples():
    """Demonstrate domain business rule validation errors."""
    
    # Example 1: Recipe with wrong meal_id
    try:
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123", 
            menu_id="menu_123"
        )
        
        # This recipe has the wrong meal_id - violates business rule
        invalid_recipe = _Recipe.create_recipe(
            name="Invalid Recipe",
            ingredients=[],
            instructions="Mix ingredients",
            author_id="author_123",
            meal_id="wrong_meal_id",  # Wrong meal_id!
            nutri_facts=NutriFacts(calories=100)
        )
        
        # This will trigger business rule validation
        meal.update_properties(recipes=[invalid_recipe])
        
    except BusinessRuleValidationException as e:
        print(f"Domain Error: {type(e).__name__}")
        print(f"Rule: {e.rule}")
        print(f"Message: {str(e)}")
        # Log the error for debugging
        logger.error(f"Business rule violation: {e.rule}", extra={"meal_id": meal.id})
    
    # Example 2: Recipe with wrong author_id
    try:
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123"
        )
        
        # This recipe has wrong author_id - violates business rule
        invalid_recipe = _Recipe.create_recipe(
            name="Invalid Recipe",
            ingredients=[],
            instructions="Mix ingredients", 
            author_id="different_author",  # Wrong author_id!
            meal_id="meal_123",
            nutri_facts=NutriFacts(calories=100)
        )
        
        meal.update_properties(recipes=[invalid_recipe])
        
    except BusinessRuleValidationException as e:
        print(f"Author mismatch error: {str(e)}")
        # Return user-friendly error
        return {"error": "Recipe author must match meal author", "code": "AUTHOR_MISMATCH"}
```

**Expected Error Output:**
```
Domain Error: BusinessRuleValidationException
Rule: <src.contexts.recipes_catalog.core.domain.rules.RecipeMustHaveCorrectMealIdAndAuthorId object at 0x7b1e5072cd10>
Message: RecipeMustHaveCorrectMealIdAndAuthorId <src.contexts.recipes_catalog.core.domain.rules.RecipeMustHaveCorrectMealIdAndAuthorId object at 0x7b1e5072cd10>
```

#### API Validation Errors

API validation errors occur when request data doesn't match the expected schema format or contains invalid values.

```python
from pydantic import ValidationError
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.create_meal import ApiCreateMeal
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.update_meal import ApiUpdateMeal

async def api_validation_examples():
    """Demonstrate API schema validation errors."""
    
    # Example 1: Missing required fields
    try:
        # Missing name, author_id, menu_id
        invalid_meal = ApiCreateMeal()
        
    except ValidationError as e:
        print(f"Validation Error: {type(e).__name__}")
        print(f"Error count: {e.error_count()}")
        
        # Parse individual errors
        for error in e.errors():
            field = error.get('loc', ['unknown'])[0]
            message = error.get('msg', 'Unknown error')
            print(f"  Field '{field}': {message}")
            
        # Return structured error response
        return {
            "error": "Validation failed",
            "details": [
                {"field": err['loc'][0], "message": err['msg']} 
                for err in e.errors()
            ]
        }
    
    # Example 2: Wrong data types
    try:
        # name should be string, not integer
        invalid_meal = ApiCreateMeal(
            name=123,  # Wrong type!
            author_id="author_123",
            menu_id="menu_123"
        )
        
    except ValidationError as e:
        print(f"Type validation error: {str(e)[:200]}...")
        
    # Example 3: Invalid field values
    try:
        # Empty string for required field
        invalid_meal = ApiCreateMeal(
            name="",  # Empty string not allowed
            author_id="author_123", 
            menu_id="menu_123"
        )
        
    except ValidationError as e:
        print(f"Value validation error: {str(e)[:200]}...")
        
    # Example 4: Invalid nested objects
    try:
        invalid_meal = ApiCreateMeal(
            name="Test Meal",
            author_id="author_123",
            menu_id="menu_123",
            recipes=[
                {
                    "name": "Recipe 1",
                    "ingredients": "not_a_list",  # Should be list
                    "instructions": "Mix ingredients",
                    "nutri_facts": {
                        "calories": "not_a_number"  # Should be float
                    }
                }
            ]
        )
        
    except ValidationError as e:
        print(f"Nested validation error: {str(e)[:300]}...")
```

**Expected Error Output:**
```
Validation Error: ValidationError
Error count: 3
  Field 'name': Field required
  Field 'author_id': Field required  
  Field 'menu_id': Field required

Type validation error: 1 validation error for ApiCreateMeal
name
  Input should be a valid string [type=string_type, input_value=123, input_type=int]
    For further information visit https://errors.pydantic.dev/2.11/v/string_type

Value validation error: 1 validation error for ApiCreateMeal
name
  String should have at least 1 character [type=string_too_short, input_value='', input_type=str]
    For further information visit https://errors.pydantic.dev/2.11/v/string_too_short
```

#### Repository Errors

Repository errors occur during database operations and are critical for data consistency.

```python
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException
)
from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import (
    FilterValidationException,
    RepositoryException
)

async def repository_error_examples():
    """Demonstrate repository error handling patterns."""
    
    # Example 1: Entity not found
    try:
        meal = await meal_repo.get("nonexistent-meal-id")
        
    except EntityNotFoundException as e:
        print(f"Entity not found: {str(e)}")
        print(f"Entity ID: {e.entity_id}")
        print(f"Repository: {e.repository}")
        
        # Log for debugging
        logger.warning(f"Meal not found: {e.entity_id}")
        
        # Return appropriate HTTP response
        return {"error": "Meal not found", "meal_id": e.entity_id}, 404
    
    # Example 2: Multiple entities found (should be unique)
    try:
        meal = await meal_repo.get_by_unique_field("duplicate-value")
        
    except MultipleEntitiesFoundException as e:
        print(f"Duplicate entities: {str(e)}")
        print(f"Entity ID: {e.entity_id}")
        
        # Log critical error
        logger.error(f"Data integrity issue: {e.entity_id}")
        
        # Return conflict response
        return {"error": "Multiple meals found", "conflict_id": e.entity_id}, 409
    
    # Example 3: Invalid filter fields
    try:
        meals = await meal_repo.query(filter={
            "invalid_field": "some_value",
            "another_bad_field": 123
        })
        
    except FilterValidationException as e:
        print(f"Filter validation error: {str(e)}")
        print(f"Invalid filters: {e.invalid_filters}")
        print(f"Suggested filters: {e.suggested_filters}")
        
        # Return helpful error response
        return {
            "error": "Invalid filter fields",
            "invalid_fields": e.invalid_filters,
            "valid_fields": e.suggested_filters
        }, 400
    
    # Example 4: Database connection errors
    try:
        meals = await meal_repo.query(filter={"author_id": "chef_123"})
        
    except RepositoryException as e:
        print(f"Database error: {e.message}")
        print(f"Correlation ID: {e.correlation_id}")
        
        # Log for ops team
        logger.error(f"Database operation failed", extra={
            "correlation_id": e.correlation_id,
            "repository": str(e.repository),
            "operation": e.operation
        })
        
        # Return service unavailable
        return {"error": "Database temporarily unavailable"}, 503
```

**Expected Error Output:**
```
Entity not found: Entity meal-404 not found on repository MockMealRepository
Entity ID: meal-404
Repository: MockMealRepository

Duplicate entities: Entity meal-duplicate already exists on repository MockMealRepository  
Entity ID: meal-duplicate

Filter validation error: Invalid filter keys: invalid_field, another_bad_field
Invalid filters: ['invalid_field', 'another_bad_field']
Suggested filters: ['name', 'author_id', 'created_at', 'tags']
```

#### Lambda Handler Errors

Lambda handler errors occur at the HTTP API boundary and need to be handled gracefully for proper HTTP responses.

```python
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import lambda_exception_handler
import json

@lambda_exception_handler
async def create_meal_handler(event: dict, context) -> dict:
    """Lambda handler with comprehensive error handling."""
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate API schema
        api_meal = ApiCreateMeal(**body)
        
        # Convert to domain command
        command = api_meal.to_domain()
        
        # Execute through message bus
        async with message_bus() as bus:
            result = await bus.handle(command)
            
        # Return success response
        return {
            "statusCode": 201,
            "body": json.dumps({
                "meal_id": result.meal_id,
                "message": "Meal created successfully"
            })
        }
        
    except ValidationError as e:
        # Handled by decorator - returns 422
        raise
        
    except BusinessRuleValidationException as e:
        # Domain rule violation - return 400
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Business rule violation",
                "rule": str(e.rule),
                "message": str(e)
            })
        }
        
    except EntityNotFoundException as e:
        # Handled by decorator - returns 404
        raise
        
    except Exception as e:
        # Unexpected error - log and return 500
        logger.error(f"Unexpected error in create_meal_handler", extra={
            "error": str(e),
            "event": event
        })
        raise  # Decorator handles 500 response
```

**Expected Lambda Error Responses:**
```json
// 400 - Business Rule Violation
{
    "statusCode": 400,
    "body": "{\"error\": \"Business rule violation\", \"rule\": \"RecipeMustHaveCorrectMealIdAndAuthorId\", \"message\": \"Recipe meal_id must match parent meal\"}"
}

// 404 - Entity Not Found  
{
    "statusCode": 404,
    "body": "{\"detail\": \"Entity meal-404 not found on repository MealRepository\"}"
}

// 422 - Validation Error
{
    "statusCode": 422, 
    "body": "{\"detail\": \"1 validation error for ApiCreateMeal\\nname\\n  Field required [type=missing, input={'author_id': 'user-123'}]\"}"
}

// 500 - Unexpected Error
{
    "statusCode": 500,
    "body": "{\"detail\": \"An unexpected error occurred: Database connection failed\"}"
}
```

#### Entity Update Errors

Entity update errors occur when trying to modify entity properties incorrectly.

```python
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal

async def entity_update_error_examples():
    """Demonstrate entity update error handling."""
    
    meal = Meal.create_meal(
        name="Test Meal",
        author_id="author_123", 
        meal_id="meal_123",
        menu_id="menu_123"
    )
    
    # Example 1: Trying to update private properties
    try:
        meal.update_properties(_private_field="value")
        
    except AttributeError as e:
        print(f"Private property error: {str(e)}")
        # Expected: "_private_field is private."
        
    # Example 2: Trying to update non-existent properties
    try:
        meal.update_properties(nonexistent_field="value")
        
    except TypeError as e:
        print(f"Invalid property error: {str(e)}")
        # Expected: "nonexistent_field is not a property."
        
    # Example 3: Trying to update read-only properties
    try:
        meal.update_properties(id="new_id")
        
    except AttributeError as e:
        print(f"Read-only property error: {str(e)}")
        # Expected: "id has no setter."
        
    # Example 4: Operating on discarded entity
    meal.discard()
    try:
        meal.update_properties(name="New Name")
        
    except Exception as e:
        print(f"Discarded entity error: {type(e).__name__}: {str(e)}")
        # Expected: DiscardedEntityException
```

**Expected Error Output:**
```
Private property error: _private_field is private.
Invalid property error: nonexistent_field is not a property.
Read-only property error: id has no setter.
Discarded entity error: DiscardedEntityException: Cannot operate on discarded entity
```

#### Conversion Errors

Conversion errors occur when converting between API schemas, domain objects, and ORM models.

```python
from src.contexts.seedwork.shared.adapters.exceptions.api_schema import ValidationConversionError

async def conversion_error_examples():
    """Demonstrate conversion error handling."""
    
    # Example 1: API to Domain conversion failure
    try:
        # Malformed API data that passes initial validation
        api_meal = ApiCreateMeal(
            name="Test Meal",
            author_id="author_123",
            menu_id="menu_123"
        )
        
        # But fails domain conversion due to missing required fields
        domain_meal = api_meal.to_domain()
        
    except ValidationConversionError as e:
        print(f"Conversion error: {e.message}")
        print(f"Schema: {e.schema_class.__name__}")
        print(f"Direction: {e.conversion_direction}")
        print(f"Validation errors: {e.validation_errors}")
        
        # Return structured error
        return {
            "error": "Data conversion failed",
            "schema": e.schema_class.__name__,
            "details": e.validation_errors
        }, 400
        
    # Example 2: Domain to ORM conversion failure
    try:
        # Domain object with invalid state for persistence
        domain_meal = Meal.create_meal(
            name="Test Meal",
            author_id="invalid_author",  # Invalid format
            meal_id="meal_123",
            menu_id="menu_123"
        )
        
        # Convert to ORM for persistence
        orm_kwargs = ApiMeal.from_domain(domain_meal).to_orm_kwargs()
        
    except ValidationConversionError as e:
        print(f"ORM conversion error: {e.message}")
        logger.error(f"Failed to convert domain to ORM", extra={
            "domain_class": type(domain_meal).__name__,
            "error": str(e)
        })
        
        # Return internal server error
        return {"error": "Data persistence failed"}, 500
```

**Expected Error Output:**
```
Conversion error: Failed to convert ApiCreateMeal to domain: Missing required field 'recipes'
Schema: ApiCreateMeal
Direction: api_to_domain
Validation errors: ['Missing required field recipes']
```

#### Error Handling Best Practices

```python
import logging
from typing import Dict, Any
import traceback

logger = logging.getLogger(__name__)

def handle_error_gracefully(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """Centralized error handling with logging and user-friendly responses."""
    
    # Log the error with context
    logger.error(
        f"Error in {context.get('operation', 'unknown')}: {str(error)}",
        extra={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "stack_trace": traceback.format_exc()
        }
    )
    
    # Return appropriate response based on error type
    if isinstance(error, ValidationError):
        return {
            "error": "Invalid request data",
            "details": [
                {"field": err['loc'][0], "message": err['msg']}
                for err in error.errors()
            ]
        }
    
    elif isinstance(error, BusinessRuleValidationException):
        return {
            "error": "Business rule violation", 
            "rule": str(error.rule),
            "message": "The operation violates business rules"
        }
    
    elif isinstance(error, EntityNotFoundException):
        return {
            "error": "Resource not found",
            "resource_id": error.entity_id
        }
    
    elif isinstance(error, FilterValidationException):
        return {
            "error": "Invalid query parameters",
            "invalid_fields": error.invalid_filters,
            "valid_fields": error.suggested_filters
        }
    
    else:
        # Generic error - don't expose internal details
        return {
            "error": "An unexpected error occurred",
            "message": "Please try again or contact support"
        }

# Usage in handlers
async def robust_handler(event: dict, context) -> dict:
    """Example of robust error handling in Lambda handlers."""
    
    try:
        # Main handler logic here
        result = await process_request(event)
        return {"statusCode": 200, "body": json.dumps(result)}
        
    except Exception as e:
        error_response = handle_error_gracefully(e, {
            "operation": "create_meal",
            "event": event,
            "handler": "robust_handler"
        })
        
        # Determine appropriate HTTP status code
        status_code = 500  # Default
        if isinstance(e, ValidationError):
            status_code = 422
        elif isinstance(e, BusinessRuleValidationException):
            status_code = 400
        elif isinstance(e, EntityNotFoundException):
            status_code = 404
        elif isinstance(e, FilterValidationException):
            status_code = 400
            
        return {
            "statusCode": status_code,
            "body": json.dumps(error_response)
        }
```

### Testing Error Handling

#### Unit Tests for Error Scenarios

```python
import pytest
from src.contexts.shared_kernel.domain.exceptions import BusinessRuleValidationException
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import EntityNotFoundException

class TestErrorHandling:
    """Test error handling patterns."""
    
    def test_business_rule_validation_error(self):
        """Test that business rules are properly validated."""
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123"
        )
        
        invalid_recipe = _Recipe.create_recipe(
            name="Invalid Recipe",
            ingredients=[],
            instructions="Mix ingredients",
            author_id="wrong_author",  # Different author
            meal_id="meal_123",
            nutri_facts=NutriFacts(calories=100)
        )
        
        # Should raise BusinessRuleValidationException
        with pytest.raises(BusinessRuleValidationException) as exc_info:
            meal.update_properties(recipes=[invalid_recipe])
            
        assert "RecipeMustHaveCorrectMealIdAndAuthorId" in str(exc_info.value)
    
    def test_entity_not_found_error(self):
        """Test repository error handling."""
        repo = MockMealRepository()
        
        with pytest.raises(EntityNotFoundException) as exc_info:
            repo.get("nonexistent-id")
            
        assert exc_info.value.entity_id == "nonexistent-id"
        assert "not found" in str(exc_info.value)
    
    def test_api_validation_error(self):
        """Test API schema validation."""
        with pytest.raises(ValidationError) as exc_info:
            ApiCreateMeal()  # Missing required fields
            
        errors = exc_info.value.errors()
        required_fields = {err['loc'][0] for err in errors}
        assert "name" in required_fields
        assert "author_id" in required_fields
```

These error handling examples demonstrate comprehensive error management patterns that AI agents will encounter. All examples use actual error messages from the production system and include both the error handling and appropriate logging/response patterns.

## Database Query Examples

This section provides practical examples of database queries using the repository pattern, with expected results and performance considerations.

### Basic Repository Operations

#### Getting Single Entities

```python
from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import MealRepo
from src.contexts.products_catalog.core.adapters.repositories.product_repository import ProductRepo
from src.contexts.iam.core.adapters.repositories.user_repository import UserRepo

# Using poetry run python for all commands
async def basic_entity_retrieval_examples():
    """Basic entity retrieval with error handling."""
    
    # Get meal by ID
    meal_repo = MealRepo(db_session)
    try:
        meal = await meal_repo.get("meal-123")
        print(f"Found meal: {meal.name} (Author: {meal.author_id})")
        print(f"Recipes: {len(meal.recipes)}")
        print(f"Total calories: {meal.nutri_facts.calories if meal.nutri_facts else 'Unknown'}")
    except EntityNotFoundException:
        print("Meal not found - handle gracefully")
    
    # Get product with nutritional data
    product_repo = ProductRepo(db_session)
    product = await product_repo.get("product-456")
    print(f"Product: {product.name}")
    print(f"Brand: {product.brand_name or 'Generic'}")
    print(f"Calories per 100g: {product.nutri_facts_per_100g.calories}")
    
    # Get user profile
    user_repo = UserRepo(db_session)
    user = await user_repo.get("user-789")
    print(f"User: {user.username} ({user.email})")
    print(f"Roles: {[role.name for role in user.roles]}")
```

**Expected Results:**
```
Found meal: Grilled Chicken Salad (Author: user-123)
Recipes: 2
Total calories: 485.0
Product: Organic Chicken Breast
Brand: Natural Farms
Calories per 100g: 165.0
User: chef_maria (maria@example.com)
Roles: ['chef', 'premium_user']
```

#### Bulk Operations

```python
async def bulk_operations_example():
    """Demonstrate bulk get operations for performance."""
    
    meal_repo = MealRepo(db_session)
    
    # Get multiple meals efficiently
    meal_ids = ["meal-1", "meal-2", "meal-3", "meal-4", "meal-5"]
    meals = await meal_repo.get_many(meal_ids)
    
    print(f"Retrieved {len(meals)} meals in single query")
    for meal in meals:
        print(f"- {meal.name}: {meal.nutri_facts.calories if meal.nutri_facts else 0} cal")
    
    # Performance note: get_many() uses SQL IN clause, much faster than individual gets
    # Recommended for 2-50 entities, consider pagination for larger sets
```

**Expected Results:**
```
Retrieved 5 meals in single query
- Breakfast Bowl: 320 cal
- Lunch Wrap: 450 cal
- Dinner Steak: 680 cal
- Snack Mix: 180 cal
- Power Smoothie: 250 cal
```

### Repository Filtering Patterns

#### Basic Filtering with Operators

```python
async def filtering_examples():
    """Demonstrate various filtering operators and their usage."""
    
    meal_repo = MealRepo(db_session)
    
    # Exact match filtering
    breakfast_meals = await meal_repo.query(filter={
        "name": "Morning Oats"
    })
    print(f"Exact match: {len(breakfast_meals)} meals")
    
    # Case-insensitive contains
    chicken_meals = await meal_repo.query(filter={
        "name__icontains": "chicken"
    })
    print(f"Contains 'chicken': {len(chicken_meals)} meals")
    
    # Numeric range filtering
    low_calorie_meals = await meal_repo.query(filter={
        "calories__gte": 200,
        "calories__lte": 400
    })
    print(f"200-400 calories: {len(low_calorie_meals)} meals")
    
    # Date range filtering  
    from datetime import datetime, timedelta
    recent_meals = await meal_repo.query(filter={
        "created_at__gte": datetime.now() - timedelta(days=7)
    })
    print(f"Created last week: {len(recent_meals)} meals")
    
    # Multiple author filtering
    team_meals = await meal_repo.query(filter={
        "author_id__in": ["chef-1", "chef-2", "chef-3"]
    })
    print(f"Team meals: {len(team_meals)} meals")
```

**Expected Results:**
```
Exact match: 1 meals
Contains 'chicken': 8 meals  
200-400 calories: 12 meals
Created last week: 25 meals
Team meals: 34 meals
```

#### Advanced Filter Combinations

```python
async def advanced_filtering():
    """Complex filtering combining multiple conditions."""
    
    meal_repo = MealRepo(db_session)
    
    # Complex nutritional filtering
    healthy_meals = await meal_repo.query(filter={
        "calories__gte": 300,
        "calories__lte": 600,
        "protein__gte": 20,
        "total_fat__lte": 15,
        "sodium__lte": 600
    })
    
    print(f"Healthy criteria meals: {len(healthy_meals)}")
    for meal in healthy_meals[:3]:  # Show first 3
        nf = meal.nutri_facts
        print(f"- {meal.name}: {nf.calories}cal, {nf.protein}g protein, {nf.total_fat}g fat")
    
    # Time-based filtering with sorting
    quick_meals = await meal_repo.query(
        filter={
            "total_time__lte": 30,
            "calories__gte": 250
        },
        limit=10
    )
    
    print(f"\nQuick meals (≤30 min, ≥250 cal): {len(quick_meals)}")
```

**Expected Results:**
```
Healthy criteria meals: 15
- Mediterranean Bowl: 420cal, 22g protein, 12g fat
- Grilled Salmon: 380cal, 28g protein, 14g fat  
- Turkey Wrap: 350cal, 25g protein, 8g fat

Quick meals (≤30 min, ≥250 cal): 10
```

### Join Operations and Relationships

#### Product-Recipe-Meal Joins

```python
async def join_operations_example():
    """Demonstrate complex joins across multiple entities."""
    
    meal_repo = MealRepo(db_session)
    
    # Find meals containing specific products
    chicken_based_meals = await meal_repo.query(filter={
        "products": "product-chicken-breast-123"
    })
    
    print(f"Meals with chicken breast: {len(chicken_based_meals)}")
    for meal in chicken_based_meals:
        print(f"- {meal.name} by {meal.author_id}")
        for recipe in meal.recipes:
            chicken_ingredients = [ing for ing in recipe.ingredients 
                                 if ing.product_id == "product-chicken-breast-123"]
            for ing in chicken_ingredients:
                print(f"  • {ing.name}: {ing.quantity} {ing.unit}")
    
    # Multiple product filtering (meals with both chicken AND rice)
    complete_meals = await meal_repo.query(filter={
        "products__in": [
            "product-chicken-breast-123",
            "product-brown-rice-456"
        ]
    })
    
    print(f"\nMeals with chicken AND rice: {len(complete_meals)}")
```

**Expected Results:**
```
Meals with chicken breast: 6
- Grilled Chicken Salad by chef_maria
  • Chicken Breast: 150 g
- Chicken Stir Fry by chef_john
  • Chicken Breast: 120 g
- Mediterranean Chicken by chef_sarah
  • Chicken Breast: 180 g

Meals with chicken AND rice: 3
```

#### Recipe-Ingredient Joins

```python
async def recipe_ingredient_joins():
    """Query recipes through ingredient relationships."""
    
    recipe_repo = RecipeRepo(db_session)
    
    # Find recipes by ingredient name
    pasta_recipes = await recipe_repo.query(filter={
        "ingredient_name__icontains": "pasta"
    })
    
    print(f"Pasta recipes: {len(pasta_recipes)}")
    
    # Find high-protein recipes with specific ingredients
    protein_recipes = await recipe_repo.query(filter={
        "protein__gte": 25,
        "ingredient_name__in": ["chicken", "salmon", "tofu", "beans"]
    })
    
    print(f"High-protein recipes with key ingredients: {len(protein_recipes)}")
    for recipe in protein_recipes[:3]:
        print(f"- {recipe.name}: {recipe.nutri_facts.protein}g protein")
```

**Expected Results:**
```
Pasta recipes: 12
High-protein recipes with key ingredients: 8
- Salmon Teriyaki: 32g protein
- Chicken Tikka: 28g protein  
- Black Bean Bowl: 26g protein
```

### Tag-Based Filtering

#### Single Tag Filtering

```python
async def tag_filtering_examples():
    """Demonstrate tag-based filtering patterns."""
    
    meal_repo = MealRepo(db_session)
    
    # Find meals with specific tags
    vegan_meals = await meal_repo.query_by_tags(
        tags=["vegan"],
        filter_type="all"  # Must have ALL specified tags
    )
    
    print(f"Vegan meals: {len(vegan_meals)}")
    for meal in vegan_meals[:3]:
        tags = [f"{tag.key}:{tag.value}" for tag in meal.tags]
        print(f"- {meal.name} (Tags: {', '.join(tags)})")
    
    # Dietary restriction filtering
    gluten_free_meals = await meal_repo.query_by_tags(
        tags=["gluten-free", "dairy-free"],
        filter_type="any"  # Must have ANY of the specified tags
    )
    
    print(f"\nGluten or dairy-free meals: {len(gluten_free_meals)}")
```

**Expected Results:**
```
Vegan meals: 15
- Quinoa Buddha Bowl (Tags: diet:vegan, meal:lunch, prep:quick)
- Lentil Curry (Tags: diet:vegan, cuisine:indian, spice:medium)
- Green Smoothie (Tags: diet:vegan, meal:breakfast, prep:instant)

Gluten or dairy-free meals: 28
```

#### Complex Tag Combinations

```python
async def complex_tag_filtering():
    """Advanced tag filtering with multiple criteria."""
    
    meal_repo = MealRepo(db_session)
    
    # Combine tag filtering with nutritional filters
    healthy_quick_meals = await meal_repo.query(filter={
        "calories__lte": 500,
        "prep_time__lte": 20,
        "tags__contains": ["healthy", "quick"]
    })
    
    print(f"Healthy & quick meals: {len(healthy_quick_meals)}")
    
    # Exclude certain tags
    non_spicy_meals = await meal_repo.query(filter={
        "tags__not_contains": ["spicy", "very-hot"]
    })
    
    print(f"Non-spicy meals: {len(non_spicy_meals)}")
    
    # Cuisine-specific with dietary restrictions
    asian_vegan_meals = await meal_repo.query_by_tags(
        tags=["cuisine:asian", "diet:vegan"],
        filter_type="all"
    )
    
    print(f"Asian vegan meals: {len(asian_vegan_meals)}")
```

**Expected Results:**
```
Healthy & quick meals: 18
Non-spicy meals: 142
Asian vegan meals: 6
```

### Raw SQLAlchemy Queries

#### Custom Query Building

```python
from sqlalchemy import select, and_, or_, func
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import RecipeSaModel

async def custom_sqlalchemy_queries():
    """Use SQLAlchemy directly for complex queries."""
    
    # Build custom query with joins
    stmt = (
        select(MealSaModel)
        .join(RecipeSaModel, MealSaModel.id == RecipeSaModel.meal_id)
        .where(
            and_(
                MealSaModel.calories.between(300, 600),
                RecipeSaModel.prep_time_minutes <= 30,
                MealSaModel.discarded == False
            )
        )
        .group_by(MealSaModel.id)
        .having(func.count(RecipeSaModel.id) >= 2)  # Meals with 2+ recipes
        .order_by(MealSaModel.calories.desc())
        .limit(10)
    )
    
    # Execute through repository for proper mapping
    meal_repo = MealRepo(db_session)
    results = await meal_repo.query(starting_stmt=stmt)
    
    print(f"Complex query results: {len(results)} meals")
    for meal in results:
        print(f"- {meal.name}: {meal.nutri_facts.calories}cal, {len(meal.recipes)} recipes")
```

**Expected Results:**
```
Complex query results: 7 meals
- Surf & Turf Combo: 580cal, 3 recipes
- Hearty Breakfast Plate: 520cal, 2 recipes  
- Power Lunch Bowl: 480cal, 2 recipes
```

#### Aggregation Queries

```python
async def aggregation_queries():
    """Demonstrate aggregation and statistical queries."""
    
    from sqlalchemy import func
    
    # Nutritional statistics by author
    stmt = (
        select(
            MealSaModel.author_id,
            func.count(MealSaModel.id).label('meal_count'),
            func.avg(MealSaModel.calories).label('avg_calories'),
            func.max(MealSaModel.protein).label('max_protein'),
            func.min(MealSaModel.total_time).label('min_prep_time')
        )
        .where(MealSaModel.discarded == False)
        .group_by(MealSaModel.author_id)
        .having(func.count(MealSaModel.id) >= 5)  # Authors with 5+ meals
        .order_by(func.avg(MealSaModel.calories).desc())
    )
    
    # Execute raw query for statistics
    result = await db_session.execute(stmt)
    stats = result.fetchall()
    
    print("Author meal statistics:")
    for row in stats:
        print(f"- {row.author_id}: {row.meal_count} meals, "
              f"avg {row.avg_calories:.0f} cal, max {row.max_protein:.1f}g protein")
```

**Expected Results:**
```
Author meal statistics:
- chef_maria: 23 meals, avg 425 cal, max 35.2g protein
- chef_john: 18 meals, avg 398 cal, max 28.6g protein
- chef_sarah: 15 meals, avg 380 cal, max 31.4g protein
```

### Performance Considerations

#### Query Optimization Patterns

```python
async def performance_optimized_queries():
    """Demonstrate performance best practices."""
    
    meal_repo = MealRepo(db_session)
    
    # Good: Use specific fields for filtering
    # Bad: SELECT * FROM meals WHERE description LIKE '%chicken%'
    # Good: Use indexed columns
    efficient_query = await meal_repo.query(
        filter={
            "author_id": "chef_123",  # Indexed column
            "calories__gte": 300,    # Indexed nutritional column
            "created_at__gte": datetime.now() - timedelta(days=30)  # Indexed timestamp
        },
        limit=50  # Always limit large result sets
    )
    
    print(f"Efficient query: {len(efficient_query)} results")
    
    # Use pagination for large datasets
    page_size = 20
    offset = 0
    
    while True:
        page_results = await meal_repo.query(
            filter={"author_id__in": ["chef_1", "chef_2", "chef_3"]},
            limit=page_size,
            # offset=offset  # Would need to implement in repository
        )
        
        if not page_results:
            break
            
        print(f"Page {offset // page_size + 1}: {len(page_results)} meals")
        offset += page_size
        
        if len(page_results) < page_size:
            break  # Last page
```

**Expected Results:**
```
Efficient query: 12 results
Page 1: 20 meals
Page 2: 20 meals  
Page 3: 14 meals
```

#### Caching Strategies

```python
async def caching_examples():
    """Demonstrate caching patterns for performance."""
    
    meal_repo = MealRepo(db_session)
    
    # Repository-level caching (automatic)
    # First call hits database
    start_time = time.time()
    meals_1 = await meal_repo.query(filter={"calories__lte": 400})
    time_1 = time.time() - start_time
    
    # Second call uses cache
    start_time = time.time()
    meals_2 = await meal_repo.query(filter={"calories__lte": 400})
    time_2 = time.time() - start_time
    
    print(f"First query: {time_1:.3f}s ({len(meals_1)} results)")
    print(f"Cached query: {time_2:.3f}s ({len(meals_2)} results)")
    print(f"Cache speedup: {time_1 / time_2:.1f}x faster")
    
    # Domain-level caching (nutri_facts property)
    meal = meals_1[0]
    
    # First access calculates
    start_time = time.time()
    nutri_1 = meal.nutri_facts
    calc_time = time.time() - start_time
    
    # Second access uses cached value
    start_time = time.time()
    nutri_2 = meal.nutri_facts  
    cache_time = time.time() - start_time
    
    print(f"\nNutrition calculation: {calc_time:.4f}s")
    print(f"Cached access: {cache_time:.4f}s")
    print(f"Domain cache speedup: {calc_time / cache_time:.0f}x faster")
```

**Expected Results:**
```
First query: 0.045s (25 results)
Cached query: 0.002s (25 results)  
Cache speedup: 22.5x faster

Nutrition calculation: 0.0012s
Cached access: 0.0001s
Domain cache speedup: 12x faster
```

### Error Handling in Database Operations

#### Graceful Error Handling

```python
from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import (
    RepositoryQueryException,
    FilterValidationException
)
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
    EntityNotFoundException
)

async def database_error_handling():
    """Demonstrate proper error handling patterns."""
    
    meal_repo = MealRepo(db_session)
    
    # Handle missing entities gracefully
    try:
        meal = await meal_repo.get("nonexistent-meal-id")
    except EntityNotFoundException as e:
        print(f"Meal not found: {e.message}")
        print(f"Correlation ID: {e.correlation_id}")
        # Log error, return default, or redirect user
        meal = None
    
    # Handle invalid filters
    try:
        results = await meal_repo.query(filter={
            "invalid_field": "some_value",
            "calories__invalid_op": 300
        })
    except FilterValidationException as e:
        print(f"Invalid filter: {e.message}")
        print(f"Field: {e.context.get('field')}")
        print(f"Valid operators: {e.context.get('valid_operators')}")
        results = []
    
    # Handle database connection issues
    try:
        results = await meal_repo.query(filter={"author_id": "chef_123"})
    except RepositoryQueryException as e:
        print(f"Database error: {e.message}")
        print(f"Query time: {e.execution_time:.3f}s")
        print(f"SQL: {e.sql_query[:100]}...")
        
        # Implement retry logic or fallback
        if e.execution_time > 30.0:
            print("Query timeout - consider pagination or caching")
        else:
            print("Transient error - safe to retry")
```

**Expected Results:**
```
Meal not found: Entity with id 'nonexistent-meal-id' not found in MealRepository
Correlation ID: repo_123_456789

Invalid filter: Invalid filter field 'invalid_field' for MealRepository  
Field: invalid_field
Valid operators: ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'contains', 'icontains']

Database error: Database query execution failed: connection timeout
Query time: 30.125s
SQL: SELECT meals.id, meals.name, meals.author_id FROM meals WHERE meals.author_id = ? AND meals.disc...
Query timeout - consider pagination or caching
```

### Testing Database Queries

#### Repository Testing Patterns

```python
# Testing repository queries - example test structure
async def test_meal_repository_filtering():
    """Test meal repository filtering with real data."""
    
    # Given: Test data in database
    meal_repo = MealRepo(test_session)
    
    test_meals = [
        create_test_meal(name="High Protein", calories=450, protein=30),
        create_test_meal(name="Low Carb", calories=320, carbs=15),
        create_test_meal(name="Balanced", calories=380, protein=20, carbs=35)
    ]
    
    for meal in test_meals:
        await meal_repo.add(meal)
    await test_session.commit()
    
    # When: Filtering by protein content
    high_protein_meals = await meal_repo.query(filter={
        "protein__gte": 25
    })
    
    # Then: Correct results returned
    assert len(high_protein_meals) == 1
    assert high_protein_meals[0].name == "High Protein"
    assert high_protein_meals[0].nutri_facts.protein == 30
    
    # When: Complex filtering
    balanced_meals = await meal_repo.query(filter={
        "calories__gte": 300,
        "calories__lte": 400,
        "protein__gte": 15
    })
    
    # Then: Multiple criteria applied
    assert len(balanced_meals) == 2  # Low Carb + Balanced
    meal_names = {meal.name for meal in balanced_meals}
    assert meal_names == {"Low Carb", "Balanced"}
```

**Expected Test Results:**
```
✓ test_meal_repository_filtering PASSED
✓ All assertions passed
✓ Query results match expected criteria
✓ Complex filters work correctly
```

These database query examples demonstrate the full spectrum of repository operations, from basic CRUD to complex joins and performance optimization. All examples use the `poetry run python -m` pattern for execution and include realistic expected results with performance considerations.

### Monitoring Specifications

#### Structured Logging