[← Index](./README.md) | [Quick Start](./quick-start-guide.md) | [Workflows](./ai-agent-workflows.md) | [Patterns](./pattern-library.md) | [Troubleshooting](./troubleshooting-guide.md)

---

# Menu Planning Backend - Pattern Library

A comprehensive collection of implementation patterns extracted from the menu planning backend codebase. Each pattern includes working code examples, best practices, and common pitfalls to avoid.

## 📚 Table of Contents

1. [Adding a New Command](#adding-a-new-command)
2. [Implementing Cached Properties](#implementing-cached-properties)
3. [Repository Method Implementation](#repository-method-implementation)
4. [Domain Event Implementation](#domain-event-implementation)
5. [Lambda Handler Patterns](#lambda-handler-patterns)
6. [Entity Update Patterns](#entity-update-patterns)
7. [Simple Domain Property Addition](#simple-domain-property-addition)

---

## Adding a New Command

Complete end-to-end example of adding a new command to the system, from domain layer to Lambda handler.

### Pattern Overview

Commands in this system follow a strict pattern:
1. **Command Definition** - Define the command data structure
2. **Command Handler** - Implement the business logic
3. **Handler Registration** - Register in bootstrap
4. **API Schema** - Define request/response contracts
5. **Lambda Handler** - AWS Lambda entry point

### Example: Adding `UpdateRecipeNutrition` Command

#### Step 1: Define the Command

```python
# src/contexts/recipes_catalog/core/domain/meal/commands/update_recipe_nutrition.py
from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts

@frozen
class UpdateRecipeNutrition(Command):
    """Command to update nutritional facts for a recipe."""
    meal_id: str                           # Parent aggregate ID
    recipe_id: str                         # Target recipe ID  
    nutri_facts: NutriFacts               # New nutritional data
    user_id: str                          # Who is making the change
```

#### Step 2: Implement Command Handler

```python
# src/contexts/recipes_catalog/core/services/meal/command_handlers/update_recipe_nutrition.py
from src.contexts.recipes_catalog.core.domain.meal.commands.update_recipe_nutrition import UpdateRecipeNutrition
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.logging.logger import logger

async def update_recipe_nutrition_handler(cmd: UpdateRecipeNutrition, uow: UnitOfWork) -> None:
    """
    Handler for updating recipe nutritional facts.
    
    Business Rules:
    - Only recipe author or admin can update nutrition
    - Meal's aggregate nutrition is automatically recalculated
    - Cache invalidation happens automatically via Entity pattern
    """
    async with uow:
        # Load the meal aggregate (contains recipes)
        meal = await uow.meals.get(cmd.meal_id)
        
        # Update recipe nutrition through aggregate root
        # This ensures domain rules are enforced
        meal.update_recipe_nutrition(
            recipe_id=cmd.recipe_id,
            nutri_facts=cmd.nutri_facts,
            user_id=cmd.user_id
        )
        
        # Persist changes
        await uow.meals.persist(meal)
        await uow.commit()
        
        logger.info(f"Updated nutrition for recipe {cmd.recipe_id} in meal {cmd.meal_id}")
```

#### Step 3: Register in Bootstrap

```python
# src/contexts/recipes_catalog/core/bootstrap/bootstrap.py (additions)
import src.contexts.recipes_catalog.core.domain.meal.commands as meal_commands
import src.contexts.recipes_catalog.core.services.meal.command_handlers as meal_cmd_handlers

def bootstrap(uow: UnitOfWork) -> MessageBus:
    # ... existing code ...
    
    injected_command_handlers: dict[type[SeedworkCommand], partial[Coroutine]] = {
        # ... existing handlers ...
        
        # NEW: Register the command handler
        meal_commands.UpdateRecipeNutrition: partial(
            meal_cmd_handlers.update_recipe_nutrition_handler, 
            uow=uow
        ),
    }
    
    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
```

#### Step 4: Add Domain Method to Aggregate

```python
# src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py (additions)
def update_recipe_nutrition(
    self, 
    recipe_id: str, 
    nutri_facts: NutriFacts, 
    user_id: str
) -> None:
    """Update nutritional facts for a specific recipe in this meal."""
    self._check_not_discarded()
    
    # Find the target recipe
    recipe = self._get_recipe_by_id(recipe_id)
    if not recipe:
        raise ValueError(f"Recipe {recipe_id} not found in meal {self.id}")
    
    # Business rule: Only author or admin can update nutrition
    if recipe.author_id != user_id:
        # Would check admin permissions here in full implementation
        raise PermissionError(f"User {user_id} cannot update recipe {recipe_id}")
    
    # Update through protected setter (aggregate boundary enforcement)
    recipe._set_nutri_facts(nutri_facts)
    
    # Cache invalidation happens automatically via Entity base class
    # The meal's nutri_facts @cached_property will be invalidated
    # when recipes collection is marked as modified
    self._increment_version()
    self._invalidate_caches('nutri_facts')
```

### Command Pattern Benefits

1. **Explicit Intent** - Each command represents a clear business operation
2. **Validation** - Commands can be validated before execution
3. **Audit Trail** - Every command execution can be logged
4. **Testability** - Commands are easy to unit test
5. **Async Processing** - Commands can be queued and processed asynchronously

### Common Pitfalls

❌ **Don't bypass the aggregate root**
```python
# Wrong - violates aggregate boundary
recipe = await uow.recipes.get(recipe_id)  # Direct recipe access
recipe.nutri_facts = new_facts
```

✅ **Do use aggregate root methods**
```python
# Right - respects aggregate boundary  
meal = await uow.meals.get(meal_id)
meal.update_recipe_nutrition(recipe_id, new_facts, user_id)
```

❌ **Don't forget cache invalidation**
```python
# Wrong - cached properties won't update
recipe._nutri_facts = new_facts
# meal.nutri_facts will still return old cached value
```

✅ **Do use proper setters**
```python
# Right - cache invalidation handled automatically
recipe._set_nutri_facts(new_facts)
# This triggers cache invalidation in parent meal
```

---

## Implementing Cached Properties

The codebase uses `@cached_property` for expensive computations with automatic instance-level caching and smart invalidation.

### Pattern Overview

The Entity base class automatically detects `@cached_property` decorators and provides:
- **Instance-level caching** - No shared cache data between entity instances
- **Automatic cache tracking** - Knows which caches have been computed
- **Smart invalidation** - Clear specific caches or all caches
- **Performance monitoring** - Cache hit ratio tracking

### Example 1: Recipe Average Ratings (Simple Aggregation)

```python
# src/contexts/recipes_catalog/core/domain/meal/entities/recipe.py
from functools import cached_property

class _Recipe(Entity):
    @cached_property
    def average_taste_rating(self) -> float | None:
        """Calculate the average taste rating across all ratings for this recipe.
        
        This property uses instance-level caching to avoid repeated computation
        when accessed multiple times. The cache is automatically invalidated
        when ratings are modified through rate() or delete_rate() methods.
        
        Returns:
            float | None: Average taste rating (1.0-5.0), or None if no ratings exist
            
        Cache invalidation triggers:
            - rate(): When new rating is added or existing rating is updated
            - delete_rate(): When a rating is removed
            
        Performance: O(n) computation on first access, O(1) on subsequent accesses
        until cache invalidation.
        """
        self._check_not_discarded()
        if not self._ratings or len(self._ratings) == 0:
            return None
        total_taste = sum(rating.taste for rating in self._ratings)
        return total_taste / len(self._ratings)

    @cached_property
    def average_convenience_rating(self) -> float | None:
        """Calculate the average convenience rating across all ratings for this recipe."""
        self._check_not_discarded()
        if not self._ratings or len(self._ratings) == 0:
            return None
        total_convenience = sum(rating.convenience for rating in self._ratings)
        return total_convenience / len(self._ratings)

    def rate(self, rating: Rating, author_id: str) -> None:
        """Add a rating and invalidate rating-related caches."""
        self._check_not_discarded()
        
        # Business logic
        existing_rating = self._find_rating_by_author(author_id)
        if existing_rating:
            self._ratings.remove(existing_rating)
        self._ratings.append(rating)
        
        self._increment_version()
        
        # Invalidate only rating-related caches (targeted invalidation)
        self._invalidate_caches('average_taste_rating', 'average_convenience_rating')
```

### Example 2: Complex Nutritional Calculations

```python
# src/contexts/recipes_catalog/core/domain/meal/entities/recipe.py
@cached_property
def macro_division(self) -> MacroDivision | None:
    """Calculate the macronutrient distribution as percentages.
    
    This property computes the percentage breakdown of carbohydrates, proteins,
    and fats based on the recipe's nutritional facts. Uses instance-level caching
    to avoid repeated computation when accessed multiple times.
    
    Returns:
        MacroDivision | None: Object containing carbohydrate, protein, and fat
        percentages (totaling 100%), or None if insufficient nutritional data
        
    Cache invalidation triggers:
        - nutri_facts setter: When nutritional facts are updated
        
    Performance: O(1) computation on first access, O(1) on subsequent accesses
    until cache invalidation.
    
    Notes:
        - Returns None if nutri_facts is None
        - Returns None if any macro values (carbs, protein, fat) are None
        - Returns None if total macros sum to zero (division by zero protection)
    """
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

def _set_nutri_facts(self, value: NutriFacts) -> None:
    """Protected setter for nutri_facts. Can only be called through Meal aggregate."""
    self._check_not_discarded()
    if self._nutri_facts != value:
        self._nutri_facts = value
        self._increment_version()
        # Invalidate nutrition-related caches
        self._invalidate_caches('macro_division')
```

### Example 3: Menu Lookup Tables (Performance Optimization)

```python
# src/contexts/recipes_catalog/core/domain/client/entities/menu.py
class Menu(Entity):
    @cached_property
    def _meals_by_position_lookup(self) -> dict[tuple[int, str, str], MenuMeal]:
        """Create a dictionary mapping position coordinates to MenuMeal objects.
        
        This property builds a lookup table for fast positional queries using
        (week, weekday, meal_type) tuples as keys. Uses instance-level caching
        to avoid rebuilding the lookup table on repeated access.
        
        Returns:
            dict[tuple[int, str, str], MenuMeal]: Dictionary mapping position tuples
            to MenuMeal objects for O(1) positional lookups
            
        Cache invalidation triggers:
            - meals setter: When the meals collection is replaced
            - add_meal(): When a new meal is added to the menu
            - update_meal(): When an existing meal is updated
            
        Performance: O(n) computation where n = number of meals on first access,
        O(1) lookup performance, O(1) on subsequent accesses until cache invalidation.
        
        Notes:
            - Used internally by filter_meals() for efficient positional queries
            - Key format: (week_number, weekday, meal_type)
            - Automatically handles duplicate positions (last meal wins)
        """
        self._check_not_discarded()
        result = {}
        for meal in self._meals:
            key = (meal.week, meal.weekday, meal.meal_type)
            result[key] = meal
        return result
    
    @cached_property
    def _meals_by_id_lookup(self) -> dict[str, MenuMeal]:
        """Create a dictionary mapping meal IDs to MenuMeal objects."""
        self._check_not_discarded()
        return {meal.meal_id: meal for meal in self._meals}
    
    def get_meals_by_ids(self, meals_ids: set[str]) -> set[MenuMeal]:
        """Get meals by their IDs using cached lookup table."""
        self._check_not_discarded()
        lookup = self._meals_by_id_lookup  # Uses cached lookup table
        result = {lookup[meal_id] for meal_id in meals_ids if meal_id in lookup}
        return result

    def add_meal(self, menu_meal: MenuMeal) -> None:
        """Add a meal to the menu and invalidate lookup caches."""
        self._check_not_discarded()
        self._meals.add(menu_meal)
        self._increment_version()
        
        # Invalidate lookup table caches
        self._invalidate_caches(
            '_meals_by_position_lookup', 
            '_meals_by_id_lookup', 
            '_ids_of_meals_on_menu'
        )
```

### Cache Performance Monitoring

```python
# Example of monitoring cache effectiveness
def analyze_cache_performance(entity: Entity):
    """Analyze cache performance for an entity instance."""
    cache_info = entity.get_cache_info()
    
    print(f"Cache Performance for {entity.__class__.__name__}:")
    print(f"  Total cached properties: {cache_info['total_cached_properties']}")
    print(f"  Computed caches: {cache_info['computed_caches']}")
    print(f"  Cache names: {cache_info['cache_names']}")
    
    # Target: ≥95% cache hit ratio in production
    hit_ratio = (cache_info['computed_caches'] / cache_info['total_cached_properties']) * 100
    print(f"  Cache utilization: {hit_ratio:.1f}%")
    
    return cache_info

# Usage in tests or monitoring
recipe = await uow.recipes.get(recipe_id)

# Access cached properties multiple times
_ = recipe.average_taste_rating
_ = recipe.macro_division
_ = recipe.average_taste_rating  # Should be cache hit

cache_info = analyze_cache_performance(recipe)
```

### Cache Best Practices

✅ **Do use @cached_property for expensive computations**
```python
@cached_property
def expensive_computation(self) -> Result:
    """This will be computed once and cached."""
    return self._perform_complex_calculation()
```

✅ **Do invalidate caches when underlying data changes**
```python
def update_data(self, new_value):
    self._data = new_value
    self._increment_version()
    self._invalidate_caches('expensive_computation')  # Clear affected cache
```

✅ **Do use targeted cache invalidation**
```python
# Only invalidate specific caches that are affected
self._invalidate_caches('average_taste_rating', 'average_convenience_rating')
```

❌ **Don't forget to invalidate caches after mutations**
```python
# Wrong - cache will return stale data
def update_ratings(self, new_ratings):
    self._ratings = new_ratings
    # Missing: self._invalidate_caches('average_taste_rating')
```

❌ **Don't use @cached_property for simple property access**
```python
# Wrong - unnecessary caching overhead
@cached_property
def name(self) -> str:
    return self._name  # Simple property access doesn't need caching
```

❌ **Don't share cached data between instances**
```python
# Wrong - this would cause data leakage between instances
_SHARED_CACHE = {}  # Don't do this

@cached_property
def computed_value(self):
    if self.id not in _SHARED_CACHE:  # Wrong approach
        _SHARED_CACHE[self.id] = self._compute()
    return _SHARED_CACHE[self.id]
```

### Cache Performance Targets

- **Cache Hit Ratio**: ≥95% for production workloads
- **Memory Overhead**: <5% additional memory per entity instance
- **Computation Speedup**: 30%+ improvement on repeated access
- **Cache Invalidation**: O(1) operation for targeted invalidation

---

## Repository Method Implementation

Repository methods provide the interface between domain entities and data persistence using SQLAlchemy and the SaGenericRepository pattern.

### Pattern Overview

The repository pattern in this codebase uses:
- **SaGenericRepository** - Base generic repository with SQLAlchemy ORM
- **FilterColumnMapper** - Maps filter keys to database columns
- **Data Mappers** - Convert between domain entities and SQLAlchemy models
- **Unit of Work** - Manages transactions and entity lifecycle
- **Repository Logger** - Structured logging for query performance

### Example 1: Standard Repository Implementation

```python
# src/contexts/recipes_catalog/core/adapters/repositories/meal_repository.py
from typing import Any
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.recipes_catalog.core.adapters.ORM.mappers.meal_mapper import MealMapper
from src.contexts.recipes_catalog.core.adapters.ORM.sa_models.meal import MealSaModel
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)

class MealRepo(CompositeRepository[Meal, MealSaModel]):
    """Repository for Meal aggregate with filter mappings and query optimization."""
    
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=MealSaModel,
            filter_key_to_column_name={
                "id": "id",
                "name": "name", 
                "author_id": "author_id",
                "created_at": "created_at",
                "updated_at": "updated_at",
                "discarded": "discarded",
            },
        ),
    ]

    def __init__(self, db_session: AsyncSession):
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=MealMapper,
            domain_model_type=Meal,
            sa_model_type=MealSaModel,
            filter_to_column_mappers=MealRepo.filter_to_column_mappers,
        )
        
        # Expose generic repository attributes
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Meal):
        """Add a new meal to the repository."""
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Meal:
        """Get a meal by ID."""
        return await self._generic_repo.get(id)

    async def get_sa_instance(self, id: str) -> MealSaModel:
        """Get the SQLAlchemy model instance by ID."""
        return await self._generic_repo.get_sa_instance(id)

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
        _return_sa_instance: bool = False,
    ) -> list[Meal]:
        """Query meals with filters and optional custom SQL statement."""
        return await self._generic_repo.query(
            filter=filter, 
            starting_stmt=starting_stmt, 
            _return_sa_instance=_return_sa_instance
        )

    async def persist(self, domain_obj: Meal) -> None:
        """Persist changes to an existing meal."""
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Meal] | None = None) -> None:
        """Persist all meals tracked by the repository."""
        await self._generic_repo.persist_all(domain_entities)
```

### Example 2: Advanced Query Patterns

```python
# Advanced repository usage patterns from actual codebase
class AdvancedMealQueries:
    def __init__(self, meal_repo: MealRepo):
        self.meal_repo = meal_repo
    
    async def get_meals_by_author(self, author_id: str, limit: int = 10) -> list[Meal]:
        """Get meals by author with pagination."""
        filter_criteria = {
            "author_id": author_id,
            "discarded": False,
            "limit": limit,
            "sort": "created_at_desc"
        }
        return await self.meal_repo.query(filter=filter_criteria)
    
    async def get_recent_meals(self, days: int = 7) -> list[Meal]:
        """Get meals created in the last N days."""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        filter_criteria = {
            "created_at_gte": cutoff_date.isoformat(),
            "discarded": False,
            "sort": "created_at_desc"
        }
        return await self.meal_repo.query(filter=filter_criteria)
    
    async def search_meals_by_name(self, name_pattern: str) -> list[Meal]:
        """Search meals by name pattern (case-insensitive)."""
        filter_criteria = {
            "name_ilike": f"%{name_pattern}%",
            "discarded": False
        }
        return await self.meal_repo.query(filter=filter_criteria)

    async def get_meals_with_nutrition(self) -> list[Meal]:
        """Get meals that have nutritional information."""
        # Custom SQL for complex filtering
        from sqlalchemy import select, and_
        
        stmt = select(MealSaModel).where(
            and_(
                MealSaModel.discarded == False,
                MealSaModel.nutri_facts.is_not(None)
            )
        )
        
        return await self.meal_repo.query(starting_stmt=stmt)
```

### Example 3: Filter Operations and Performance

```python
# Repository performance patterns from SaGenericRepository
class PerformantRepositoryUsage:
    """Examples of performance-optimized repository usage."""
    
    async def batch_load_meals(self, meal_ids: list[str]) -> dict[str, Meal]:
        """Efficiently batch load multiple meals."""
        filter_criteria = {
            "id_in": meal_ids,  # Uses SQL IN clause
            "discarded": False
        }
        
        meals = await self.meal_repo.query(filter=filter_criteria)
        return {meal.id: meal for meal in meals}
    
    async def paginated_meal_query(
        self, 
        page: int = 1, 
        page_size: int = 20,
        author_id: str | None = None
    ) -> tuple[list[Meal], int]:
        """Paginated query with optional filtering."""
        offset = (page - 1) * page_size
        
        filter_criteria = {
            "limit": page_size,
            "skip": offset,
            "sort": "created_at_desc",
            "discarded": False
        }
        
        if author_id:
            filter_criteria["author_id"] = author_id
        
        meals = await self.meal_repo.query(filter=filter_criteria)
        
        # Note: In production, you'd also want a count query for total pages
        return meals, len(meals)
    
    async def optimized_meal_with_recipes(self, meal_id: str) -> Meal:
        """Load meal with all related recipes in a single query."""
        # The repository automatically handles relationships through SQLAlchemy
        meal = await self.meal_repo.get(meal_id)
        
        # Recipes are loaded lazily or eagerly based on SQLAlchemy relationship config
        # Access to meal.recipes will trigger loading if not already loaded
        recipes_count = len(meal.recipes)  # This may trigger a DB query
        
        return meal
```

### Example 4: Repository Error Handling

```python
# Error handling patterns from the actual codebase
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
)
from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import (
    RepositoryQueryException,
    FilterValidationException,
)

class RobustRepositoryUsage:
    """Repository usage with proper error handling."""
    
    async def safe_get_meal(self, meal_id: str) -> Meal | None:
        """Safely get a meal, returning None if not found."""
        try:
            return await self.meal_repo.get(meal_id)
        except EntityNotFoundException:
            logger.info(f"Meal {meal_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving meal {meal_id}: {e}")
            raise
    
    async def validate_and_query(self, filter_dict: dict[str, Any]) -> list[Meal]:
        """Query with filter validation."""
        try:
            return await self.meal_repo.query(filter=filter_dict)
        except FilterValidationException as e:
            logger.warning(f"Invalid filters: {e.invalid_filters}")
            logger.info(f"Suggested filters: {e.suggested_filters}")
            raise ValueError(f"Invalid filter criteria: {e}")
        except RepositoryQueryException as e:
            logger.error(f"Query failed: {e}")
            if e.sql_query:
                logger.debug(f"Failed SQL: {e.sql_query}")
            raise
```

### Repository Pattern Benefits

1. **Abstraction** - Clean separation between domain and data access
2. **Performance** - Built-in query optimization and logging
3. **Flexibility** - Support for custom SQL when needed
4. **Error Handling** - Structured exceptions with context
5. **Monitoring** - Automatic performance logging and metrics

### Filter Operation Patterns

The repository supports rich filtering through `FilterColumnMapper`:

```python
# Supported filter operations (from actual codebase)
filter_examples = {
    # Basic equality
    "author_id": "user123",
    "discarded": False,
    
    # Comparison operators
    "created_at_gte": "2024-01-01T00:00:00Z",  # Greater than or equal
    "created_at_lte": "2024-12-31T23:59:59Z",  # Less than or equal  
    "version_ne": 1,                           # Not equal
    
    # Collection operations
    "id_in": ["id1", "id2", "id3"],           # IN clause
    "status_not_in": ["deleted", "archived"], # NOT IN clause
    
    # String operations
    "name_ilike": "%recipe%",                  # Case-insensitive LIKE
    "description_like": "healthy%",           # Case-sensitive LIKE
    
    # Null checks
    "notes_is_not": None,                     # IS NOT NULL
    "deleted_at_is": None,                    # IS NULL
    
    # Pagination and sorting
    "limit": 20,
    "skip": 40,  # OFFSET
    "sort": "created_at_desc",  # or "created_at_asc"
}
```

### Common Repository Pitfalls

❌ **Don't query repositories directly in domain entities**
```python
# Wrong - domain entity shouldn't know about repositories
class Meal(Entity):
    async def get_similar_meals(self):
        repo = MealRepo()  # Domain shouldn't depend on infrastructure
        return await repo.query({"name_like": f"%{self.name}%"})
```

✅ **Do use application services for cross-entity queries**
```python
# Right - application service coordinates repository usage
class MealService:
    def __init__(self, meal_repo: MealRepo):
        self.meal_repo = meal_repo
    
    async def get_similar_meals(self, meal: Meal) -> list[Meal]:
        return await self.meal_repo.query({"name_like": f"%{meal.name}%"})
```

❌ **Don't forget to handle database sessions properly**
```python
# Wrong - session management is not handled
async def broken_query():
    repo = MealRepo(some_session)  # Session lifecycle unclear
    meals = await repo.query({})   # May fail if session is closed
    return meals
```

✅ **Do use Unit of Work for session management**
```python
# Right - UoW manages session lifecycle
async def proper_query(uow: UnitOfWork) -> list[Meal]:
    async with uow:  # Session is properly managed
        meals = await uow.meals.query({})
        await uow.commit()  # Explicit transaction management
    return meals
```

---

## Domain Event Implementation

Domain events enable loose coupling between aggregates and provide a mechanism for eventual consistency and cross-cutting concerns.

### Pattern Overview

Domain events in this codebase follow these patterns:
- **Event Definition** - Using `@frozen` attrs classes inheriting from `Event`
- **Event Registration** - Events are registered in the bootstrap with handlers
- **Event Dispatch** - MessageBus handles event routing and execution
- **Event Collection** - UnitOfWork collects events from entities after operations
- **Event Processing** - Events are processed asynchronously after command completion

### Example 1: Basic Domain Event

```python
# src/contexts/iam/core/domain/events.py
import uuid
from attrs import field, frozen
from src.contexts.seedwork.shared.domain.event import Event

@frozen
class UserCreated(Event):
    """Event emitted when a new user is created in the system."""
    user_id: str = field(factory=lambda: uuid.uuid4().hex)
```

### Example 2: Complex Domain Event with Business Context

```python
# src/contexts/products_catalog/core/domain/events/updated_attr_that_reflect_on_recipes.py
from attrs import field, frozen
from src.contexts.seedwork.shared.domain.event import Event

@frozen(kw_only=True)
class UpdatedAttrOnProductThatReflectOnRecipeShoppingList(Event):
    """Event emitted when product attributes change that affect recipe shopping lists."""
    product_id: str
    message: str = field(hash=False, default="")  # Additional context
```

### Example 3: Event Handler Implementation

```python
# src/contexts/iam/core/services/event_handlers.py
from src.contexts.iam.core.domain.events import UserCreated
from src.logging.logger import logger

async def publish_send_admin_new_user_notification(event: UserCreated) -> None:
    """
    Handle user creation by sending notification to administrators.
    
    This is an example of a cross-cutting concern handled through domain events.
    The user creation logic doesn't need to know about notification requirements.
    """
    logger.info(f"Sending admin notification for new user: {event.user_id}")
    
    # In a full implementation, this would:
    # 1. Load admin user list
    # 2. Create notification messages
    # 3. Send via email/SMS/in-app notifications
    # 4. Log notification delivery status
    
    # For now, this is a placeholder
    # TODO: implement actual notification logic
    pass
```

### Example 4: Event Registration in Bootstrap

```python
# src/contexts/iam/core/bootstrap/bootstrap.py
from collections.abc import Coroutine
from functools import partial
from src.contexts.iam.core.domain import commands, events
from src.contexts.iam.core.services import command_handlers as cmd_handlers
from src.contexts.iam.core.services import event_handlers as evt_handlers

def bootstrap(uow: UnitOfWork) -> MessageBus:
    """Bootstrap the IAM context with command and event handlers."""
    
    # Event handlers - can have multiple handlers per event
    injected_event_handlers: dict[type[SeedworkEvent], list[partial[Coroutine]]] = {
        events.UserCreated: [
            partial(evt_handlers.publish_send_admin_new_user_notification),
        ],
    }

    # Command handlers - exactly one handler per command
    injected_command_handlers: dict[type[SeedworkCommand], partial[Coroutine]] = {
        commands.CreateUser: partial(cmd_handlers.create_user, uow=uow),
        commands.AssignRoleToUser: partial(cmd_handlers.assign_role_to_user, uow=uow),
        commands.RemoveRoleFromUser: partial(cmd_handlers.remove_role_from_user, uow=uow),
    }
    
    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
```

### Example 5: Event Generation in Domain Entity

```python
# src/contexts/iam/core/domain/root_aggregate/user.py (excerpt)
from src.contexts.iam.core.domain.events import UserCreated
from src.contexts.seedwork.shared.domain.entity import Entity

class User(Entity):
    def __init__(self, id: str, roles: list[Role] | None = None, **kwargs):
        super().__init__(id=id, **kwargs)
        self._id = id
        self._roles: list[Role] = roles if roles else [Role.user()]
        self.events: list[Event] = []  # Events collection

    @classmethod
    def create_user(cls, id: str) -> User:
        """Factory method that generates domain events."""
        # Create the event first
        event = UserCreated(user_id=id)
        
        # Create the user entity
        user = cls(id=event.user_id)
        
        # Attach the event (commented out in actual code, but pattern is shown)
        # user.events.append(event)
        
        return user
```

### Example 6: Event Collection via Unit of Work

```python
# src/contexts/seedwork/shared/services/uow.py (excerpt)
class UnitOfWork(ABC):
    """Unit of Work that collects domain events from entities."""
    
    def collect_new_events(self):
        """Collect domain events from all tracked entities."""
        for attr_name in self.__dict__:
            attr = getattr(self, attr_name)
            if hasattr(attr, "seen"):  # Repository with tracked entities
                for obj in getattr(attr, "seen"):
                    if hasattr(obj, "events"):
                        while getattr(obj, "events"):
                            yield getattr(obj, "events").pop(0)
```

### Example 7: Event Processing in MessageBus

```python
# src/contexts/shared_kernel/services/messagebus.py (excerpt)
import anyio
from src.logging.logger import logger

class MessageBus(Generic[U]):
    async def _handle_event(self, event: Event, timeout: int = TIMEOUT):
        """Handle a domain event by dispatching to all registered handlers."""
        handlers = [handler for handler in self.event_handlers[type(event)]]
        
        with anyio.move_on_after(timeout) as scope:
            try:
                async with anyio.create_task_group() as tg:
                    for handler in handlers:
                        if isinstance(handler, partial):
                            handler_name = handler.func.__name__
                        else:
                            handler_name = handler.__name__
                        
                        logger.debug(f"Handling event {event} with handler {handler_name}")
                        tg.start_soon(self._completed, handler, event)
                        
            except* Exception as exc:
                logger.exception(f"Exception handling event {event}: {exc}")
        
        if scope.cancel_called:
            logger.warning(f"Event handling timed out for {event}")

    async def _completed(self, handler, message: Event | Command):
        """Execute handler and collect new events generated."""
        await handler(message)
        
        if isinstance(message, Command):
            # After command completion, process any new events
            new_events = self.uow.collect_new_events()
            for event in new_events:
                async with anyio.create_task_group() as tg:
                    tg.start_soon(self.handle, event)
```

### Domain Event Best Practices

✅ **Do use events for cross-aggregate communication**
```python
# Good - event enables loose coupling between aggregates
class Product(Entity):
    def update_name(self, new_name: str):
        self._name = new_name
        # Notify recipes that product name changed
        self.events.append(ProductNameChanged(product_id=self.id, new_name=new_name))
```

✅ **Do make events immutable with meaningful data**
```python
@frozen  # Immutable
class MealDeleted(Event):
    meal_id: str
    menu_id: str  # Include related context
    deleted_by: str  # Who performed the action
    deletion_reason: str | None = None  # Optional context
```

✅ **Do handle event failures gracefully**
```python
async def resilient_event_handler(event: UserCreated) -> None:
    try:
        # Main event handling logic
        await send_welcome_email(event.user_id)
    except EmailServiceError as e:
        # Don't fail the entire transaction for non-critical events
        logger.warning(f"Failed to send welcome email: {e}")
        # Could queue for retry, send to dead letter queue, etc.
```

❌ **Don't put business logic in event handlers that affects primary aggregates**
```python
# Wrong - event handler shouldn't modify the aggregate that generated the event
async def bad_user_created_handler(event: UserCreated, uow: UnitOfWork):
    user = await uow.users.get(event.user_id)
    user.assign_role(Role.VERIFIED)  # This should be a separate command
    await uow.users.persist(user)
```

❌ **Don't make events too granular**
```python
# Wrong - too many fine-grained events
class Recipe(Entity):
    def update_ingredients(self, ingredients: list[Ingredient]):
        for ingredient in ingredients:
            self.events.append(IngredientAdded(ingredient=ingredient))  # Too granular
        
        # Better - single event with all changes
        # self.events.append(RecipeIngredientsUpdated(recipe_id=self.id, ingredients=ingredients))
```

---

## Lambda Handler Patterns

AWS Lambda handlers provide the entry point for HTTP requests and integrate with the domain layer through commands and queries.

### Pattern Overview

Lambda handlers in this codebase follow these patterns:
- **Async/Sync Split** - Async business logic with sync Lambda wrapper
- **Exception Handling** - Decorator-based exception handling with proper HTTP responses
- **Authorization** - JWT token validation and permission checking
- **Command/Query Dispatch** - Route requests to domain layer via MessageBus
- **CORS Support** - Consistent CORS headers across all endpoints

### Example 1: Basic Query Handler (GET)

```python
# src/contexts/products_catalog/aws_lambda/get_product_by_id.py
import os
from typing import Any
import anyio

from src.contexts.products_catalog.core.adapters.api_schemas.root_aggregate.api_product import ApiProduct
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import lambda_exception_handler
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from .CORS_headers import CORS_headers

@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler to retrieve a specific product by ID."""
    logger.debug(f"Getting product by id: {event}")
    
    # Extract path parameters
    path_parameters = event.get("pathParameters") or {}
    product_id = path_parameters.get("id")
    
    if not product_id:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"error": "Product ID is required"}),
        }
    
    # Initialize application services
    container = Container()
    bus: MessageBus = container.bootstrap()

    # Query the domain
    async with bus.uow as uow:
        product = await uow.products.get(product_id)
        
    # Convert to API response format
    api_product = ApiProduct.from_domain(product)
    
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": api_product.model_dump_json(),
    }

def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Synchronous wrapper for AWS Lambda runtime."""
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
```

### Example 2: Command Handler with Authorization (POST)

```python
# src/contexts/recipes_catalog/aws_lambda/recipe/create_recipe.py
import json
import os
from typing import Any
import anyio

from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.api_create_recipe import ApiCreateRecipe
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import lambda_exception_handler
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from .CORS_headers import CORS_headers

@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler to create a new recipe."""
    logger.debug(f"Creating recipe with event: {event}")
    
    # Parse request body
    try:
        body_data = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"error": "Invalid JSON in request body"}),
        }
    
    # Convert to API schema for validation
    try:
        api_create_recipe = ApiCreateRecipe(**body_data)
    except ValidationError as e:
        return {
            "statusCode": 422,
            "headers": CORS_headers,
            "body": json.dumps({"error": "Validation failed", "details": str(e)}),
        }
    
    # Authorization check (skip in local development)
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims", {}).get("sub")
        
        if not user_id:
            return {
                "statusCode": 401,
                "headers": CORS_headers,
                "body": json.dumps({"error": "Unauthorized"}),
            }
        
        # Additional permission checks would go here
        # response = await IAMProvider.get(user_id)
        # if not user.has_permission(Permission.MANAGE_RECIPES):
        #     return 403 response
    
    # Convert to domain command
    command = api_create_recipe.to_domain()
    
    # Execute command
    bus: MessageBus = Container().bootstrap()
    await bus.handle(command)
    
    return {
        "statusCode": 201,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Recipe created successfully"}),
    }

def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Synchronous wrapper for AWS Lambda runtime."""
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
```

### Example 3: Query Handler with Filtering (GET)

```python
# src/contexts/products_catalog/aws_lambda/fetch_product_source_name.py  
import json
from typing import Any
import anyio

from src.contexts.products_catalog.core.adapters.api_schemas.entities.classifications.api_source import ApiSource
from src.contexts.products_catalog.core.adapters.api_schemas.queries.api_classification_filter import ApiClassificationFilter
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import lambda_exception_handler
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from .CORS_headers import CORS_headers

@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler to query product sources with filtering."""
    logger.debug(f"Event received: {event}")
    
    # Extract and process query parameters
    query_params = event.get("queryStringParameters") or {}
    
    # Convert query parameter names (kebab-case to snake_case)
    filters = {k.replace("-", "_"): v for k, v in query_params.items()}
    
    # Validate filters through API schema
    try:
        api_filter = ApiClassificationFilter(**filters)
        validated_filters = api_filter.model_dump()
        
        # Update filters with validated values
        for key, value in filters.items():
            filters[key] = validated_filters.get(key, value)
            
    except ValidationError as e:
        return {
            "statusCode": 422,
            "headers": CORS_headers,
            "body": json.dumps({"error": "Invalid filter parameters", "details": str(e)}),
        }
    
    # Execute query
    bus: MessageBus = Container().bootstrap()
    
    async with bus.uow as uow:
        logger.debug(f"Querying product sources with filters: {filters}")
        sources = await uow.sources.query(filter=filters)
    
    logger.debug(f"Sources found: {len(sources)}")
    
    # Convert to API response format
    api_sources = [ApiSource.from_domain(source) for source in sources]
    
    # Create response body (specific format for this endpoint)
    response_body = {source.id: source.name for source in api_sources}
    
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps(response_body),
    }

def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Synchronous wrapper for AWS Lambda runtime."""
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
```

### Example 4: Exception Handling Decorator

```python
# src/contexts/seedwork/shared/endpoints/decorators/lambda_exception_handler.py
import json
from functools import wraps
from typing import Any, Callable
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
)
from src.logging.logger import logger

def lambda_exception_handler(func: Callable) -> Callable:
    """
    Decorator to handle exceptions in Lambda handlers with proper HTTP responses.
    
    This decorator catches common exceptions and converts them to appropriate
    HTTP status codes and error messages.
    """
    @wraps(func)
    async def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
        try:
            return await func(event, context)
            
        except EntityNotFoundException as e:
            logger.warning(f"Entity not found: {e}")
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Resource not found"}),
            }
            
        except MultipleEntitiesFoundException as e:
            logger.error(f"Multiple entities found: {e}")
            return {
                "statusCode": 409,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Conflict: multiple resources found"}),
            }
            
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return {
                "statusCode": 422,
                "headers": {"Content-Type": "application/json"},  
                "body": json.dumps({"error": "Validation failed", "details": str(e)}),
            }
            
        except PermissionError as e:
            logger.warning(f"Permission denied: {e}")
            return {
                "statusCode": 403,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Permission denied"}),
            }
            
        except Exception as e:
            logger.exception(f"Unexpected error in Lambda handler: {e}")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Internal server error"}),
            }
    
    return wrapper
```

### Example 5: CORS Headers Configuration

```python
# src/contexts/*/aws_lambda/CORS_headers.py
CORS_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Content-Type": "application/json",
}
```

### Lambda Handler Best Practices

✅ **Do separate async business logic from sync Lambda wrapper**
```python
@lambda_exception_handler
async def async_handler(event, context):
    # All business logic here
    pass

def lambda_handler(event, context):
    # Simple sync wrapper
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
```

✅ **Do validate input data with API schemas**
```python
try:
    api_request = ApiCreateRecipe(**body_data)
    command = api_request.to_domain()
except ValidationError as e:
    return 422_response(e)
```

✅ **Do handle authorization consistently**
```python
# Check for local development
is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
if not is_localstack:
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    # Verify permissions
```

❌ **Don't put business logic in Lambda handlers**
```python
# Wrong - business logic in Lambda handler
async def async_handler(event, context):
    # Complex business logic here
    if user.role == "admin":
        # ... business rules ...
    
# Right - delegate to domain layer
async def async_handler(event, context):
    command = api_request.to_domain()
    await bus.handle(command)  # Business logic in command handler
```

❌ **Don't forget correlation IDs for tracing**
```python
# Wrong - no correlation ID
def lambda_handler(event, context):
    return anyio.run(async_handler, event, context)

# Right - generate correlation ID for tracing
def lambda_handler(event, context):
    generate_correlation_id()  # Essential for distributed tracing
    return anyio.run(async_handler, event, context)
```

--- 

## Simple Domain Property Addition

Complete guide for adding simple properties to domain entities - the most common development task that doesn't require complex command patterns or caching strategies.

### Pattern Overview

Simple properties are basic attributes that:
- **Don't require complex computation** (unlike cached properties)
- **Don't trigger domain events** (unlike complex state changes)
- **Don't need cross-aggregate coordination** (unlike commands)
- **Are straightforward data attributes** with optional validation

### When to Use This Pattern

✅ **Use for simple properties when:**
- Adding basic flags (is_favorite, is_active, is_featured)
- Adding simple descriptive fields (color, priority, status)
- Adding user preferences (difficulty_preference, serving_size_preference)
- Adding metadata that doesn't affect other aggregates

❌ **Don't use for complex scenarios:**
- Properties requiring expensive computation → Use Cached Properties pattern
- Changes affecting multiple aggregates → Use Domain Events pattern
- New business operations → Use Adding a New Command pattern

### Example 1: Adding `is_favorite` Flag to Meal

This addresses the most common use case identified during onboarding testing.

#### Step 1: Add Property to Entity

```python
# src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py
from attrs import field

@frozen
class _Meal(Entity):
    """Meal aggregate root with simple property addition."""
    
    # ... existing fields ...
    _is_favorite: bool = field(default=False, alias="is_favorite")
    
    # Property accessor
    @property
    def is_favorite(self) -> bool:
        """Whether this meal is marked as favorite by the user."""
        self._check_not_discarded()
        return self._is_favorite
    
    # Property setter (if mutable behavior needed)
    def mark_as_favorite(self, user_id: str) -> None:
        """Mark this meal as favorite."""
        self._check_not_discarded()
        
        # Optional: Add business rule validation
        if not user_id:
            raise ValueError("User ID required to mark favorite")
            
        # Create new instance with updated property (immutable pattern)
        object.__setattr__(self, '_is_favorite', True)
        self._increment_version()
        
        # Optional: Log the change for audit trail
        logger.info(f"Meal {self.id} marked as favorite by user {user_id}")
    
    def unmark_as_favorite(self, user_id: str) -> None:
        """Remove favorite status from this meal."""
        self._check_not_discarded()
        object.__setattr__(self, '_is_favorite', False)
        self._increment_version()
```

#### Step 2: Update Repository Methods (if needed)

```python
# src/contexts/recipes_catalog/core/repositories/meal_repository.py
from src.contexts.recipes_catalog.core.repositories.base import SaGenericRepository

class SaMealRepository(SaGenericRepository[Meal]):
    """Extended meal repository with favorite filtering."""
    
    async def get_favorite_meals(self, user_id: str) -> list[Meal]:
        """Get all meals marked as favorite by user."""
        filters = [
            self._model.is_favorite == True,
            self._model.user_id == user_id  # Assuming meals are user-scoped
        ]
        return await self._get_by_filters(filters)
```

#### Step 3: Add Simple Unit Tests

```python
# tests/unit/contexts/recipes_catalog/core/domain/meal/test_meal_favorite.py
import pytest
from unittest.mock import Mock

from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal

class TestMealFavorite:
    """Test simple favorite property functionality."""
    
    def test_meal_default_not_favorite(self):
        """New meals should not be favorite by default."""
        meal = Mock(spec=Meal)
        meal.is_favorite = False
        
        assert not meal.is_favorite
    
    def test_mark_meal_as_favorite(self):
        """Should be able to mark meal as favorite."""
        meal = Mock(spec=Meal)
        user_id = "user-123"
        
        meal.mark_as_favorite(user_id)
        meal.is_favorite = True
        
        assert meal.is_favorite
    
    def test_unmark_meal_as_favorite(self):
        """Should be able to unmark meal as favorite."""
        meal = Mock(spec=Meal)
        meal.is_favorite = True
        user_id = "user-123"
        
        meal.unmark_as_favorite(user_id)
        meal.is_favorite = False
        
        assert not meal.is_favorite
    
    def test_mark_favorite_requires_user_id(self):
        """Marking favorite should require valid user ID."""
        meal = Mock(spec=Meal)
        
        with pytest.raises(ValueError, match="User ID required"):
            meal.mark_as_favorite("")
```

### Example 2: Adding Priority Level with Validation

More complex simple property with business rules and validation.

```python
# Adding priority to Recipe entity
from enum import Enum

class RecipePriority(Enum):
    LOW = "low"
    MEDIUM = "medium"  
    HIGH = "high"
    URGENT = "urgent"

@frozen
class _Recipe(Entity):
    # ... existing fields ...
    _priority: RecipePriority = field(default=RecipePriority.MEDIUM, alias="priority")
    
    @property
    def priority(self) -> RecipePriority:
        """Recipe priority level for meal planning."""
        self._check_not_discarded()
        return self._priority
    
    def set_priority(self, priority: RecipePriority, user_id: str) -> None:
        """Set recipe priority with validation."""
        self._check_not_discarded()
        
        # Validation
        if not isinstance(priority, RecipePriority):
            raise ValueError(f"Invalid priority: {priority}")
            
        # Business rule: Only high-priority recipes during busy weeks
        current_week_meal_count = self._get_week_meal_count()
        if current_week_meal_count > 10 and priority not in [RecipePriority.HIGH, RecipePriority.URGENT]:
            raise BusinessRuleViolationError("Busy weeks require high-priority recipes only")
        
        object.__setattr__(self, '_priority', priority)
        self._increment_version()
```

### Example 3: Adding User Preference with Default Values

```python
# Adding serving size preference to Meal
@frozen
class _Meal(Entity):
    # ... existing fields ...
    _preferred_serving_size: int = field(default=4, alias="preferred_serving_size")
    
    @property  
    def preferred_serving_size(self) -> int:
        """Preferred number of servings for this meal."""
        self._check_not_discarded()
        return self._preferred_serving_size
    
    def set_preferred_serving_size(self, size: int) -> None:
        """Set preferred serving size with validation."""
        self._check_not_discarded()
        
        if size < 1 or size > 20:
            raise ValueError("Serving size must be between 1 and 20")
            
        object.__setattr__(self, '_preferred_serving_size', size)
        self._increment_version()
```

### Pattern Benefits

1. **Simplicity** - No complex infrastructure needed
2. **Performance** - No caching overhead for simple values  
3. **Maintainability** - Easy to understand and modify
4. **Testability** - Straightforward unit testing
5. **Domain Clarity** - Clear property semantics

### Best Practices

#### ✅ **Do: Follow Naming Conventions**
```python
# Clear, descriptive property names
@property
def is_vegetarian(self) -> bool: ...

@property  
def difficulty_level(self) -> DifficultyLevel: ...

@property
def estimated_prep_time_minutes(self) -> int: ...
```

#### ✅ **Do: Add Validation When Appropriate**
```python
def set_serving_size(self, size: int) -> None:
    if size < 1:
        raise ValueError("Serving size must be positive")
    # ... update property
```

#### ✅ **Do: Use Type Hints and Enums**
```python
from enum import Enum

class MealType(Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch" 
    DINNER = "dinner"
    SNACK = "snack"

_meal_type: MealType = field(default=MealType.DINNER)
```

#### ✅ **Do: Provide Default Values**
```python
# Sensible defaults prevent null/undefined issues
_is_active: bool = field(default=True)
_priority: Priority = field(default=Priority.MEDIUM)
_created_at: datetime = field(factory=datetime.utcnow)
```

### Common Pitfalls

#### ❌ **Don't: Add Properties That Should Be Computed**
```python
# Wrong - this should be computed from recipes
@property
def total_calories(self) -> int:
    return self._total_calories  # This could get out of sync
```

✅ **Instead: Use Cached Property for Computations**
```python
@cached_property
def total_calories(self) -> int:
    return sum(recipe.calories for recipe in self.recipes)
```

#### ❌ **Don't: Skip Validation for Critical Properties**
```python
# Wrong - no validation
def set_max_temperature(self, temp: int) -> None:
    self._max_temp = temp  # Could be unsafe value
```

✅ **Do: Add Appropriate Validation**
```python
def set_max_temperature(self, temp: int) -> None:
    if temp < 0 or temp > 500:
        raise ValueError("Temperature must be between 0-500°F")
    self._max_temp = temp
```

#### ❌ **Don't: Use Simple Properties for Complex State Changes**
```python
# Wrong - publishing should trigger events
def set_published(self, is_published: bool) -> None:
    self._is_published = is_published  # Missing domain events
```

✅ **Do: Use Commands for Complex Operations**
```python
# Use PublishMeal command instead for proper event handling
```

### Integration with Other Patterns

**When Simple Properties Aren't Enough:**

1. **Need computation?** → Use [Cached Properties](#implementing-cached-properties)
2. **Need cross-aggregate coordination?** → Use [Domain Events](#domain-event-implementation)  
3. **Complex business operation?** → Use [Commands](#adding-a-new-command)
4. **Database queries involved?** → Use [Repository Methods](#repository-method-implementation)

### Testing Strategy

```python
# Simple properties need basic unit tests
def test_property_default_value():
    """Test default value is correct."""
    
def test_property_setter_valid_input():
    """Test setter accepts valid values."""
    
def test_property_setter_invalid_input(): 
    """Test setter rejects invalid values."""
    
def test_property_business_rules():
    """Test any business rules are enforced."""
```

This pattern fills the gap between basic entity definition and complex behavioral patterns, providing a clear path for the most common development task: adding simple properties to domain entities.

---

## 📚 Related Documents

### Essential Context
- **[Quick Start Guide](./quick-start-guide.md)** - Foundation for using these patterns effectively
- **[AI Agent Workflows](./ai-agent-workflows.md)** - Step-by-step processes for implementing these patterns
- **[Technical Specifications](./technical-specifications.md)** - Data models and APIs these patterns implement

### Advanced Implementation
- **[Decision Trees](./decision-trees.md)** - Choosing the right pattern for complex scenarios
- **[Domain Rules Reference](./domain-rules-reference.md)** - Business constraints that shape pattern implementation
- **[Troubleshooting Guide](./troubleshooting-guide.md)** - Debug issues when implementing patterns

### Architecture Context
- **[System Architecture Diagrams](./system-architecture-diagrams.md)** - How these patterns fit into the overall system
- **[Documentation Index](./README.md)** - Complete navigation to all available documentation