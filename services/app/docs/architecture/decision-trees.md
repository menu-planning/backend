# Decision Trees for AI Agent Development

A comprehensive guide to common development decisions in the menu planning backend architecture. These decision trees help AI agents make appropriate architectural choices quickly and consistently.

## Overview

This document provides decision trees and flowcharts for common development scenarios:

1. **Which Aggregate to Modify?** - Domain model decisions
2. **Should I Cache This?** - Performance optimization decisions  
3. **Test Strategy Selection** - Testing approach decisions
4. **Repository vs Direct Query** - Data access decisions
5. **Event vs Direct Call** - Communication pattern decisions
6. **Performance Optimization Priority** - Optimization strategy decisions

Each decision tree includes:
- **Decision Logic**: Step-by-step decision flow
- **Code Examples**: Real codebase examples
- **Performance Notes**: Performance implications
- **Common Pitfalls**: What to avoid
- **Quick Reference**: Summary tables

## 1. Which Aggregate to Modify?

### Decision Tree

```
🎯 NEED TO MODIFY DATA?
    │
    ├─ What type of data are you modifying?
    │   
    ├─ MEAL DATA (name, description, nutrition, etc.)
    │   ├─ Does it affect menu display?
    │   │   ├─ ✅ YES → Modify `Meal` aggregate
    │   │   │   └─ Event: UpdatedAttrOnMealThatReflectOnMenu
    │   │   └─ ❌ NO → Modify `Meal` aggregate  
    │   │       └─ Event: (none needed)
    │   
    ├─ RECIPE DATA (ingredients, instructions, ratings)
    │   ├─ Part of existing meal?
    │   │   ├─ ✅ YES → Access via `Meal` aggregate
    │   │   │   └─ meal.update_recipes() or meal.create_recipe()
    │   │   └─ ❌ NO → Invalid - Recipes must belong to meals
    │   
    ├─ MENU DATA (meal positioning, client assignment)
    │   ├─ Affects meal-menu relationships?
    │   │   ├─ ✅ YES → Modify `Menu` aggregate  
    │   │   │   └─ Event: MenuMealAddedOrRemoved
    │   │   └─ ❌ NO → Modify `Menu` aggregate
    │   │       └─ Event: (varies by change)
    │   
    ├─ USER/CLIENT DATA (profiles, preferences)
    │   └─ → Modify `Client` or `User` aggregate (IAM context)
    │
    └─ CROSS-AGGREGATE Changes?
        ├─ Multiple aggregates affected?
        │   ├─ ✅ YES → Use Application Service
        │   │   └─ Coordinate via Unit of Work pattern
        │   └─ ❌ NO → Single aggregate modification
        │
        └─ 🔄 Return to specific aggregate decision above
```

### Code Examples

#### ✅ Correct: Modify Meal Aggregate

```python
# Modify meal properties that affect menu display
meal = await uow.meals.get(meal_id)
meal.update_properties(
    name="Updated Meal Name",      # Affects menu display
    description="New description"   # Internal change
)
await uow.meals.persist(meal)

# Result: UpdatedAttrOnMealThatReflectOnMenu event generated
# Menu will auto-update via event handler
```

#### ✅ Correct: Recipe Management via Meal

```python
# Add recipe to existing meal
meal = await uow.meals.get(meal_id)
meal.create_recipe(
    name="New Recipe",
    ingredients=[...],
    instructions="Mix and cook",
    author_id=meal.author_id,
    meal_id=meal.id
)
await uow.meals.persist(meal)

# Result: Meal aggregate maintains consistency
# Cache invalidation automatic
```

#### ✅ Correct: Menu Meal Management

```python
# Add meal to menu
menu = await uow.menus.get(menu_id)
menu_meal = MenuMeal(
    meal_id=meal_id,
    week=1,
    weekday="Seg", 
    meal_type="almoço"
)
menu.add_meal(menu_meal)
await uow.menus.persist(menu)

# Result: MenuMealAddedOrRemoved event
# Meal.menu_id updated via event handler
```

#### ❌ Wrong: Direct Entity Modification

```python
# DON'T DO THIS - Bypasses aggregate boundaries
recipe = await uow.recipes.get(recipe_id)  # ❌ No direct recipe repo
recipe.name = "Changed"  # ❌ Bypasses meal aggregate
await uow.recipes.persist(recipe)  # ❌ Breaks consistency
```

### Performance Notes

| Aggregate | Cache Impact | Event Cost | Recommended Pattern |
|-----------|--------------|------------|-------------------|
| **Meal** | Medium | Low-Medium | Direct modification |
| **Recipe** | High | None | Via Meal aggregate |
| **Menu** | Low | Medium | Direct modification |
| **Cross-Aggregate** | Varies | High | Application Service |

### Quick Reference

| **I need to...** | **Use Aggregate** | **Key Method** | **Events Generated** |
|-------------------|-------------------|----------------|-------------------|
| Change meal name/description | `Meal` | `update_properties()` | UpdatedAttrOnMealThatReflectOnMenu |
| Add/modify recipes | `Meal` | `create_recipe()`, `update_recipes()` | (menu event if name changes) |
| Position meals in menu | `Menu` | `add_meal()`, `update_meal()` | MenuMealAddedOrRemoved |
| Delete meal | `Meal` | `delete()` | MealDeleted |
| Delete menu | `Menu` | `delete()` | MenuDeleted |
| Bulk operations | Application Service | UnitOfWork pattern | Multiple events |

---

*Continue reading for additional decision trees...* 

## 2. Should I Cache This?

### Decision Flowchart

```
🤔 CONSIDERING CACHING?
    │
    ├─ What type of computation/data?
    │   
    ├─ 📊 COMPUTED PROPERTY (nutrition, averages, totals)
    │   ├─ Expensive calculation? (>5ms)
    │   │   ├─ ✅ YES → Use @cached_property ⚡
    │   │   │   ├─ Instance-level data?
    │   │   │   │   ├─ ✅ YES → Perfect fit!
    │   │   │   │   └─ ❌ NO → Consider repository cache
    │   │   │   └─ Add _invalidate_caches() on mutations
    │   │   │
    │   │   └─ ❌ NO → Skip caching (overhead > benefit)
    │   
    ├─ 🔍 DATABASE QUERIES (repository calls)
    │   ├─ Frequently called with same params?
    │   │   ├─ ✅ YES → Repository-level caching 🏪
    │   │   │   ├─ Data changes frequently?
    │   │   │   │   ├─ ✅ YES → Short TTL (60s)
    │   │   │   │   └─ ❌ NO → Long TTL (300s+)
    │   │   │   └─ Implement _build_cache_key()
    │   │   │
    │   │   └─ ❌ NO → No caching needed
    │   
    ├─ 📋 LOOKUP DICTIONARIES (ID→Entity maps)
    │   ├─ Collection changes infrequently?
    │   │   ├─ ✅ YES → @cached_property perfect ✨
    │   │   │   └─ Invalidate on collection changes
    │   │   └─ ❌ NO → Real-time computation
    │   
    └─ 🌐 EXTERNAL API CALLS (third-party data)
        ├─ Stable data with rate limits?
        │   ├─ ✅ YES → Redis/Application cache 🌍
        │   │   └─ TTL based on data freshness needs
        │   └─ ❌ NO → Direct calls only

🎯 CACHE INVALIDATION STRATEGY:
    │
    ├─ WHEN should cache clear?
    │   ├─ On specific property changes → _invalidate_caches('property_name')
    │   ├─ On any entity change → _invalidate_caches()  # Clear all
    │   └─ Time-based → TTL expiration
    │
    └─ HOW to detect changes?
        ├─ Property setters → Call invalidation
        ├─ update_properties() → Auto-invalidation
        └─ Repository persist → Entity-level invalidation
```

### Caching Patterns in Codebase

#### ✅ Instance-Level Caching (@cached_property)

```python
class Meal(Entity):
    @cached_property
    def nutri_facts(self) -> NutriFacts | None:
        """Aggregate nutrition from all recipes.
        
        Cache invalidation triggers:
        - recipes setter: When recipes collection changes
        - create_recipe(): When recipe added
        - delete_recipe(): When recipe removed
        """
        if not self.recipes:
            return None
            
        total_calories = sum(r.nutri_facts.calories for r in self.recipes if r.nutri_facts)
        total_protein = sum(r.nutri_facts.protein for r in self.recipes if r.nutri_facts)
        # ... aggregate all nutrition values
        
        return NutriFacts(calories=total_calories, protein=total_protein, ...)

    def create_recipe(self, **kwargs):
        """Add recipe and invalidate affected caches."""
        recipe = Recipe.create_recipe(**kwargs)
        self._recipes.append(recipe)
        self._invalidate_caches('nutri_facts')  # Clear nutrition cache
        self._increment_version()
```

