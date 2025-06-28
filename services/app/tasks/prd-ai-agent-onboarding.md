# PRD: AI Agent Onboarding - Menu Planning Backend Architecture

## Executive Summary

### Problem Statement
AI agents working on this codebase need comprehensive understanding of the domain-driven design architecture, asynchronous patterns, and nutrition domain knowledge to effectively collaborate with users on development tasks. Without proper onboarding, agents may violate architectural principles, miss critical business rules, or produce code that doesn't align with established patterns.

### Proposed Solution
Create a comprehensive onboarding guide that enables AI agents to act as senior technical leads, understanding the entire system architecture, domain model, testing philosophy, and infrastructure. This PRD documents the system's design patterns based on "Architecture Patterns with Python" adapted for asynchronous execution with anyio, AWS Lambda deployment, and RDS PostgreSQL persistence.

### Business Value
- **Reduced onboarding time**: AI agents can immediately understand system architecture
- **Higher code quality**: Agents follow established patterns and conventions
- **Better collaboration**: Agents understand domain language and business rules
- **Safer modifications**: TDD approach ensures changes don't break existing functionality

### Success Criteria
- AI agents can navigate and modify any part of the codebase effectively
- All code changes include comprehensive tests with behavior-focused coverage
- Domain integrity is maintained through proper aggregate boundaries
- Performance targets are met (95%+ cache hit ratio, <2s response times)

## System Overview

### Architecture Philosophy
This system implements Domain-Driven Design (DDD) principles from "Architecture Patterns with Python" by Harry Percival and Bob Gregory, adapted for:
- **Asynchronous execution** using anyio/asyncio
- **Serverless deployment** on AWS Lambda
- **Event-driven architecture** with domain events
- **CQRS patterns** for read/write separation
- **Repository pattern** with Unit of Work for data persistence

### Core Architectural Principles
1. **Domain Model Isolation**: Business logic lives in pure domain objects
2. **Dependency Inversion**: Domain depends on abstractions, not implementations
3. **Event-Driven Communication**: Aggregates communicate through domain events
4. **Test-Driven Development**: Behavior-focused tests drive implementation
5. **Performance by Design**: Instance-level caching for expensive computations

## Domain Model

### Bounded Contexts

#### 1. Recipes Catalog Context
**Purpose**: Manages recipes, meals, menus, and clients for meal planning

**Aggregates**:
- **Meal (Root Aggregate)**
  - Manages Recipe entities
  - Enforces nutrition consistency
  - Handles recipe lifecycle (create, update, delete)
  - Maintains author consistency

- **Menu (Root Aggregate)**
  - Manages MenuMeal value objects
  - Tracks meal assignments by week/day/type
  - Maintains client relationship

- **Client (Root Aggregate)**
  - Represents meal planning clients
  - Manages client preferences and dietary restrictions

**Key Domain Rules**:
- Recipes can only be modified through their parent Meal
- Nutrition facts are automatically aggregated from recipes
- Author ID must be consistent across aggregate and entities
- Menu positions (week/day/meal_type) must be unique

#### 2. Products Catalog Context
**Purpose**: Manages food products, nutritional data, and classifications

**Aggregates**:
- **Product (Root Aggregate)**
  - Stores nutritional information
  - Manages classifications (brand, category, food group)
  - Handles voting for food/non-food determination

**Classifications**:
- Brand, Source, Category, ParentCategory, FoodGroup, ProcessType

#### 3. IAM Context
**Purpose**: Identity and Access Management

**Aggregates**:
- **User (Root Aggregate)**
  - Manages user roles and permissions
  - Handles authentication state

#### 4. Shared Kernel
**Purpose**: Common value objects and enums used across contexts

**Key Components**:
- NutriFacts: Nutritional information value object
- Tag: Classification tags with author tracking
- Address, ContactInfo, Profile: User-related value objects
- DietType, MealType, Season: Domain enums

### Domain Patterns

#### Entity Base Class Features
```python
class Entity:
    """Enhanced with instance-level caching and standardized updates"""
    
    # Instance-level caching with @cached_property
    @cached_property
    def expensive_computation(self):
        self._cached_attrs.add('expensive_computation')
        return self._do_expensive_work()
    
    # Automatic cache invalidation
    def mutate(self):
        self._data = new_value
        self._invalidate_caches('expensive_computation')
        self._increment_version()
    
    # Standardized update pattern
    def update_properties(self, **kwargs):
        # 1. Validation
        # 2. Apply changes (protected setters first)
        # 3. Post-update hooks
        # 4. Version increment
        # 5. Cache invalidation
```

