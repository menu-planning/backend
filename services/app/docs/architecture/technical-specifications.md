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

### Monitoring Specifications

#### Structured Logging
```python
# Log format
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "logger": "recipes_catalog.command_handler",
    "message": "Meal created successfully",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "meal_id": "660e8400-e29b-41d4-a716-446655440000",
    "recipe_count": 3,
    "total_calories": 650,
    "duration_ms": 145,
    "cache_hits": ["nutri_facts", "macro_division"],
    "correlation_id": "770e8400-e29b-41d4-a716-446655440000"
}
```

#### Metrics to Track
```python
# Business metrics
- meals_created_total (counter)
- recipes_per_meal (histogram)
- nutrition_calculation_duration (histogram)
- cache_hit_ratio (gauge)

# Technical metrics
- lambda_cold_starts (counter)
- database_connection_pool_size (gauge)
- query_duration_by_operation (histogram)
- domain_rule_violations (counter)

# Alerts
- Cache hit ratio < 50% for 1 hour
- p95 response time > 2s for 15 minutes
- Error rate > 1% for 5 minutes
- Database connection pool exhausted
```

### Testing Specifications

#### Test Data Factories
```python
def create_meal(**overrides) -> Meal:
    """Factory for creating test meals"""
    defaults = {
        'name': f"Test Meal {uuid4()}",
        'author_id': str(uuid4()),
        'meal_id': str(uuid4()),
        'menu_id': str(uuid4()),
        'recipes': []
    }
    return Meal.create_meal(**{**defaults, **overrides})

def create_recipe_with_nutrition(
    calories: float = 300,
    protein: float = 20,
    carbs: float = 30,
    fat: float = 15
) -> _Recipe:
    """Factory for recipes with specific nutrition"""
    return _Recipe(
        id=str(uuid4()),
        name=f"Test Recipe {uuid4()}",
        nutri_facts=NutriFacts(
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat
        ),
        # ... other required fields
    )
```

#### Performance Test Patterns
```python
@pytest.mark.benchmark(group="cache_performance")
def test_nutri_facts_cache_performance(benchmark):
    """Benchmark cache effectiveness"""
    meal = create_meal_with_recipes(recipe_count=50)
    
    # Warm up cache
    _ = meal.nutri_facts
    
    # Benchmark cached access
    result = benchmark(lambda: meal.nutri_facts)
    
    assert result.calories > 0
    assert benchmark.stats['mean'] < 0.001  # < 1ms
```

### Deployment Specifications

#### Environment Variables
```bash
# Required
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
STAGE=production|staging|development

# Optional
LOG_LEVEL=INFO
CACHE_TTL_SECONDS=3600
MAX_POOL_SIZE=50
STATEMENT_TIMEOUT_SECONDS=30
```

#### Lambda Configuration
```yaml
Runtime: python3.11
MemorySize: 512 MB
Timeout: 30 seconds
ReservedConcurrentExecutions: 100
Environment:
  Variables:
    PYTHONPATH: /var/runtime:/opt/python
    DATABASE_URL: ${ssm:/app/db/url~true}
Layers:
  - arn:aws:lambda:${AWS::Region}:xxx:layer:dependencies:latest
```

#### CI/CD Pipeline
```yaml
stages:
  - test:
      - pytest tests/unit --cov=src
      - pytest tests/integration
      - mypy src/
      
  - build:
      - poetry export -f requirements.txt
      - pip install -r requirements.txt -t layer/python
      - zip -r layer.zip layer/
      
  - deploy:
      - aws lambda update-function-code
      - aws lambda update-function-configuration
      - alembic upgrade head
```

This technical specification provides the detailed contracts and implementation guidelines that AI agents need to work effectively with the codebase while maintaining consistency and quality.