#### ✅ Repository-Level Caching (Future Implementation)

```python
class SaGenericRepository:
    async def query(self, filter=None, **kwargs):
        """Query with caching support."""
        # Build cache key from parameters
        cache_key = self._build_cache_key(filter=filter, **kwargs)
        
        # Try cache first
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
            
        # Execute query
        result = await self._execute_query(filter, **kwargs)
        
        # Store in cache
        self._set_cache(cache_key, result, ttl=300)
        return result
```

#### ✅ Lookup Dictionary Caching

```python
class Menu(Entity):
    @cached_property
    def _meals_by_id_lookup(self) -> dict[str, MenuMeal]:
        """O(1) meal lookup by ID."""
        return {meal.meal_id: meal for meal in self._meals}
    
    @cached_property
    def meals_dict(self) -> dict[tuple[int, str, str], MenuMeal]:
        """O(1) meal lookup by (week, weekday, meal_type)."""
        return {
            (meal.week, meal.weekday, meal.meal_type): meal 
            for meal in self._meals
        }
    
    def add_meal(self, meal: MenuMeal):
        """Add meal and invalidate lookup caches."""
        self._meals.add(meal)
        self._invalidate_caches('_meals_by_id_lookup', 'meals_dict')
```

### Performance Impact Analysis

| Pattern | Setup Cost | Access Cost | Memory Usage | Cache Hit Ratio |
|---------|------------|-------------|--------------|----------------|
| **@cached_property** | O(n) first access | O(1) subsequent | Per-instance | 95-100% |
| **Repository cache** | O(1) storage | O(1) lookup | Shared pool | 80-95% |
| **Lookup dict** | O(n) dict build | O(1) lookup | Per-instance | 100% |
| **No caching** | O(1) | O(n) every time | None | N/A |

### When NOT to Cache

#### ❌ Avoid Caching When:

```python
# Simple property access - no computation
@property
def name(self) -> str:
    return self._name  # ❌ Don't cache - just field access

# Frequently changing data
@property 
def current_timestamp(self) -> datetime:
    return datetime.now()  # ❌ Don't cache - always changes

# Cheap computations
@property
def full_name(self) -> str:
    return f"{self.first_name} {self.last_name}"  # ❌ Don't cache - string concat is fast

# One-time use data
def generate_report_id(self) -> str:
    return uuid.uuid4().hex  # ❌ Don't cache - used once
```

### Cache Invalidation Examples

#### Targeted Invalidation

```python
def _set_recipes(self, value: list[Recipe]):
    """Update recipes and invalidate only affected caches."""
    self._recipes = value
    # Only invalidate nutrition-related caches
    self._invalidate_caches('nutri_facts', 'macro_division', 'weight_in_grams')
    self._increment_version()
```

#### Bulk Invalidation

```python  
def update_properties(self, **kwargs):
    """Update multiple properties - invalidate all caches for safety."""
    super().update_properties(**kwargs)
    # Clear all caches since we don't know what changed
    self._invalidate_caches()  # No args = clear all
```

### Quick Reference

| **Cache This** | **Pattern** | **Invalidate When** | **Performance Gain** |
|----------------|-------------|-------------------|-------------------|
| Aggregated nutrition | `@cached_property` | Recipe changes | 30-100x |
| Rating averages | `@cached_property` | New ratings | 10-50x |
| ID lookup maps | `@cached_property` | Collection changes | 5-20x |
| Repository queries | Future cache layer | Data mutations | 3-10x |
| **Don't Cache** | **Reason** | **Alternative** | **Notes** |
| Simple properties | No computation | Direct access | Caching overhead > benefit |
| Changing data | Always stale | Real-time computation | Timestamp, counters, etc. |
| One-time use | No reuse | Direct computation | UUIDs, temporary values |

--- 

## 3. Test Strategy Selection

### Decision Matrix

```
🧪 WHAT TO TEST?
    │
    ├─ What are you implementing?
    │   
    ├─ 🎯 DOMAIN ENTITY/VALUE OBJECT (business logic)
    │   ├─ Complex business rules?
    │   │   ├─ ✅ YES → Unit Tests + Domain Tests 🏗️
    │   │   │   ├─ Test business rule validation
    │   │   │   ├─ Test state transitions  
    │   │   │   ├─ Test aggregate boundaries
    │   │   │   └─ Mock external dependencies
    │   │   │
    │   │   └─ ❌ NO → Simple Unit Tests
    │   │       └─ Focus on property behavior
    │   
    ├─ 🗃️ REPOSITORY/DATA ACCESS (persistence layer)  
    │   ├─ Custom query logic?
    │   │   ├─ ✅ YES → Integration Tests 🔗
    │   │   │   ├─ Real database required
    │   │   │   ├─ Test actual SQL generation
    │   │   │   ├─ Test constraint violations
    │   │   │   └─ Performance benchmarks
    │   │   │
    │   │   └─ ❌ NO → Basic CRUD Tests
    │   │       └─ Test standard operations
    │   
    ├─ ⚡ PERFORMANCE CRITICAL CODE (caching, aggregation)
    │   ├─ Performance requirements?
    │   │   ├─ ✅ YES → Performance Tests 📊
    │   │   │   ├─ Benchmark current implementation
    │   │   │   ├─ Set performance thresholds
    │   │   │   ├─ Test with realistic data sizes
    │   │   │   └─ Monitor cache hit ratios
    │   │   │
    │   │   └─ ❌ NO → Standard test approach
    │   
    ├─ 🌐 API ENDPOINTS (Lambda handlers)
    │   ├─ Complex request/response logic?
    │   │   ├─ ✅ YES → E2E Tests 🎭
    │   │   │   ├─ Full request lifecycle
    │   │   │   ├─ Authentication/authorization
    │   │   │   ├─ Error response formats
    │   │   │   └─ Integration with services
    │   │   │
    │   │   └─ ❌ NO → API Contract Tests
    │   │       └─ Request/response validation
    │   
    └─ 🔄 EVENT HANDLERS (domain events)
        ├─ Cross-aggregate coordination?
        │   ├─ ✅ YES → Integration + E2E Tests 🔗🎭
        │   │   ├─ Test event generation
        │   │   ├─ Test event handling
        │   │   ├─ Test eventual consistency
        │   │   └─ Test failure scenarios
        │   │
        │   └─ ❌ NO → Unit Tests
        │       └─ Mock dependencies
        
🎯 TEST COVERAGE TARGETS:
    │
    ├─ Domain Layer → 95%+ (critical business logic)
    ├─ Repository Layer → 90%+ (data integrity)  
    ├─ API Layer → 85%+ (user interface)
    └─ Event Handlers → 90%+ (system coordination)
```

### Test Strategy by Component

#### 🏗️ Domain Entity Tests

```python
class TestMealDomainBehavior:
    """Test meal business rules and aggregate behavior."""
    
    def test_meal_creation_generates_menu_event_when_menu_id_provided(self):
        """Domain rule: Meal creation with menu_id generates update event."""
        # Given: Meal creation parameters with menu
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="user-123", 
            meal_id="meal-456",
            menu_id="menu-789"  # Key: has menu association
        )
        
        # Then: Should generate menu update event
        update_events = [e for e in meal.events 
                        if isinstance(e, UpdatedAttrOnMealThatReflectOnMenu)]
        assert len(update_events) == 1
        assert update_events[0].menu_id == "menu-789"
        assert update_events[0].meal_id == "meal-456"
    
    def test_meal_creation_without_menu_id_skips_event_generation(self):
        """Domain rule: No menu events when meal not associated with menu."""
        # Given: Meal creation without menu association
        meal = Meal(
            id="meal-123",
            name="Standalone Meal",
            author_id="user-456",
            menu_id=None  # Key: no menu association
        )
        
        # When: Modifying meal properties
        meal.update_properties(name="Updated Name")
        
        # Then: No menu events should be generated
        menu_events = [e for e in meal.events 
                      if isinstance(e, UpdatedAttrOnMealThatReflectOnMenu)]
        assert len(menu_events) == 0
```

#### 🔗 Repository Integration Tests