#### Aggregate Boundary Enforcement
```python
# Recipe uses protected setters (Pythonic convention)
class _Recipe(Entity):
    @property
    def name(self) -> str:
        return self._name
    
    def _set_name(self, value: str) -> None:
        """Protected setter - only called via Meal aggregate"""
        self._name = value
        self._increment_version()

# Meal provides public API for recipe modifications
class Meal(Entity):
    def update_recipes(self, recipe_id: str, **kwargs):
        """Public API enforcing aggregate boundaries"""
        recipe = self._get_recipe_by_id(recipe_id)
        recipe.update_properties(**kwargs)
        self._invalidate_caches('nutri_facts')
```

## Technical Architecture

### Layer Structure
```
src/contexts/{context_name}/
├── core/
│   ├── domain/           # Pure domain logic
│   │   ├── commands/     # Command objects
│   │   ├── entities/     # Domain entities
│   │   ├── events/       # Domain events
│   │   ├── root_aggregate/  # Aggregate roots
│   │   └── value_objects/   # Value objects
│   ├── adapters/         # Interface adapters
│   │   ├── api_schemas/  # Pydantic models for API
│   │   ├── ORM/          # SQLAlchemy mappings
│   │   └── repositories/ # Repository implementations
│   ├── services/         # Application services
│   │   ├── command_handlers.py
│   │   ├── event_handlers.py
│   │   └── uow.py        # Unit of Work
│   └── bootstrap/        # Dependency injection
└── aws_lambda/           # Lambda function handlers
```

### Asynchronous Patterns

#### Repository Pattern with Async
```python
class RecipeRepo(SeedWorkRepository[_Recipe]):
    async def get(self, recipe_id: str) -> _Recipe:
        async with self.session.begin():
            result = await self.session.execute(
                select(RecipeSAModel).where(RecipeSAModel.id == recipe_id)
            )
            return self._to_domain(result.scalar_one())
```

#### Unit of Work Pattern
```python
class UnitOfWork:
    async def __aenter__(self):
        self.session = self.session_factory()
        self.recipes = RecipeRepo(self.session)
        self.meals = MealRepo(self.session)
        return self
    
    async def commit(self):
        await self._publish_events()
        await self.session.commit()
```

#### Command Handler Pattern
```python
async def create_meal(cmd: CreateMeal, uow: UnitOfWork):
    async with uow:
        meal = Meal.create_meal(
            name=cmd.name,
            author_id=cmd.author_id,
            recipes=cmd.recipes
        )
        await uow.meals.add(meal)
        await uow.commit()
```

### Performance Optimization

#### Cache Strategy
- **Instance-level caching**: Each entity instance maintains its own cache
- **Automatic invalidation**: Caches cleared on relevant mutations
- **Target metrics**: 95%+ cache hit ratio, 30x+ performance improvement

#### Monitored Properties
- `meal.nutri_facts`: Aggregated nutrition from all recipes
- `recipe.average_taste_rating`: Computed from all ratings
- `menu._meals_by_position_lookup`: O(1) meal position queries

### Infrastructure

#### AWS Lambda Deployment
- **Handler pattern**: One Lambda function per command/query
- **Cold start optimization**: Lightweight handlers, lazy imports
- **Error handling**: Structured error responses with correlation IDs

#### Database (RDS PostgreSQL)
- **Async driver**: asyncpg for high-performance queries
- **Connection pooling**: Managed by SQLAlchemy async sessions
- **Schema migrations**: Alembic with async support

## Testing Philosophy

### Test-Driven Development (TDD)
1. **Write test first**: Define expected behavior before implementation
2. **Red-Green-Refactor**: Fail, pass, improve
3. **Behavior over implementation**: Test what it does, not how

### Test Structure
```
tests/contexts/{context_name}/
├── unit/                 # Pure domain logic tests
│   ├── test_entities.py
│   ├── test_value_objects.py
│   └── test_cmd_handlers.py
├── integration/          # Repository and service tests
│   ├── test_repository.py
│   └── test_uow.py
└── e2e/                  # Full Lambda handler tests
```

### Testing Patterns

#### Domain Entity Tests
```python
def test_meal_nutri_facts_aggregation():
    """Test that nutri_facts correctly aggregates from recipes"""
    # Arrange
    meal = create_meal_with_recipes(recipe_count=3)
    
    # Act
    nutri_facts = meal.nutri_facts
    
    # Assert
    assert nutri_facts.calories == sum(r.nutri_facts.calories for r in meal.recipes)
    assert nutri_facts.protein == sum(r.nutri_facts.protein for r in meal.recipes)
```

#### Cache Behavior Tests
```python
def test_cache_invalidation_on_recipe_update():
    """Test that updating a recipe invalidates meal's nutri_facts cache"""
    meal = create_meal_with_recipes()
    
    # First access caches the value
    initial_nutri = meal.nutri_facts
    
    # Update recipe should invalidate cache
    meal.update_recipes(
        recipe_id=meal.recipes[0].id,
        nutri_facts=new_nutrition_data()
    )
    
    # Next access should show updated values
    updated_nutri = meal.nutri_facts
    assert updated_nutri != initial_nutri
```

#### Repository Tests with Async
```python
async def test_meal_repository_cascade_save():
    """Test that saving a meal persists all recipes"""
    async with UnitOfWork() as uow:
        meal = create_meal_with_recipes(recipe_count=3)
        await uow.meals.add(meal)
        await uow.commit()
    
    # Verify in new transaction
    async with UnitOfWork() as uow:
        saved_meal = await uow.meals.get(meal.id)
        assert len(saved_meal.recipes) == 3
```

### Coverage Requirements
- **Domain layer**: ≥90% coverage required
- **Critical paths**: 100% coverage for financial calculations
- **Edge cases**: Parametrized tests for boundary conditions

## Domain Knowledge

### Nutrition Domain

#### Core Concepts
1. **Macronutrients**: Carbohydrates, Proteins, Fats
2. **Micronutrients**: Vitamins, Minerals
3. **Energy**: Calories (kcal)
4. **Serving sizes**: Grams, portions, units

#### Business Rules
1. **Calorie calculation**: 
   - Carbs: 4 kcal/g
   - Protein: 4 kcal/g
   - Fat: 9 kcal/g
   - Alcohol: 7 kcal/g

2. **Macro division**:
   - Must sum to ~100% (allowing for rounding)
   - Calculated from energy contribution, not weight

3. **Recipe scaling**:
   - Nutrition scales linearly with quantity
   - Minimum serving sizes enforced

#### Menu Planning Rules
1. **Weekly structure**:
   - 4 weeks per menu cycle
   - 7 days per week
   - Multiple meal types per day (breakfast, lunch, dinner, snacks)

2. **Dietary restrictions**:
   - Allergen tracking (gluten, dairy, nuts, etc.)
   - Diet types (vegan, vegetarian, keto, etc.)
   - Religious restrictions (halal, kosher)

3. **Nutritional balance**:
   - Daily calorie targets
   - Macro distribution goals
   - Micronutrient requirements

## Development Workflow

### For AI Agents

#### 1. Understanding a Task
```python
# First, analyze the domain model
- Identify affected aggregates
- Review existing tests for behavior
- Check domain rules and invariants

# Example: "Add allergen filtering to recipes"
1. Find Recipe entity and Meal aggregate
2. Review how tags/classifications work
3. Check existing filter patterns
4. Look for similar features (diet_type filtering)
```

#### 2. TDD Approach
```python
# Step 1: Write failing test
async def test_filter_recipes_by_allergen():
    # Arrange
    meal = create_meal_with_recipes_containing_allergens()
    
    # Act
    gluten_free_recipes = meal.filter_recipes(exclude_allergens=['gluten'])
    
    # Assert
    assert all('gluten' not in r.allergens for r in gluten_free_recipes)

# Step 2: Implement minimum code to pass
# Step 3: Refactor while keeping tests green
# Step 4: Add edge case tests
```

#### 3. Making Changes
```python
# Always follow the layer hierarchy
1. Domain layer changes first (entities, value objects)
2. Update repositories if needed
3. Modify command handlers
4. Update API schemas
5. Adjust Lambda handlers

# Run tests after each layer
pytest tests/contexts/recipes_catalog/unit -v
pytest tests/contexts/recipes_catalog/integration -v
```

#### 4. Performance Considerations
```python
# Before adding computed properties
1. Consider if caching is needed (expensive calculation?)
2. Use @cached_property for instance-level caching
3. Ensure cache invalidation on mutations
4. Write tests for cache behavior
5. Benchmark if performance-critical
```

### Common Patterns to Follow

#### Command Pattern
```python
@dataclass
class CreateRecipe:
    """Command for recipe creation"""
    meal_id: str
    name: str
    ingredients: list[Ingredient]
    instructions: str
    nutri_facts: NutriFacts
    author_id: str
```