```python
class TestMealRepositoryIntegration:
    """Test repository with real database operations."""
    
    @pytest.mark.integration
    async def test_complex_meal_filtering_with_joins(self, meal_repository, test_session):
        """Test complex filtering logic with actual database."""
        # Given: Meals with recipes and tags in real database
        meal = create_test_ORM_meal(name="Complex Test Meal")
        test_session.add(meal)
        await test_session.flush()
        
        recipe = create_test_ORM_recipe(name="Test Recipe", meal_id=meal.id)
        test_session.add(recipe)
        await test_session.commit()
        
        # When: Performing complex filter query
        results = await meal_repository.query(
            filter={
                "recipe_name": "Test Recipe",
                "author_id": meal.author_id
            },
            _return_sa_instance=True
        )
        
        # Then: Should return correct results from real database
        assert len(results) == 1
        assert results[0].name == "Complex Test Meal"
        
    @timeout_test(30.0)  # Performance constraint
    async def test_repository_performance_with_large_dataset(
        self, meal_repository, large_test_dataset
    ):
        """Test repository performance with realistic data volume."""
        # When: Querying large dataset with complex filters  
        with benchmark_timer() as timer:
            results = await meal_repository.query(
                filter={"total_time_gte": 30, "calorie_density_gte": 200.0},
                limit=50
            )
        
        # Then: Should meet performance targets
        timer.assert_faster_than(2.0)  # 2 second max
        assert len(results) <= 50
```

#### 📊 Performance Tests

```python
class TestMealCachingPerformance:
    """Test caching performance with benchmarks."""
    
    def test_nutrition_aggregation_cache_performance(self, meal_with_recipes):
        """Test that nutrition caching provides expected performance gain."""
        # Given: Meal with multiple recipes requiring aggregation
        assert len(meal_with_recipes.recipes) >= 5  # Ensure significant computation
        
        # When: First access (cache miss)
        with benchmark_timer() as timer_cold:
            first_result = meal_with_recipes.nutri_facts
        
        # When: Second access (cache hit)
        with benchmark_timer() as timer_warm:
            second_result = meal_with_recipes.nutri_facts
        
        # Then: Cached access should be significantly faster
        cache_speedup = timer_cold.elapsed / timer_warm.elapsed
        assert cache_speedup > 10  # At least 10x faster cached
        assert first_result is second_result  # Same object (cached)
        
    def test_cache_invalidation_performance_impact(self, meal_with_recipes):
        """Test that cache invalidation doesn't degrade performance."""
        # Given: Cached nutrition facts
        _ = meal_with_recipes.nutri_facts  # Prime cache
        
        # When: Invalidating cache through recipe update
        with benchmark_timer() as timer:
            meal_with_recipes.create_recipe(
                name="Performance Test Recipe",
                ingredients=[],
                instructions="Test instructions",
                author_id=meal_with_recipes.author_id,
                meal_id=meal_with_recipes.id
            )
            
        # Then: Cache invalidation + new computation should be reasonable
        timer.assert_faster_than(0.010)  # 10ms max including invalidation
```

#### 🎭 End-to-End API Tests

```python
class TestMealAPIEndToEnd:
    """Test complete meal API workflow."""
    
    @pytest.mark.e2e
    async def test_meal_creation_api_workflow(self, api_client, test_database):
        """Test complete meal creation through API."""
        # Given: Valid meal creation request
        meal_data = {
            "name": "API Test Meal",
            "author_id": "user-123",
            "menu_id": "menu-456",
            "recipes": [
                {
                    "name": "API Test Recipe",
                    "ingredients": [
                        {"name": "Test Ingredient", "quantity": 1.0, "unit": "cup"}
                    ],
                    "instructions": "Mix and serve"
                }
            ]
        }
        
        # When: Making API request
        response = await api_client.post("/meals", json=meal_data)
        
        # Then: Should create meal successfully
        assert response.status_code == 201
        meal_response = response.json()
        
        # And: Should be retrievable via API
        get_response = await api_client.get(f"/meals/{meal_response['id']}")
        assert get_response.status_code == 200
        
        # And: Should have correct structure and data
        retrieved_meal = get_response.json()
        assert retrieved_meal["name"] == "API Test Meal"
        assert len(retrieved_meal["recipes"]) == 1
        assert retrieved_meal["recipes"][0]["name"] == "API Test Recipe"
```

### Test Organization Structure

```
tests/contexts/recipes_catalog/
├── unit/                           # Fast, isolated tests
│   ├── domain/
│   │   ├── test_meal_entity.py     # Business logic tests
│   │   ├── test_recipe_entity.py   # Entity behavior tests  
│   │   └── test_value_objects.py   # Value object tests
│   ├── adapters/
│   │   └── test_api_schemas.py     # Serialization tests
│   └── services/  
│       └── test_command_handlers.py # Service logic tests
│
├── integration/                    # Database + external dependencies
│   ├── repositories/
│   │   ├── test_meal_repository.py # Real database tests
│   │   └── test_query_performance.py # Performance benchmarks
│   ├── services/
│   │   └── test_uow_integration.py # Unit of work tests
│   └── events/
│       └── test_event_handlers.py  # Event processing tests
│
└── e2e/                           # Full system tests
    ├── api/
    │   ├── test_meal_endpoints.py  # HTTP API tests
    │   └── test_error_handling.py  # Error response tests
    └── workflows/
        └── test_meal_lifecycle.py  # Complete user scenarios
```

### Test Data Strategy

#### Domain Test Data (Fast)

```python
# Unit tests - use simple domain objects
def create_test_meal(name="Test Meal", **kwargs):
    """Create meal domain object for unit testing."""
    return Meal(
        id=kwargs.get('id', f"meal-{uuid.uuid4().hex}"),
        name=name,
        author_id=kwargs.get('author_id', 'test-author'),
        **kwargs
    )
```

#### Database Test Data (Real)

```python  
# Integration tests - use ORM models with real database
def create_test_ORM_meal(name="Test Meal", **kwargs):
    """Create meal ORM model for integration testing."""
    return MealSaModel(
        id=kwargs.get('id', f"meal-{uuid.uuid4().hex}"),
        name=name,
        author_id=kwargs.get('author_id', 'test-author'),
        created_at=datetime.utcnow(),
        **kwargs
    )
```

### Quick Reference

| **Component Type** | **Primary Test Strategy** | **Coverage Target** | **Key Focus Areas** |
|-------------------|-------------------------|-------------------|-------------------|
| **Domain Entities** | Unit + Domain Tests | 95%+ | Business rules, state transitions |
| **Repositories** | Integration Tests | 90%+ | Query logic, constraints, performance |
| **API Endpoints** | E2E Tests | 85%+ | Request/response, error handling |
| **Event Handlers** | Integration + E2E | 90%+ | Event flow, eventual consistency |
| **Caching Logic** | Performance Tests | 85%+ | Cache hits, invalidation, benchmarks |
| **Value Objects** | Unit Tests | 95%+ | Validation, immutability |

| **Test Type** | **Speed** | **Database** | **External Services** | **When to Use** |
|---------------|-----------|--------------|---------------------|----------------|
| **Unit** | Fast (ms) | Mocked | Mocked | Business logic, algorithms |
| **Integration** | Medium (100ms) | Real | Mocked | Repository queries, event handling |
| **E2E** | Slow (1s+) | Real | Real/Stubbed | User workflows, API contracts |
| **Performance** | Variable | Real | Mocked | Benchmarks, optimization validation |

--- 

## 4. Repository vs Direct Query

### Decision Guide

```
🗃️ NEED TO ACCESS DATA?
    │
    ├─ What type of data operation?
    │   
    ├─ 📖 SINGLE ENTITY ACCESS (by ID)
    │   ├─ Simple ID lookup?
    │   │   ├─ ✅ YES → Repository.get(id) ✨
    │   │   │   ├─ Built-in caching support
    │   │   │   ├─ Domain mapping included
    │   │   │   ├─ Relationship loading
    │   │   │   └─ Error handling standardized
    │   │   │
    │   │   └─ ❌ NO → Complex query needed below
    │   
    ├─ 🔍 FILTERED QUERIES (search, filter, sort)
    │   ├─ Domain-driven filtering needed?
    │   │   ├─ ✅ YES → Repository.query(filter={}) 🏗️
    │   │   │   ├─ Domain filter keys
    │   │   │   ├─ Join optimization
    │   │   │   ├─ Performance monitoring
    │   │   │   └─ Consistent error handling
    │   │   │
    │   │   └─ ❌ NO → Raw SQL edge case
    │   
    ├─ 📊 CUSTOM SQL/ANALYTICS (complex aggregations)
    │   ├─ Business logic in SQL?
    │   │   ├─ ✅ YES → Direct Query Builder 🛠️
    │   │   │   ├─ QueryBuilder(session, Model)
    │   │   │   ├─ Type-safe query construction
    │   │   │   ├─ Manual optimization control
    │   │   │   └─ Raw SQL for complex cases
    │   │   │
    │   │   └─ ❌ NO → Repository can handle it
    │   
    ├─ 🔄 BULK OPERATIONS (batch insert/update)
    │   ├─ Domain rules apply to all items?
    │   │   ├─ ✅ YES → Repository.persist_all() 📦
    │   │   │   ├─ Bulk domain validation
    │   │   │   ├─ Transaction management
    │   │   │   ├─ Event generation
    │   │   │   └─ Cache invalidation
    │   │   │
    │   │   └─ ❌ NO → Direct session bulk operations
    │   
    └─ 🎯 PERFORMANCE CRITICAL (high-frequency queries)
        ├─ Need maximum control over SQL?
        │   ├─ ✅ YES → Direct QueryBuilder + Session 🚀
        │   │   ├─ Eliminate repository overhead
        │   │   ├─ Custom caching strategies
        │   │   ├─ Manual query optimization
        │   │   └─ Skip domain mapping if needed
        │   │
        │   └─ ❌ NO → Repository with custom filters
        │       └─ Add specialized filter mappers
        
🎯 ARCHITECTURE DECISION FACTORS:
    │
    ├─ CONSISTENCY → Repository (domain rules enforced)
    ├─ PERFORMANCE → QueryBuilder (full control)
    ├─ MAINTAINABILITY → Repository (standardized patterns)
    ├─ COMPLEX LOGIC → QueryBuilder (custom SQL)
    └─ BULK OPERATIONS → Depends on domain rule complexity
```

### Access Patterns in Codebase

#### ✅ Repository Pattern (Recommended Default)

```python
# Single entity access - always use repository
async def get_meal_handler(meal_id: str, uow: UnitOfWork):
    """Standard entity access pattern."""
    try:
        meal = await uow.meals.get(meal_id)  # ✅ Repository handles everything
        return ApiMeal.from_domain(meal)
    except EntityNotFoundException:
        raise HTTPException(status_code=404, detail="Meal not found")

# Domain-driven filtering - use repository with filters
async def search_meals_handler(filters: dict, uow: UnitOfWork):
    """Business-logic filtering through repository."""
    meals = await uow.meals.query(filter={
        "author_id": filters["user_id"],
        "recipe_name": filters.get("recipe_name"),  # ✅ Domain filter keys
        "total_time_lte": filters.get("max_time"),
        "nutri_facts_calories_gte": filters.get("min_calories")
    })
    return [ApiMeal.from_domain(m) for m in meals]

# Bulk operations with domain validation
async def create_multiple_meals(meal_data_list: list, uow: UnitOfWork):
    """Bulk creation with domain rules."""
    meals = []
    for meal_data in meal_data_list:
        meal = Meal.create_meal(**meal_data)  # ✅ Domain validation
        meals.append(meal)
        await uow.meals.add(meal)
    
    await uow.meals.persist_all(meals)  # ✅ Bulk persistence + events
    await uow.commit()
```

#### ✅ QueryBuilder Pattern (Performance/Complex Queries)

```python
# Complex analytics query - use QueryBuilder
async def get_nutrition_analytics(session: AsyncSession, filters: dict):
    """Complex aggregation requiring custom SQL."""
    qb = QueryBuilder[Meal, MealSaModel](session, MealSaModel)
    
    result = await (qb
        .select()
        .join(RecipeSaModel, MealSaModel.recipes)  # ✅ Type-safe joins
        .where(GreaterThanOperator(), MealSaModel.created_at, filters["start_date"])
        .group_by(MealSaModel.author_id)
        .having(CountOperator(), MealSaModel.id, min_count=5)
        .order_by(MealSaModel.created_at, descending=True)
        .execute(_return_sa_instance=True))  # ✅ Skip domain mapping for analytics
    
    return result

# Performance-critical lookup - bypass repository overhead
async def get_meal_names_bulk(meal_ids: list[str], session: AsyncSession):
    """High-frequency name lookup - performance optimized."""
    if not meal_ids:
        return {}
        
    qb = QueryBuilder[Meal, MealSaModel](session, MealSaModel)
    results = await (qb
        .select(MealSaModel.id, MealSaModel.name)  # ✅ Only needed fields
        .where(InOperator(), MealSaModel.id, meal_ids)
        .execute(_return_sa_instance=True))
    
    return {r.id: r.name for r in results}  # ✅ Direct dict conversion
```

#### ✅ Direct Session (Raw SQL Edge Cases)

```python
# Raw SQL for database-specific optimizations
async def get_complex_meal_statistics(session: AsyncSession, params: dict):
    """Database-specific analytics requiring raw SQL."""
    sql = """
    WITH meal_stats AS (
        SELECT 
            m.author_id,
            COUNT(*) as meal_count,
            AVG(m.calorie_density) as avg_calories,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY m.total_time) as median_time
        FROM meals m
        WHERE m.created_at >= :start_date
        GROUP BY m.author_id
        HAVING COUNT(*) >= :min_meals
    )
    SELECT * FROM meal_stats ORDER BY avg_calories DESC
    """
    
    result = await session.execute(text(sql), params)
    return [dict(row) for row in result.fetchall()]
```

### Performance Comparison

| Access Pattern | Setup Cost | Query Cost | Type Safety | Domain Rules | Use When |
|----------------|------------|------------|-------------|--------------|----------|
| **Repository.get()** | Low | Low | High | ✅ Full | Standard CRUD |
| **Repository.query()** | Low | Medium | High | ✅ Full | Business filtering |
| **QueryBuilder** | Medium | Low-Medium | High | ❌ Manual | Complex queries |
| **Direct Session** | High | Low | Medium | ❌ None | Raw SQL needed |

### Repository Filter Examples

#### Standard Domain Filters

```python
# Meal repository supports these domain-oriented filters
meal_filters = {
    # Basic entity filters
    "name": "Pasta Primavera",
    "author_id": "user-123",
    "menu_id": "menu-456",
    
    # Recipe relationship filters (via joins)
    "recipe_name": "Chicken Alfredo",
    "recipe_id": "recipe-789",
    "ingredient_name": "tomatoes",
    
    # Numeric range filters
    "total_time_gte": 30,        # >= 30 minutes
    "total_time_lte": 60,        # <= 60 minutes
    "calorie_density_gte": 200.0,
    
    # Nutrition filters (nested object)
    "nutri_facts_calories_gte": 500,
    "nutri_facts_protein_gte": 20.0,
    
    # List filters (IN clause)
    "author_id": ["user-1", "user-2", "user-3"],
    "tags": ["vegetarian", "quick"],
    
    # Boolean filters
    "like": True,
    "discarded": False
}

# Usage
meals = await uow.meals.query(filter=meal_filters, limit=20)
```

#### Custom Filter Mappers

```python
# Adding custom domain filters to repository
class MealRepo(CompositeRepository[Meal, MealSaModel]):
    filter_to_column_mappers = [
        # Standard meal filters
        FilterColumnMapper(
            sa_model_type=MealSaModel,
            filter_key_to_column_name={
                "name": "name",
                "author_id": "author_id",
                "total_time": "total_time",
                "calorie_density": "calorie_density"
            }
        ),
        # Recipe filters (requires join)
        FilterColumnMapper(
            sa_model_type=RecipeSaModel,
            filter_key_to_column_name={
                "recipe_name": "name",
                "recipe_id": "id"
            },
            join_target_and_on_clause=[(RecipeSaModel, MealSaModel.recipes)]
        ),
        # Ingredient filters (requires multiple joins)
        FilterColumnMapper(
            sa_model_type=IngredientSaModel,
            filter_key_to_column_name={"ingredient_name": "name"},
            join_target_and_on_clause=[
                (RecipeSaModel, MealSaModel.recipes),
                (IngredientSaModel, RecipeSaModel.ingredients)
            ]
        )
    ]
```

### Error Handling Patterns

#### Repository Error Handling

```python
# Repository provides consistent error handling
try:
    meal = await uow.meals.get("invalid-id")
except EntityNotFoundException as e:
    # ✅ Consistent exception types
    logger.warning(f"Meal not found: {e.entity_id}")
    raise HTTPException(status_code=404)
except RepositoryQueryException as e:
    # ✅ Query-specific error context
    logger.error(f"Query failed: {e.message}", extra=e.context)
    raise HTTPException(status_code=500)
```