#### Event Pattern
```python
@dataclass
class RecipeCreated(Event):
    """Domain event for recipe creation"""
    meal_id: str
    recipe_id: str
    name: str
    author_id: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)
```

#### Repository Pattern
```python
class RecipeRepository(Protocol):
    """Repository interface for recipes"""
    async def get(self, recipe_id: str) -> _Recipe: ...
    async def add(self, recipe: _Recipe) -> None: ...
    async def update(self, recipe: _Recipe) -> None: ...
```

## Error Handling

### Domain Exceptions
```python
class BusinessRuleValidationException(Exception):
    """Raised when a domain rule is violated"""
    def __init__(self, rule: type[BusinessRule], message: str):
        self.rule = rule
        self.message = f"{rule.__name__}: {message}"

class DiscardedEntityException(Exception):
    """Raised when operating on a discarded entity"""
    pass
```

### Validation Pattern
```python
# Domain rules as classes
class RecipeMustHaveValidNutrition(BusinessRule):
    def __init__(self, nutri_facts: NutriFacts):
        self.nutri_facts = nutri_facts
    
    def is_broken(self) -> bool:
        return (
            self.nutri_facts.calories < 0 or
            self.nutri_facts.protein < 0 or
            self.nutri_facts.carbs < 0 or
            self.nutri_facts.fat < 0
        )

# Usage in domain
def create_recipe(self, **kwargs):
    nutri_facts = kwargs['nutri_facts']
    self.check_rule(RecipeMustHaveValidNutrition(nutri_facts))
```

## Monitoring and Observability

### Key Metrics
1. **Performance**:
   - Cache hit ratios per entity type
   - Query execution times
   - Lambda cold start frequency

2. **Business**:
   - Recipes created per day
   - Average nutrition accuracy
   - Menu completion rates

3. **Technical**:
   - Domain rule violations
   - Repository operation latency
   - Event processing lag

### Logging Strategy
```python
# Structured logging with context
logger.info(
    "Recipe created",
    extra={
        "meal_id": meal.id,
        "recipe_id": recipe.id,
        "author_id": author_id,
        "nutrition_calories": recipe.nutri_facts.calories,
        "cache_invalidated": ["nutri_facts", "macro_division"]
    }
)
```

## Security Considerations

### Authentication & Authorization
- **Authentication**: Handled by AWS Cognito (assumed from context)
- **Authorization**: Role-based access control in domain
- **Multi-tenancy**: Author-based data isolation

### Data Protection
- **PII handling**: User data in separate context (IAM)
- **Audit trail**: Version tracking on all entities
- **Soft deletes**: Entities marked as discarded, not deleted

## Migration and Evolution

### Adding New Features
1. **Start with domain model**: Add to entities/aggregates
2. **Maintain backward compatibility**: Use optional fields
3. **Version your commands**: Support multiple command versions
4. **Test migrations**: Ensure existing data works

### Refactoring Safely
1. **Parallel run**: New code alongside old
2. **Feature flags**: Gradual rollout
3. **Comprehensive tests**: Before touching domain
4. **Event versioning**: For breaking changes

## Quick Reference

### Key Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/contexts --cov-report=term-missing

# Run specific context tests
pytest tests/contexts/recipes_catalog -v

# Run only unit tests
pytest tests/contexts/recipes_catalog/unit -v

# Type checking
mypy src/

# Database migrations
alembic upgrade head
```

### Important Files
- `src/contexts/seedwork/shared/domain/entity.py` - Base entity class
- `src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py` - Meal aggregate example
- `tests/performance_phase_4_1_cache_effectiveness.py` - Cache performance benchmarks
- `docs/architecture/decisions/ADR-001-*.md` - Architecture decisions

### Performance Targets
- Cache hit ratio: ≥95%
- Response time: <2s for 95th percentile
- Domain operation latency: <100ms
- Test execution: <5 minutes for full suite

## Conclusion

This architecture provides a robust foundation for building a scalable, maintainable meal planning system. AI agents should approach development with these principles:

1. **Domain-first thinking**: Understand the business problem before coding
2. **Test-driven development**: Write tests that describe behavior
3. **Performance awareness**: Use caching judiciously with proper invalidation
4. **Architectural consistency**: Follow established patterns and conventions
5. **Collaborative mindset**: Work alongside users, respecting their expertise

Remember: You're not just writing code; you're modeling a complex nutrition and meal planning domain with real-world constraints and requirements. Every decision should enhance the domain model's expressiveness while maintaining system performance and reliability.