#### QueryBuilder Error Handling

```python
# QueryBuilder requires manual error handling
try:
    qb = QueryBuilder[Meal, MealSaModel](session, MealSaModel)
    results = await qb.select().where(...).execute()
except SQLAlchemyError as e:
    # ❌ Manual SQL error interpretation required
    if "foreign key" in str(e):
        raise HTTPException(status_code=400, detail="Invalid reference")
    elif "unique constraint" in str(e):
        raise HTTPException(status_code=409, detail="Duplicate entry")
    else:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500)
```

### Quick Reference

| **I need to...** | **Use Pattern** | **Key Method** | **Benefits** |
|-------------------|-----------------|----------------|--------------|
| Get entity by ID | Repository | `get(id)` | Caching, relationships, errors |
| Search/filter entities | Repository | `query(filter={})` | Domain filters, joins, consistency |
| Complex analytics | QueryBuilder | `select().join().where()` | SQL control, performance |
| Bulk operations | Repository | `persist_all()` | Domain validation, events |
| Raw SQL analytics | Direct Session | `execute(text(sql))` | Database-specific features |
| Performance critical | QueryBuilder | Custom optimization | Maximum control |

| **Consider Repository When** | **Consider QueryBuilder When** | **Consider Direct SQL When** |
|------------------------------|-------------------------------|------------------------------|
| ✅ Standard CRUD operations | ✅ Complex query logic needed | ✅ Database-specific features |
| ✅ Domain rules must apply | ✅ Performance is critical | ✅ Analytics/reporting |
| ✅ Consistent error handling | ✅ Custom joins required | ✅ Bulk data processing |
| ✅ Relationship loading | ✅ Raw SQL needed | ✅ Migration scripts |
| ✅ Event generation needed | ✅ Skip domain mapping | ✅ Performance debugging |

--- 

## 5. Event vs Direct Call

### Decision Tree

```
🔄 NEED TO COORDINATE BETWEEN COMPONENTS?
    │
    ├─ What type of coordination is needed?
    │   
    ├─ 📦 WITHIN SAME AGGREGATE (internal consistency)
    │   ├─ Immediate consistency required?
    │   │   ├─ ✅ YES → Direct Method Call 🔗
    │   │   │   ├─ meal.create_recipe()
    │   │   │   ├─ menu.add_meal()
    │   │   │   ├─ recipe.rate()
    │   │   │   └─ Synchronous validation
    │   │   │
    │   │   └─ ❌ NO → Still use direct calls (same aggregate)
    │   
    ├─ 🌐 CROSS-AGGREGATE COORDINATION (eventual consistency)
    │   ├─ Operations can be independent?
    │   │   ├─ ✅ YES → Domain Events 📡
    │   │   │   ├─ UpdatedAttrOnMealThatReflectOnMenu
    │   │   │   ├─ MealDeleted → MenuMealRemoved
    │   │   │   ├─ MenuMealAddedOrRemoved
    │   │   │   └─ Async event handlers
    │   │   │
    │   │   └─ ❌ NO → Application Service coordination
    │   
    ├─ ⚡ NOTIFICATION/LOGGING (side effects)
    │   ├─ Core operation success matters more than notification?
    │   │   ├─ ✅ YES → Domain Events 📢
    │   │   │   ├─ Email notifications
    │   │   │   ├─ Audit logging
    │   │   │   ├─ Analytics tracking
    │   │   │   └─ External API calls
    │   │   │
    │   │   └─ ❌ NO → Direct calls (critical notifications)
    │   
    └─ 🔄 COMPLEX WORKFLOWS (multi-step processes)
        ├─ Steps can fail independently?
        │   ├─ ✅ YES → Event-Driven Saga 🎭
        │   │   ├─ Order processing workflows
        │   │   ├─ Multi-aggregate updates
        │   │   ├─ Compensation logic
        │   │   └─ State machine patterns
        │   │
        │   └─ ❌ NO → Transaction Script/Service
        │       └─ Single transaction coordination

🎯 CONSISTENCY REQUIREMENTS:
    │
    ├─ STRONG CONSISTENCY → Direct calls within aggregate
    ├─ EVENTUAL CONSISTENCY → Events between aggregates  
    ├─ LOOSE COUPLING → Events for notifications
    └─ COMPLEX WORKFLOWS → Event-driven patterns
```

### Event Patterns in Codebase

#### ✅ Domain Events (Cross-Aggregate Coordination)

```python
# Meal aggregate generates events for menu updates
class Meal(Entity):
    def update_properties(self, **kwargs):
        """Update meal properties and notify menu of changes."""
        # Direct property updates (within aggregate)
        super().update_properties(**kwargs)
        
        # Generate domain event for menu coordination
        if self.menu_id:
            self.add_event_to_updated_menu("Updated meal properties")
            
    def add_event_to_updated_menu(self, message: str = ""):
        """Generate event when meal changes affect menu display."""
        if not self.menu_id:
            return
            
        # Domain event - asynchronous cross-aggregate coordination
        event = UpdatedAttrOnMealThatReflectOnMenu(
            menu_id=self.menu_id,
            meal_id=self.id,
            message=message
        )
        self.events.append(event)

    def delete(self):
        """Delete meal and notify menu via event."""
        # Direct state change (within aggregate)
        for recipe in self._recipes:
            recipe.delete()
            
        # Cross-aggregate notification via event
        if self.menu_id:
            self.events.append(MealDeleted(
                meal_id=self.id,
                menu_id=self.menu_id
            ))
        self._discard()
```

#### ✅ Event Handlers (Eventual Consistency)

```python
# Event handler coordinates between aggregates
async def update_menu_meals(
    evt: UpdatedAttrOnMealThatReflectOnMenu, 
    uow: UnitOfWork
):
    """Handle meal updates by updating corresponding menu meals."""
    # Load both aggregates independently
    meal = await uow.meals.get(evt.meal_id)
    menu = await uow.menus.get(evt.menu_id)
    
    # Find affected menu meals
    menu_meals = menu.get_meals_by_ids({meal.id})
    
    # Update menu representation of meal
    for menu_meal in menu_meals:
        updated_menu_meal = menu_meal.replace(
            meal_name=meal.name,
            nutri_facts=meal.nutri_facts,
        )
        menu.update_meal(updated_menu_meal)
    
    # Persist changes to menu aggregate
    await uow.menus.persist(menu)
    await uow.commit()

# Event handler for meal deletion
async def remove_meals_from_menu(evt: MealDeleted, uow: UnitOfWork):
    """Remove deleted meals from menu."""
    menu = await uow.menus.get(evt.menu_id)
    menu.remove_meals(frozenset({evt.meal_id}))
    await uow.menus.persist(menu)
    await uow.commit()
```

#### ✅ Direct Method Calls (Within Aggregate)

```python
# Direct calls within meal aggregate for immediate consistency
class Meal(Entity):
    def create_recipe(self, **kwargs):
        """Add recipe directly - immediate consistency required."""
        # Direct method call within aggregate boundary
        recipe = _Recipe.create_recipe(
            meal_id=self.id,
            author_id=self.author_id,
            **kwargs
        )
        self._recipes.append(recipe)  # Direct state modification
        
        # Cache invalidation (immediate)
        self._invalidate_caches('nutri_facts')
        
        # Version increment (immediate)
        self._increment_version()
        
        # Event for cross-aggregate coordination (eventual)
        self.add_event_to_updated_menu("Created new recipe in meal")

    def update_recipes(self, updates: dict):
        """Update multiple recipes directly."""
        for recipe_id, kwargs in updates.items():
            recipe = self.get_recipe_by_id(recipe_id)  # Direct lookup
            if recipe:
                recipe.update_properties(**kwargs)  # Direct call
                
        # Immediate cache invalidation
        self._invalidate_caches('nutri_facts')
        self._increment_version()
        
        # Eventual menu update
        self.add_event_to_updated_menu("Updated recipes in meal")
```

#### ✅ Application Service (Complex Coordination)

```python
# Application service for complex cross-aggregate operations
class MealManagementService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        
    async def copy_meal_to_menu(
        self, 
        source_meal_id: str, 
        target_menu_id: str,
        position: tuple[int, str, str]  # week, weekday, meal_type
    ):
        """Complex operation requiring coordination."""
        # Load source meal
        source_meal = await self.uow.meals.get(source_meal_id)
        target_menu = await self.uow.menus.get(target_menu_id)
        
        # Create new meal (direct aggregate method)
        copied_meal = Meal.copy_meal(
            meal=source_meal,
            id_of_user_coping_meal=target_menu.author_id,
            id_of_target_menu=target_menu_id
        )
        
        # Add to meals repository
        await self.uow.meals.add(copied_meal)
        await self.uow.meals.persist(copied_meal)
        
        # Create menu meal representation (direct aggregate method)
        menu_meal = MenuMeal(
            meal_id=copied_meal.id,
            week=position[0],
            weekday=position[1], 
            meal_type=position[2],
            meal_name=copied_meal.name,
            nutri_facts=copied_meal.nutri_facts
        )
        
        # Add to menu (direct aggregate method)
        target_menu.add_meal(menu_meal)
        await self.uow.menus.persist(target_menu)
        
        # Commit all changes together
        await self.uow.commit()
        
        return copied_meal.id
```

### Event vs Direct Call Decision Matrix

| Scenario | Pattern | Reason | Implementation |
|----------|---------|--------|----------------|
| **Recipe → Meal nutrition update** | Direct Call | Same aggregate, immediate consistency | `meal.create_recipe()` |
| **Meal name → Menu display update** | Domain Event | Cross-aggregate, eventual consistency | `UpdatedAttrOnMealThatReflectOnMenu` |
| **Menu meal positioning** | Direct Call | Within menu aggregate | `menu.add_meal()` |
| **Meal deletion → Menu cleanup** | Domain Event | Cross-aggregate coordination | `MealDeleted` event |
| **User rating → Recipe average** | Direct Call | Within recipe/meal aggregate | `recipe.rate()` |
| **Menu changes → Meal references** | Domain Event | Cross-aggregate, loose coupling | `MenuMealAddedOrRemoved` |
| **Complex meal copying** | Application Service | Multi-aggregate transaction | Direct calls + UoW |
| **Analytics/Audit logging** | Domain Event | Side effect, non-critical | Background event handlers |

### Event Handler Registration

```python
# Event handler registry maps events to handlers
EVENT_HANDLERS = {
    # Meal-related events
    UpdatedAttrOnMealThatReflectOnMenu: [update_menu_meals],
    MealDeleted: [remove_meals_from_menu],
    
    # Menu-related events
    MenuMealAddedOrRemoved: [update_menu_id_on_meals],
    MenuDeleted: [delete_related_meals],
    
    # Recipe-related events (future)
    RecipeCreated: [update_product_usage_stats],
    RecipeUpdated: [invalidate_nutrition_caches],
}

# Event dispatcher in application service
async def dispatch_events(entity: Entity, uow: UnitOfWork):
    """Dispatch all pending events from an entity."""
    for event in entity.events:
        event_type = type(event)
        if event_type in EVENT_HANDLERS:
            for handler in EVENT_HANDLERS[event_type]:
                try:
                    await handler(event, uow)
                except Exception as e:
                    logger.error(f"Event handler failed: {e}", exc_info=True)
                    # Continue with other handlers
    
    # Clear events after processing
    entity.events.clear()
```

### Error Handling Strategies

#### Event Handler Failures

```python
# Resilient event processing with retry and dead letter
async def process_events_with_retry(entity: Entity, uow: UnitOfWork):
    """Process events with retry logic and failure handling."""
    failed_events = []
    
    for event in entity.events:
        event_type = type(event)
        
        if event_type not in EVENT_HANDLERS:
            logger.warning(f"No handler for event: {event_type}")
            continue
            
        for handler in EVENT_HANDLERS[event_type]:
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    await handler(event, uow)
                    break  # Success, move to next handler
                except Exception as e:
                    retry_count += 1
                    logger.warning(
                        f"Event handler retry {retry_count}/{max_retries}: {e}",
                        extra={"event_type": event_type.__name__, "handler": handler.__name__}
                    )
                    
                    if retry_count >= max_retries:
                        # Send to dead letter queue
                        failed_events.append((event, handler, str(e)))
                        logger.error(
                            f"Event handler failed permanently: {e}",
                            exc_info=True,
                            extra={"event": event, "handler": handler.__name__}
                        )
    
    # Handle failed events (dead letter processing)
    if failed_events:
        await send_to_dead_letter_queue(failed_events)
    
    entity.events.clear()
```

### Performance Considerations

#### Event Processing Overhead

```python
# Batch event processing for performance
async def process_events_in_batch(entities: list[Entity], uow: UnitOfWork):
    """Process events from multiple entities efficiently."""
    # Group events by type for batch processing
    events_by_type = defaultdict(list)
    
    for entity in entities:
        for event in entity.events:
            events_by_type[type(event)].append(event)
    
    # Process each event type in batch
    for event_type, events in events_by_type.items():
        if event_type in EVENT_HANDLERS:
            for handler in EVENT_HANDLERS[event_type]:
                # Some handlers can process events in batch
                if hasattr(handler, 'process_batch'):
                    await handler.process_batch(events, uow)
                else:
                    # Process individually
                    for event in events:
                        await handler(event, uow)
    
    # Clear all events
    for entity in entities:
        entity.events.clear()
```

### Testing Event-Driven Logic

```python
class TestMealEventGeneration:
    """Test event generation patterns."""
    
    def test_meal_property_update_generates_menu_event(self):
        """Test that meal changes generate appropriate events."""
        # Given: Meal associated with menu
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="user-123",
            meal_id="meal-456", 
            menu_id="menu-789"
        )
        meal.events.clear()  # Clear creation events
        
        # When: Updating meal properties
        meal.update_properties(name="Updated Name")
        
        # Then: Should generate menu update event
        update_events = [e for e in meal.events 
                        if isinstance(e, UpdatedAttrOnMealThatReflectOnMenu)]
        assert len(update_events) == 1
        assert update_events[0].menu_id == "menu-789"
        assert update_events[0].meal_id == "meal-456"

class TestEventHandlers:
    """Test event handler behavior."""
    
    @pytest.mark.integration
    async def test_meal_update_event_handler(self, uow):
        """Test that meal update events properly update menus."""
        # Given: Meal and menu in database
        meal = await create_test_meal_in_db(uow)
        menu = await create_test_menu_with_meal(uow, meal.id)
        
        # When: Processing meal update event
        event = UpdatedAttrOnMealThatReflectOnMenu(
            menu_id=menu.id,
            meal_id=meal.id,
            message="Test update"
        )
        await update_menu_meals(event, uow)
        
        # Then: Menu should reflect updated meal data
        updated_menu = await uow.menus.get(menu.id)
        menu_meal = updated_menu.get_meals_by_ids({meal.id}).pop()
        assert menu_meal.meal_name == meal.name
```

### Quick Reference

| **Use Direct Calls When** | **Use Events When** | **Use Application Service When** |
|---------------------------|---------------------|----------------------------------|
| ✅ Same aggregate boundary | ✅ Cross-aggregate coordination | ✅ Complex multi-aggregate workflows |
| ✅ Immediate consistency required | ✅ Eventual consistency acceptable | ✅ Transaction coordination needed |
| ✅ Simple state changes | ✅ Loose coupling desired | ✅ Business process orchestration |
| ✅ Performance critical | ✅ Side effects (logging, notifications) | ✅ Error handling across aggregates |
| ✅ Validation must be synchronous | ✅ Fan-out to multiple handlers | ✅ Compensation logic required |

| **Pattern** | **Consistency** | **Performance** | **Complexity** | **Testability** |
|-------------|-----------------|-----------------|----------------|-----------------|
| **Direct Calls** | Strong | High | Low | Easy |
| **Domain Events** | Eventual | Medium | Medium | Medium |
| **Application Service** | Configurable | Medium | High | Complex |

--- 

## 6. Performance Optimization Priority

### Priority Matrix

```
🚀 PERFORMANCE ISSUE DETECTED?
    │
    ├─ What type of performance problem?
    │   
    ├─ 🐌 SLOW DATABASE QUERIES (>100ms)
    │   ├─ Query frequency?
    │   │   ├─ 🔥 HIGH FREQUENCY → Priority 1 (Critical) 🚨
    │   │   │   ├─ Add repository caching immediately
    │   │   │   ├─ Optimize SQL with QueryBuilder
    │   │   │   ├─ Add database indexes
    │   │   │   └─ Consider read replicas
    │   │   │
    │   │   ├─ 📊 MEDIUM FREQUENCY → Priority 2 (High) ⚡
    │   │   │   ├─ Optimize query filters
    │   │   │   ├─ Add targeted indexes
    │   │   │   ├─ Use starting_stmt optimization
    │   │   │   └─ Monitor with RepositoryLogger
    │   │   │
    │   │   └─ 📝 LOW FREQUENCY → Priority 3 (Medium) 📋
    │   │       ├─ Document query complexity
    │   │       ├─ Add performance tests
    │   │       └─ Consider future optimization
    │   
    ├─ 🧮 EXPENSIVE COMPUTATIONS (>10ms)
    │   ├─ Data recomputed frequently?
    │   │   ├─ 🔥 YES, SAME DATA → Priority 1 (Critical) 🚨
    │   │   │   ├─ Add @cached_property immediately
    │   │   │   ├─ Implement cache invalidation
    │   │   │   ├─ Benchmark performance gain
    │   │   │   └─ Monitor cache hit ratio
    │   │   │
    │   │   ├─ 🔄 YES, SIMILAR DATA → Priority 2 (High) ⚡
    │   │   │   ├─ Consider computation sharing
    │   │   │   ├─ Add lookup dictionaries
    │   │   │   ├─ Batch processing optimization
    │   │   │   └─ Cache intermediate results
    │   │   │
    │   │   └─ 🔀 NO, ALWAYS DIFFERENT → Priority 4 (Low) 📝
    │   │       ├─ Algorithm optimization
    │   │       ├─ Data structure improvements
    │   │       └─ Parallel processing consideration
    │   
    ├─ 🌐 NETWORK/API CALLS (>200ms)
    │   ├─ External dependency reliability?
    │   │   ├─ 🔥 CRITICAL DEPENDENCY → Priority 1 (Critical) 🚨
    │   │   │   ├─ Implement circuit breaker
    │   │   │   ├─ Add fallback mechanisms
    │   │   │   ├─ Cache responses aggressively
    │   │   │   └─ Consider async processing
    │   │   │
    │   │   ├─ 📊 IMPORTANT SERVICE → Priority 2 (High) ⚡
    │   │   │   ├─ Add response caching
    │   │   │   ├─ Implement retry logic
    │   │   │   ├─ Connection pooling
    │   │   │   └─ Timeout optimization
    │   │   │
    │   │   └─ 📝 OPTIONAL SERVICE → Priority 3 (Medium) 📋
    │   │       ├─ Background processing
    │   │       ├─ Best-effort caching
    │   │       └─ Graceful degradation
    │   
    └─ 💾 MEMORY USAGE (high allocation)
        ├─ Memory growth pattern?
        │   ├─ 🔥 GROWING UNBOUNDED → Priority 1 (Critical) 🚨
        │   │   ├─ Identify memory leaks
        │   │   ├─ Add cache size limits
        │   │   ├─ Implement LRU eviction
        │   │   └─ Monitor memory usage
        │   │
        │   ├─ 📊 HIGH BUT STABLE → Priority 3 (Medium) 📋
        │   │   ├─ Object pooling
        │   │   ├─ Lazy loading
        │   │   ├─ Data structure optimization
        │   │   └─ Garbage collection tuning
        │   │
        │   └─ 📝 WITHIN LIMITS → Priority 4 (Low) 📝
        │       └─ Monitor and document

🎯 OPTIMIZATION IMPACT SCORING:
    │
    ├─ BUSINESS IMPACT × TECHNICAL EFFORT = PRIORITY SCORE
    ├─ High Business Impact + Low Effort = Priority 1 (Do Now)
    ├─ High Business Impact + High Effort = Priority 2 (Plan & Execute) 
    ├─ Low Business Impact + Low Effort = Priority 3 (Quick Wins)
    └─ Low Business Impact + High Effort = Priority 4 (Don't Do)
```

### Performance Optimization Patterns

#### 🚨 Priority 1: Critical Performance Issues

```python
# Example: High-frequency nutrition aggregation
class Meal(Entity):
    @cached_property
    def nutri_facts(self) -> NutriFacts | None:
        """CRITICAL: Cached nutrition aggregation (95%+ cache hit ratio)."""
        if not self.recipes:
            return None
            
        # Expensive aggregation - cached after first computation
        total_calories = sum(r.nutri_facts.calories for r in self.recipes if r.nutri_facts)
        total_protein = sum(r.nutri_facts.protein for r in self.recipes if r.nutri_facts)
        total_carbs = sum(r.nutri_facts.carbohydrate for r in self.recipes if r.nutri_facts)
        total_fat = sum(r.nutri_facts.total_fat for r in self.recipes if r.nutri_facts)
        
        return NutriFacts(
            calories=total_calories,
            protein=total_protein,
            carbohydrate=total_carbs,
            total_fat=total_fat
        )
    
    def create_recipe(self, **kwargs):
        """Invalidate critical caches immediately when data changes."""
        recipe = _Recipe.create_recipe(**kwargs)
        self._recipes.append(recipe)
        # CRITICAL: Must invalidate to maintain consistency
        self._invalidate_caches('nutri_facts')
        self._increment_version()

# Repository-level caching for high-frequency queries
class MealRepo(CompositeRepository[Meal, MealSaModel]):
    async def query(self, filter=None, **kwargs):
        """CRITICAL: Add caching for high-frequency meal queries."""
        # Build cache key
        cache_key = self._build_cache_key(filter=filter, **kwargs)
        
        # Try cache first (avoid database hit)
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
            
        # Execute query
        result = await super().query(filter=filter, **kwargs)
        
        # Cache result with appropriate TTL
        ttl = 300 if filter.get('author_id') else 60  # User-specific vs global
        self._set_cache(cache_key, result, ttl=ttl)
        
        return result
```

#### ⚡ Priority 2: High Impact Optimizations

```python
# Lookup dictionary optimization for menu operations
class Menu(Entity):
    @cached_property
    def _meals_by_id_lookup(self) -> dict[str, MenuMeal]:
        """HIGH PRIORITY: O(1) meal lookup for menu operations."""
        return {meal.meal_id: meal for meal in self._meals}
    
    @cached_property
    def meals_dict(self) -> dict[tuple[int, str, str], MenuMeal]:
        """HIGH PRIORITY: Fast position-based meal lookup."""
        return {
            (meal.week, meal.weekday, meal.meal_type): meal 
            for meal in self._meals
        }
    
    def get_meals_by_ids(self, meal_ids: set[str]) -> set[MenuMeal]:
        """Optimized meal retrieval using lookup dictionary."""
        # O(1) lookup per meal instead of O(n) search
        return {self._meals_by_id_lookup[meal_id] 
                for meal_id in meal_ids 
                if meal_id in self._meals_by_id_lookup}
    
    def add_meal(self, meal: MenuMeal):
        """Invalidate lookup caches when collection changes."""
        self._meals.add(meal)
        # Invalidate lookup caches
        self._invalidate_caches('_meals_by_id_lookup', 'meals_dict')
        self.events.append(MenuMealAddedOrRemoved(...))

# Query optimization with QueryBuilder
async def get_popular_meals_optimized(
    session: AsyncSession, 
    author_id: str, 
    limit: int = 20
) -> list[MealSaModel]:
    """HIGH PRIORITY: Optimized popular meals query."""
    qb = QueryBuilder[Meal, MealSaModel](session, MealSaModel)
    
    results = await (qb
        .select(MealSaModel.id, MealSaModel.name, MealSaModel.calorie_density)  # Only needed fields
        .join(RecipeSaModel, MealSaModel.recipes)
        .join(RatingSaModel, RecipeSaModel.ratings)
        .where(EqualsOperator(), MealSaModel.author_id, author_id)
        .where(GreaterThanOperator(), RatingSaModel.taste, 4)  # High rated only
        .group_by(MealSaModel.id)
        .having(CountOperator(), RatingSaModel.id, min_count=5)  # Minimum rating count
        .order_by(MealSaModel.calorie_density, descending=False)
        .limit(limit)
        .execute(_return_sa_instance=True))
    
    return results
```

#### 📋 Priority 3: Medium Impact Optimizations

```python
# Rating average caching (less frequent access)
class _Recipe(Entity):
    @cached_property
    def average_taste_rating(self) -> float | None:
        """MEDIUM PRIORITY: Cache rating averages (accessed less frequently)."""
        if not self._ratings:
            return None
        return sum(r.taste for r in self._ratings) / len(self._ratings)
    
    def rate(self, user_id: str, taste: int, convenience: int):
        """Invalidate rating caches when new ratings added."""
        rating = Rating(user_id=user_id, recipe_id=self.id, taste=taste, convenience=convenience)
        self._ratings.append(rating)
        # MEDIUM PRIORITY: Invalidate rating caches
        self._invalidate_caches('average_taste_rating', 'average_convenience_rating')

# Batch processing optimization
async def update_multiple_meals_optimized(
    meal_updates: list[tuple[str, dict]], 
    uow: UnitOfWork
):
    """MEDIUM PRIORITY: Batch meal updates for better performance."""
    meals = []
    
    # Load all meals in batch
    meal_ids = [meal_id for meal_id, _ in meal_updates]
    filter_in_query = {"id": meal_ids}
    meals = await uow.meals.query(filter=filter_in_query)
    meals_by_id = {meal.id: meal for meal in meals}
    
    # Apply updates
    for meal_id, updates in meal_updates:
        if meal_id in meals_by_id:
            meal = meals_by_id[meal_id]
            meal.update_properties(**updates)
    
    # Persist all at once
    await uow.meals.persist_all(meals)
    await uow.commit()
```

#### 📝 Priority 4: Low Priority/Future Optimizations

```python
# Algorithm improvements (low impact)
class NutritionalAnalyzer:
    """LOW PRIORITY: Advanced nutrition analysis (used infrequently)."""
    
    def calculate_macro_distribution(self, nutri_facts: NutriFacts) -> MacroDivision:
        """Future optimization: More efficient macro calculation."""
        # Current implementation is acceptable for low-frequency use
        carb_calories = nutri_facts.carbohydrate * 4
        protein_calories = nutri_facts.protein * 4
        fat_calories = nutri_facts.total_fat * 9
        
        total_calories = carb_calories + protein_calories + fat_calories
        if total_calories == 0:
            return MacroDivision(carbohydrate=0, protein=0, fat=0)
            
        return MacroDivision(
            carbohydrate=(carb_calories / total_calories) * 100,
            protein=(protein_calories / total_calories) * 100,
            fat=(fat_calories / total_calories) * 100
        )

# Memory optimization (monitor but don't fix immediately)
class EntityCache:
    """LOW PRIORITY: Advanced entity caching (implement when needed)."""
    
    def __init__(self, max_size: int = 1000):
        self._cache: dict = {}
        self._access_order: list = []
        self._max_size = max_size
    
    def get(self, key: str):
        """LRU cache implementation for future use."""
        if key in self._cache:
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None
    
    def set(self, key: str, value):
        """Add with LRU eviction."""
        if len(self._cache) >= self._max_size:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]
            
        self._cache[key] = value
        self._access_order.append(key)
```

### Performance Monitoring & Benchmarking

#### Benchmark Timer Usage

```python
class PerformanceTests:
    """Performance testing patterns for optimization validation."""
    
    def test_nutrition_aggregation_performance(self, meal_with_recipes):
        """Validate caching performance improvements."""
        # Baseline: First access (cache miss)
        with benchmark_timer() as timer_cold:
            result_cold = meal_with_recipes.nutri_facts
            
        # Optimized: Second access (cache hit)  
        with benchmark_timer() as timer_warm:
            result_warm = meal_with_recipes.nutri_facts
            
        # Performance assertions
        timer_warm.assert_faster_than(0.001)  # < 1ms for cached access
        
        # Cache effectiveness
        speedup = timer_cold.elapsed / timer_warm.elapsed
        assert speedup > 10  # At least 10x faster when cached
        assert result_cold is result_warm  # Same object (cached)
    
    @timeout_test(30.0)
    async def test_repository_query_performance(self, meal_repository, large_dataset):
        """Validate repository optimization effectiveness."""
        # Performance-critical query
        with benchmark_timer() as timer:
            results = await meal_repository.query(
                filter={"author_id": "test-user", "total_time_lte": 60},
                limit=50
            )
            
        # Performance targets
        timer.assert_faster_than(2.0)  # < 2 seconds
        assert len(results) <= 50
        
    def test_lookup_dictionary_performance(self, menu_with_many_meals):
        """Validate O(1) lookup performance."""
        meal_ids = {meal.meal_id for meal in list(menu_with_many_meals.meals)[:10]}
        
        # Optimized lookup using dictionary
        with benchmark_timer() as timer:
            found_meals = menu_with_many_meals.get_meals_by_ids(meal_ids)
            
        # Should be very fast regardless of total meal count
        timer.assert_faster_than(0.001)  # < 1ms for 10 lookups
        assert len(found_meals) == len(meal_ids)
```

#### Repository Performance Monitoring

```python
# Repository logger configuration for performance tracking
class MealRepo(CompositeRepository[Meal, MealSaModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self._repo_logger = RepositoryLogger.create_logger("MealRepo")
        self._repo_logger.enable_performance_tracking = True
        
    async def query(self, **kwargs):
        """Query with performance monitoring."""
        async with self._repo_logger.track_query(
            "meal_query",
            filter_count=len(kwargs.get('filter', {})),
            has_limit=kwargs.get('limit') is not None
        ) as context:
            
            result = await super().query(**kwargs)
            context["result_count"] = len(result)
            
            # Performance warning for slow queries
            if context.get("execution_time", 0) > 1.0:
                self._repo_logger.warn_performance_issue(
                    "slow_meal_query",
                    f"Meal query took {context['execution_time']:.2f}s",
                    **context
                )
                
            return result
```

### Performance Optimization Decision Matrix

| **Issue Type** | **Frequency** | **Business Impact** | **Priority** | **Action** |
|----------------|---------------|-------------------|-------------|------------|
| Slow DB Query | High | High | 🚨 P1 | Add caching immediately |
| Expensive Computation | High | High | 🚨 P1 | Add @cached_property |
| Network Timeout | Medium | High | ⚡ P2 | Add circuit breaker |
| Memory Leak | Low | High | ⚡ P2 | Fix immediately |
| Slow Algorithm | High | Medium | ⚡ P2 | Optimize algorithm |
| Cache Miss | Medium | Medium | 📋 P3 | Improve cache strategy |
| Inefficient Loop | Low | Medium | 📋 P3 | Refactor when convenient |
| Suboptimal Data Structure | Low | Low | 📝 P4 | Document for future |

### Performance Targets by Component

| **Component** | **Target** | **Critical Threshold** | **Optimization Strategy** |
|---------------|------------|----------------------|--------------------------|
| **@cached_property** | <1ms (cached) | >10ms (cached) | Cache invalidation review |
| **Repository.get()** | <50ms | >200ms | Add database indexes |
| **Repository.query()** | <100ms | >500ms | Query optimization |
| **API Endpoints** | <200ms | >1000ms | Caching + optimization |
| **Event Handlers** | <50ms | >200ms | Async processing |
| **Cache Hit Ratio** | >95% | <80% | Cache strategy review |

### Quick Reference

| **When to Optimize** | **Priority Level** | **Immediate Actions** |
|---------------------|-------------------|---------------------|
| ✅ High frequency + High impact | 🚨 P1 Critical | Add caching, optimize queries |
| ✅ Medium frequency + High impact | ⚡ P2 High | Plan optimization sprint |
| ✅ High frequency + Medium impact | ⚡ P2 High | Quick performance wins |
| ✅ Low frequency + High impact | 📋 P3 Medium | Monitor and document |
| ✅ Any frequency + Low impact | 📝 P4 Low | Future consideration |

| **Don't Optimize When** | **Instead Do** | **Rationale** |
|-------------------------|----------------|---------------|
| ❌ Premature optimization | ✅ Add monitoring | Measure first, optimize second |
| ❌ Low business impact | ✅ Document and track | Resource allocation priority |
| ❌ One-time operations | ✅ Accept current performance | Optimization overhead not worth it |
| ❌ Already within targets | ✅ Monitor for degradation | Don't over-engineer |

---

## Summary

These decision trees provide a comprehensive framework for making consistent architectural choices in the menu planning backend. Each tree is based on real codebase patterns and includes:

- **Clear decision logic** with binary choices
- **Practical code examples** from the actual system
- **Performance implications** and trade-offs
- **Quick reference tables** for fast decisions
- **Common pitfalls** to avoid

By following these decision trees, AI agents can quickly navigate complex architectural decisions while maintaining consistency with established patterns and achieving optimal performance characteristics.

For additional guidance, see:
- [`docs/architecture/quick-start-guide.md`](quick-start-guide.md) - Getting started with the codebase
- [`docs/architecture/technical-specifications.md`](technical-specifications.md) - Detailed technical patterns
- [`docs/architecture/ai-agent-workflows.md`](ai-agent-workflows.md) - Step-by-step development workflows