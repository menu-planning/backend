[← Index](./README.md) | [Quick Start](./quick-start-guide.md) | [Workflows](./ai-agent-workflows.md) | [Patterns](./pattern-library.md) | [Troubleshooting](./troubleshooting-guide.md)

---

# AI Agent Workflow Guide

## 🤖 AI Agent Development Workflows

This guide provides step-by-step workflows for AI agents working with the menu planning backend. Each workflow includes decision points, validation steps, and practical examples from the actual codebase.

---

## 🔍 Workflow 1: Analyzing a New Feature Request

### Overview
When you receive a feature request, follow this systematic approach to understand the domain impact and implementation scope.

### Step-by-Step Process

#### Phase 1: Requirements Analysis (5-10 minutes)

**1.1 Extract Core Requirements**
```bash
# Read the feature request and identify:
# - What business capability is needed?
# - Which domain context is involved?
# - What are the success criteria?

# Example: "Add ability to rate recipes within meals"
# → Business capability: Recipe rating
# → Domain context: recipes_catalog
# → Success criteria: Store and retrieve recipe ratings
```

**1.2 Identify Domain Boundaries**
```python
# Map the request to domain contexts:
# - recipes_catalog: Meals, recipes, ingredients
# - products_catalog: Food products, nutrition data
# - shared_kernel: Common value objects
# - iam: User management

# For recipe rating example:
# Primary context: recipes_catalog (recipe rating)
# Shared kernel: Rating value object (if doesn't exist)
# IAM context: User authentication for rating
```

**1.3 Determine Aggregate Impact**
```bash
# Check which aggregates are involved:
find src/contexts -name "*root_aggregate*" -type f | head -10

# For recipe rating:
# - Meal aggregate (contains recipes)
# - Recipe entity (within meal)
# - Need to add rating capability to Recipe
```

#### Phase 2: Domain Investigation (10-15 minutes)

**2.1 Study Existing Patterns**
```bash
# Look for similar functionality in the codebase
grep -r "rating\|rate" src/contexts/ --include="*.py"
grep -r "review\|comment" src/contexts/ --include="*.py"

# Study existing value objects
ls src/contexts/shared_kernel/domain/value_objects/
```

**2.2 Examine Test Patterns**
```bash
# Find test examples for similar features
find tests/contexts/recipes_catalog -name "*test_*" -type f | grep -E "(recipe|meal)"

# Study domain rule tests
cat tests/contexts/recipes_catalog/core/domain/meal/entities/test_recipe_domain_rules.py
```

**2.3 Check Command/Query Patterns**
```bash
# Review existing commands
ls src/contexts/recipes_catalog/core/domain/meal/commands/

# Check command handlers
cat src/contexts/recipes_catalog/core/services/command_handlers.py
```

#### Phase 3: Impact Assessment (5 minutes)

**3.1 Data Model Changes**
```python
# Identify new/modified entities:
# - Recipe entity: Add rating field
# - New Rating value object (if needed)
# - Database schema changes

# Example assessment:
# NEW: Rating value object with score (1-5) and optional comment
# MODIFIED: Recipe entity to include ratings collection
# SCHEMA: Add recipe_ratings table or rating fields
```

**3.2 API Changes**
```python
# Identify new commands/queries needed:
# - RateRecipe command
# - GetRecipeRatings query
# - UpdateRecipeRating command (if editing allowed)

# Example API impact:
# POST /meals/{meal_id}/recipes/{recipe_id}/ratings
# GET /meals/{meal_id}/recipes/{recipe_id}/ratings
# PUT /ratings/{rating_id}
```

**3.3 Performance Considerations**
```python
# Consider caching needs:
# - Recipe average rating (cached property)
# - Rating counts (cached property)
# - Impact on meal nutrition calculations (none for rating)
```

### Decision Points

| Question | If Yes → | If No → |
|----------|----------|---------|
| Does this cross multiple contexts? | Plan integration strategy | Proceed with single context |
| Does this need new value objects? | Design value objects first | Use existing patterns |
| Does this affect cached properties? | Plan cache invalidation | Proceed with normal flow |
| Does this need new aggregates? | Consider aggregate design | Modify existing aggregates |

### Example Output Template

```markdown
## Feature Analysis: Recipe Rating

**Domain Context**: recipes_catalog
**Primary Aggregate**: Meal (contains Recipe entities)
**Impact Level**: Medium (new functionality, no breaking changes)

**Required Changes**:
- NEW: Rating value object (score: float, comment: str?, author_id: str, created_at: datetime)
- MODIFIED: Recipe entity to include ratings: list[Rating]
- NEW: RateRecipe command
- NEW: GetRecipeRatings query
- CACHED: Recipe.average_rating property
- SCHEMA: Add rating fields to recipe table or separate ratings table

**Implementation Order**:
1. Create Rating value object
2. Add TDD tests for Recipe rating behavior
3. Modify Recipe entity to support ratings
4. Create RateRecipe command and handler
5. Add caching for average ratings
6. Create API endpoints
7. Update documentation

**Risk Assessment**: Low
- No breaking changes to existing API
- Isolated to Recipe entity
- Standard CRUD operations
```

---

## 🕵️ Workflow 2: Domain Investigation Process

### Overview
Deep-dive investigation of domain logic before implementing changes.

### Step-by-Step Process

#### Phase 1: Domain Model Exploration (10 minutes)

**1.1 Start with Aggregate Roots**
```bash
# Identify the primary aggregate
ls src/contexts/*/core/domain/*/root_aggregate/

# For meal/recipe features:
cat src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py | head -50
```

**1.2 Map Entity Relationships**
```python
# Using Python shell to explore domain model
# poetry run python manage.py shell

from contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe

# Create sample instances to understand relationships
meal = Meal.create_meal(
    name="Investigation Meal",
    author_id="test-user",
    meal_id="test-meal-id",
    menu_id="test-menu-id"
)

# Explore available methods and properties
print("Meal properties:", [prop for prop in dir(meal) if not prop.startswith('_')])
print("Meal recipes:", meal.recipes)
print("Meal version:", meal.version)
```

**1.3 Study Value Objects**
```bash
# Examine value objects used by the domain
ls src/contexts/shared_kernel/domain/value_objects/
ls src/contexts/recipes_catalog/core/domain/meal/value_objects/

# Study key value objects
cat src/contexts/shared_kernel/domain/value_objects/nutri_facts.py
cat src/contexts/recipes_catalog/core/domain/meal/value_objects/ingredient.py
```

#### Phase 2: Business Rules Discovery (15 minutes)

**2.1 Find Domain Rules**
```bash
# Look for domain rule implementations
find src -name "*rule*" -type f
find src -name "*validation*" -type f

# Study business rule tests
cat tests/contexts/recipes_catalog/core/domain/meal/root_aggregate/test_meal_domain_rules.py
```

**2.2 Understand Invariants**
```python
# Key domain invariants to understand:
# - Recipe must belong to correct meal (meal_id match)
# - Recipe author must match meal author
# - Ingredient positions must be consecutive
# - Nutrition facts must be valid
# - Caching rules for performance

# Example: Understanding recipe-meal relationship rules
grep -A 10 -B 5 "meal_id.*author_id" tests/contexts/recipes_catalog/core/domain/
```

**2.3 Cache Behavior Analysis**
```bash
# Study caching patterns - critical for performance
cat tests/contexts/seedwork/shared/domain/test_entity_cache_invalidation.py

# Find cached properties
grep -r "@cached_property" src/contexts/
grep -r "_invalidate_cache" src/contexts/
```

#### Phase 3: Integration Points (10 minutes)

**3.1 Command Handlers**
```bash
# Study how commands are handled
cat src/contexts/recipes_catalog/core/services/command_handlers.py | head -50

# Look for handler patterns
grep -A 5 -B 5 "async def handle" src/contexts/*/core/services/
```

**3.2 Repository Patterns**
```bash
# Understand data access patterns
find src -name "*repository*" -type f
cat src/contexts/recipes_catalog/core/adapters/repositories/meal_repository.py | head -30
```

**3.3 Event Handling**
```bash
# Check for domain events
find src -name "*event*" -type f
grep -r "Event" src/contexts/*/core/domain/
```

### Investigation Checklist

- [ ] **Primary Aggregate Identified**: Which aggregate owns this functionality?
- [ ] **Entity Relationships Mapped**: How do entities relate within the aggregate?
- [ ] **Value Objects Located**: What value objects are involved?
- [ ] **Business Rules Understood**: What invariants must be maintained?
- [ ] **Cache Dependencies Identified**: What cached properties are affected?
- [ ] **Command/Query Patterns Found**: How is similar functionality implemented?
- [ ] **Integration Points Mapped**: What services/repositories are involved?
- [ ] **Test Patterns Understood**: How is similar functionality tested?

### Example Investigation Output

```markdown
## Domain Investigation: Recipe Rating Feature

**Aggregate Analysis**:
- Primary: Meal aggregate (recipes_catalog context)
- Recipes are entities within Meal aggregate
- Recipe mutations go through Meal aggregate root

**Entity Relationships**:
- Meal 1:N Recipe (composition)
- Recipe contains ingredients, nutrition facts
- Recipe has author_id that must match Meal author_id

**Business Rules Discovered**:
- Recipe.meal_id must match parent Meal.id
- Recipe.author_id must match Meal.author_id  
- Recipe positions handled automatically
- No duplicate recipe names within meal (soft rule)

**Cache Dependencies**:
- Meal.nutri_facts aggregates from all recipes
- Meal.total_time calculated from recipe times
- Adding rating won't affect existing cached properties
- New cached property: Recipe.average_rating will be needed

**Implementation Pattern**:
- Use protected _Recipe.create_recipe() method
- Mutations through Meal.update_recipes() method
- Follow existing command/handler pattern
- Repository access through meal_repository

**Test Strategy**:
- Domain rule tests in test_recipe_domain_rules.py
- Entity behavior tests in test_recipe.py
- Integration tests through command handlers
- Cache invalidation tests for new cached properties
```

---

## 🧪 Workflow 3: TDD Implementation Process

### Overview
Test-Driven Development workflow specifically tailored for domain-driven architecture.

### Step-by-Step Process

#### Phase 1: Test Strategy Planning (5 minutes)

**1.1 Identify Test Categories**
```python
# Plan test coverage:
# 1. Domain Rule Tests - Business logic validation
# 2. Entity Behavior Tests - Entity state management
# 3. Command Handler Tests - Application service layer
# 4. Integration Tests - Repository and persistence
# 5. Cache Behavior Tests - Performance features
```

**1.2 Locate Test Files**
```bash
# Find existing test patterns to follow
find tests/contexts/recipes_catalog/core/domain/meal -name "test_*.py"

# Key test files for reference:
# - test_meal_domain_rules.py: Business rule validation
# - test_recipe_domain_rules.py: Recipe-specific rules
# - test_meal.py: Entity behavior characterization
# - test_recipe.py: Recipe entity behavior
```

#### Phase 2: Domain Rule Tests First (15-20 minutes)

**2.1 Create Domain Rule Tests**
```python
# Example: TDD for recipe rating feature
# File: tests/contexts/recipes_catalog/core/domain/meal/entities/test_recipe_rating_rules.py

import pytest
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.recipes_catalog.core.domain.meal.value_objects.rating import Rating  # NEW
from src.contexts.shared_kernel.domain.exceptions import BusinessRuleValidationException

class TestRecipeRatingBusinessRules:
    """Test domain business rules for recipe rating."""
    
    def test_recipe_accepts_valid_rating_from_meal_author(self):
        """Domain should accept ratings from meal author."""
        # Arrange: Create meal and recipe
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123", 
            menu_id="menu_123"
        )
        
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Test",
            author_id="author_123",
            meal_id="meal_123",
            nutri_facts=NutriFacts(calories=100)
        )
        
        # Create valid rating
        rating = Rating(
            score=4.5,
            comment="Great recipe!",
            author_id="author_123",  # Same as meal author
            created_at=datetime.now()
        )
        
        # Act: Add rating to recipe
        recipe.add_rating(rating)
        
        # Assert: Domain should accept valid rating
        assert len(recipe.ratings) == 1
        assert recipe.ratings[0].score == 4.5
        
    def test_recipe_rejects_rating_with_invalid_score(self):
        """Domain should reject ratings with invalid scores."""
        # Test implementation following domain rule pattern...
        # This test will FAIL initially - that's TDD!
```

**2.2 Run Failing Tests**
```bash
# Run the new test - it should fail (TDD red phase)
poetry run python -m pytest tests/contexts/recipes_catalog/core/domain/meal/entities/test_recipe_rating_rules.py -v

# Expected: ImportError for Rating value object, AttributeError for add_rating method
```

#### Phase 3: Implement Minimum Code (10-15 minutes)

**3.1 Create Value Objects**
```python
# File: src/contexts/recipes_catalog/core/domain/meal/value_objects/rating.py
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Rating:
    """Recipe rating value object."""
    score: float           # 1.0-5.0
    author_id: str        # Who gave the rating
    created_at: datetime  # When rating was given
    comment: str | None = None  # Optional comment
    
    def __post_init__(self):
        """Validate rating constraints."""
        if not (1.0 <= self.score <= 5.0):
            raise ValueError("Rating score must be between 1.0 and 5.0")
        if not self.author_id:
            raise ValueError("Rating must have an author_id")
```

**3.2 Add Entity Methods**
```python
# Add to Recipe entity (_Recipe class)
# File: src/contexts/recipes_catalog/core/domain/meal/entities/recipe.py

def add_rating(self, rating: Rating) -> None:
    """Add a rating to this recipe."""
    # Business rule: Rating author must match meal author
    if rating.author_id != self.author_id:
        raise BusinessRuleValidationException(
            "Rating author must match recipe author"
        )
    
    # Add to ratings collection
    if not hasattr(self, '_ratings'):
        self._ratings = []
    self._ratings.append(rating)
    
    # Invalidate cached properties
    self._invalidate_cache()

@property 
def ratings(self) -> list[Rating]:
    """Get all ratings for this recipe."""
    return getattr(self, '_ratings', [])
```

**3.3 Run Tests - Green Phase**
```bash
# Run tests again - they should pass now
poetry run python -m pytest tests/contexts/recipes_catalog/core/domain/meal/entities/test_recipe_rating_rules.py -v

# Expected: All tests pass (TDD green phase)
```

#### Phase 4: Entity Behavior Tests (10 minutes)

**4.1 Add Characterization Tests**
```python
# File: tests/contexts/recipes_catalog/core/domain/meal/entities/test_recipe_rating_behavior.py

class TestRecipeRatingBehavior:
    """Test recipe rating entity behaviors."""
    
    def test_recipe_calculates_average_rating(self):
        """Recipe should calculate average rating from all ratings."""
        # Arrange: Create recipe with multiple ratings
        recipe = self._create_test_recipe()
        
        ratings = [
            Rating(score=4.0, author_id="user1", created_at=datetime.now()),
            Rating(score=5.0, author_id="user2", created_at=datetime.now()),
            Rating(score=3.0, author_id="user3", created_at=datetime.now())
        ]
        
        for rating in ratings:
            recipe.add_rating(rating)
            
        # Act: Get average rating
        avg_rating = recipe.average_rating
        
        # Assert: Should calculate correct average
        assert avg_rating == 4.0  # (4 + 5 + 3) / 3
```

**4.2 Add Cached Property**
```python
# Add to Recipe entity
from src.contexts.seedwork.shared.domain.entity import cached_property

@cached_property
def average_rating(self) -> float | None:
    """Calculate average rating for this recipe."""
    if not self.ratings:
        return None
    return sum(rating.score for rating in self.ratings) / len(self.ratings)
```

#### Phase 5: Command Handler Tests (10 minutes)

**5.1 Create Command and Handler Tests**
```python
# File: tests/contexts/recipes_catalog/core/services/test_rate_recipe_command.py

class TestRateRecipeCommand:
    """Test RateRecipe command handling."""
    
    async def test_rate_recipe_command_success(self):
        """RateRecipe command should add rating to recipe."""
        # Arrange: Create command
        command = RateRecipe(
            meal_id="meal_123",
            recipe_id="recipe_456", 
            score=4.5,
            comment="Great recipe!",
            author_id="user_789"
        )
        
        # Mock repository (follow existing patterns)
        mock_repo = Mock()
        meal = self._create_test_meal_with_recipe()
        mock_repo.get.return_value = meal
        
        handler = MealCommandHandler(meal_repository=mock_repo)
        
        # Act: Handle command
        await handler.rate_recipe(command)
        
        # Assert: Recipe should have new rating
        recipe = meal.get_recipe_by_id("recipe_456")
        assert len(recipe.ratings) == 1
        assert recipe.ratings[0].score == 4.5
```

#### Phase 6: Refactor and Polish (5 minutes)

**6.1 Clean Up Code**
```bash
# Run full test suite to ensure no regressions
poetry run python -m pytest tests/contexts/recipes_catalog/ -v

# Run linting and formatting
poetry run python -m ruff check .
poetry run python -m black . --check
poetry run python -m mypy src/
```

**6.2 Add Integration Tests**
```python
# Add end-to-end tests if needed
# File: tests/contexts/recipes_catalog/e2e/test_recipe_rating_integration.py
```

### TDD Checklist

- [ ] **Domain Rule Tests Written**: Business rules tested first
- [ ] **Tests Initially Fail**: Red phase achieved
- [ ] **Minimum Implementation**: Just enough code to pass tests
- [ ] **Tests Pass**: Green phase achieved  
- [ ] **Entity Behavior Tests**: State management tested
- [ ] **Cached Properties Tested**: Performance features validated
- [ ] **Command Handler Tests**: Application layer tested
- [ ] **Code Refactored**: Clean, maintainable implementation
- [ ] **Integration Tests Added**: End-to-end scenarios covered
- [ ] **No Regressions**: Full test suite passes

### Common TDD Patterns in This Codebase

```python
# 1. Domain Rule Testing Pattern
def test_domain_accepts_valid_input(self):
    """Domain should accept valid business scenario."""
    # Arrange: Set up valid domain state
    # Act: Perform domain operation
    # Assert: Verify expected outcome

def test_domain_rejects_invalid_input(self):
    """Domain should reject invalid business scenario."""
    # Arrange: Set up invalid scenario
    # Act & Assert: Expect BusinessRuleValidationException

# 2. Entity Behavior Testing Pattern  
def test_entity_property_calculation(self):
    """Entity should calculate derived properties correctly."""
    # Focus on state changes and computed properties

# 3. Cache Testing Pattern
def test_cached_property_invalidation(self):
    """Cached property should invalidate when dependencies change."""
    # Test cache behavior specifically

# 4. Command Handler Testing Pattern
async def test_command_handler_success_scenario(self):
    """Command handler should process valid commands successfully."""
    # Test application service layer behavior
```

---

## ⚡ Workflow 4: Performance Impact Analysis

### Overview
Systematic approach to analyzing and optimizing performance impact of changes.

### Step-by-Step Checklist

#### Phase 1: Impact Assessment (5 minutes)

**1.1 Cache Dependency Analysis**
```bash
# Identify affected cached properties
grep -r "@cached_property" src/contexts/ | grep -E "(recipe|meal|nutrition)"

# Check cache invalidation patterns
grep -r "_invalidate_cache" src/contexts/recipes_catalog/
```

**1.2 Database Impact Assessment**
```python
# Questions to answer:
# - Does this add new database queries?
# - Does this change existing query patterns?
# - Are there N+1 query risks?
# - Does this affect joins or aggregations?

# Example for recipe rating:
# NEW QUERIES: 
# - Insert rating: 1 query
# - Get recipe ratings: 1 query per recipe
# - Calculate average rating: Aggregation query
# RISK: N+1 when loading meal with recipe ratings
```

**1.3 Memory Impact Assessment**
```python
# Consider memory usage:
# - New objects per request
# - Collection sizes (ratings per recipe)
# - Cache memory usage
# - Domain event memory

# Example assessment:
# Rating object: ~100 bytes per rating
# Recipe with 10 ratings: ~1KB additional
# Meal with 5 recipes: ~5KB additional  
# Impact: Minimal for typical usage
```

#### Phase 2: Performance Testing (15 minutes)

**2.1 Create Performance Benchmarks**
```python
# File: tests/performance/test_recipe_rating_performance.py

import pytest
from datetime import datetime
from src.contexts.seedwork.shared.infrastructure.benchmark_timer import BenchmarkTimer

class TestRecipeRatingPerformance:
    """Performance tests for recipe rating feature."""
    
    @pytest.mark.benchmark
    def test_add_rating_performance(self):
        """Benchmark adding ratings to recipes."""
        # Arrange: Create meal with recipe
        meal = self._create_test_meal_with_recipe()
        recipe = meal.recipes[0]
        
        # Act & Measure: Add 100 ratings
        with BenchmarkTimer("add_rating") as timer:
            for i in range(100):
                rating = Rating(
                    score=4.0,
                    author_id=f"user_{i}",
                    created_at=datetime.now()
                )
                recipe.add_rating(rating)
        
        # Assert: Performance expectations
        assert timer.duration < 0.1  # Should complete in < 100ms
        assert len(recipe.ratings) == 100
        
    @pytest.mark.benchmark
    def test_average_rating_calculation_performance(self):
        """Benchmark average rating calculation with caching."""
        # Arrange: Recipe with many ratings
        recipe = self._create_recipe_with_ratings(count=1000)
        
        # Act & Measure: Multiple average calculations
        with BenchmarkTimer("average_rating") as timer:
            for _ in range(100):
                avg = recipe.average_rating  # Should use cache after first call
                
        # Assert: Caching should make this fast
        assert timer.duration < 0.01  # Should be very fast with caching
        assert avg is not None
```

**2.2 Run Performance Tests**
```bash
# Run performance benchmarks
poetry run python -m pytest tests/performance/ --benchmark-only -v

# Analyze results
# Look for:
# - Slow operations (>100ms)
# - Memory leaks
# - Cache efficiency
```

**2.3 Database Query Analysis**
```python
# File: tests/performance/test_recipe_rating_database_performance.py

class TestRecipeRatingDatabasePerformance:
    """Test database performance for recipe rating operations."""
    
    async def test_meal_with_recipe_ratings_query_count(self):
        """Verify no N+1 queries when loading meal with recipe ratings."""
        # Arrange: Create meal with multiple recipes and ratings
        await self._create_meal_with_rated_recipes(recipe_count=5, ratings_per_recipe=3)
        
        # Act: Load meal with all recipe ratings
        with QueryCountAssert(max_queries=2) as query_counter:  # Meal + ratings join
            meal = await meal_repository.get_with_recipe_ratings("meal_123")
            
        # Assert: Efficient query pattern
        assert len(meal.recipes) == 5
        assert all(len(recipe.ratings) == 3 for recipe in meal.recipes)
        assert query_counter.count <= 2  # Should use joins, not N+1 queries
```

#### Phase 3: Optimization Implementation (10 minutes)

**3.1 Cache Optimization**
```python
# Optimize expensive calculations with caching
@cached_property
def average_rating(self) -> float | None:
    """Calculate average rating (cached for performance)."""
    if not self.ratings:
        return None
    return sum(rating.score for rating in self.ratings) / len(self.ratings)

@cached_property  
def rating_count(self) -> int:
    """Get count of ratings (cached for performance)."""
    return len(self.ratings)

# Cache invalidation on rating changes
def add_rating(self, rating: Rating) -> None:
    """Add rating and invalidate cache."""
    self._ratings.append(rating)
    self._invalidate_cache()  # Invalidates average_rating and rating_count
```

**3.2 Database Query Optimization**
```python
# Repository method with efficient queries
async def get_meal_with_recipe_ratings(self, meal_id: str) -> Meal:
    """Get meal with all recipe ratings in single query."""
    # Use JOIN to avoid N+1 queries
    query = """
    SELECT m.*, r.*, rt.*  
    FROM meals m
    LEFT JOIN recipes r ON r.meal_id = m.id
    LEFT JOIN recipe_ratings rt ON rt.recipe_id = r.id
    WHERE m.id = %s
    """
    # Implementation with proper object mapping...
```

**3.3 Memory Optimization**
```python
# Lazy loading for large collections
@property
def ratings(self) -> list[Rating]:
    """Get ratings with lazy loading."""
    if not hasattr(self, '_ratings_loaded'):
        self._load_ratings()
        self._ratings_loaded = True
    return self._ratings

def _load_ratings(self) -> None:
    """Load ratings on demand."""
    # Load from repository only when needed
    pass
```

### Performance Analysis Template

```markdown
## Performance Impact Analysis: Recipe Rating Feature

**Cache Impact**:
- NEW: Recipe.average_rating cached property
- NEW: Recipe.rating_count cached property  
- INVALIDATION: Cache invalidated on add_rating()
- MEMORY: ~50 bytes per cached value
- EFFICIENCY: 100x faster on repeated access

**Database Impact**:
- NEW QUERIES: 
  - INSERT rating: 1 query per rating
  - SELECT ratings for recipe: 1 query per recipe
  - SELECT average rating: 1 aggregation query
- OPTIMIZATION: JOIN query to load meal + recipe ratings
- N+1 RISK: Mitigated with JOIN queries
- INDEX NEEDED: recipe_id, created_at for rating queries

**Memory Impact**:
- Rating object: ~100 bytes
- 10 ratings per recipe: ~1KB  
- 100 recipes with ratings: ~100KB
- ASSESSMENT: Minimal impact for expected usage

**Performance Benchmarks**:
- Add single rating: <1ms
- Calculate average (cached): <0.1ms  
- Calculate average (uncached): <10ms for 1000 ratings
- Load meal with rated recipes: <50ms for 10 recipes

**Optimization Recommendations**:
1. Use cached properties for expensive calculations
2. Implement JOIN queries to avoid N+1
3. Add database indexes on rating queries
4. Consider lazy loading for large rating collections
5. Monitor cache hit rates in production

**Risk Assessment**: Low
- Performance impact minimal for expected usage
- Caching provides good performance characteristics
- Database queries optimized with JOINs
- Memory usage reasonable
```

---

## 📋 Workflow 5: Code Review Preparation

### Overview
Comprehensive checklist to prepare code for review, ensuring quality and maintainability.

### Step-by-Step Checklist

#### Phase 1: Code Quality Validation (10 minutes)

**1.1 Run All Quality Checks**
```bash
# Type checking
poetry run python -m mypy src/

# Linting
poetry run python -m ruff check .

# Formatting  
poetry run python -m black . --check

# Security scanning
poetry run python -m bandit -r src/

# Import sorting
poetry run python -m isort . --check
```

**1.2 Test Coverage Validation**
```bash
# Run full test suite with coverage
poetry run python -m pytest --cov=src --cov-report=term-missing --cov-report=html

# Check coverage thresholds
# - Unit tests: >95% coverage
# - Integration tests: >80% coverage  
# - E2E tests: Key scenarios covered

# Review coverage report
open htmlcov/index.html  # Check uncovered lines
```

**1.3 Performance Validation**
```bash
# Run performance tests
poetry run python -m pytest tests/performance/ --benchmark-only

# Check for performance regressions
# Compare benchmark results with baseline
```

#### Phase 2: Documentation Review (5 minutes)

**2.1 Code Documentation**
```python
# Verify docstrings for public methods
# Example good docstring:
def add_rating(self, rating: Rating) -> None:
    """Add a rating to this recipe.
    
    Args:
        rating: The rating to add. Must have matching author_id.
        
    Raises:
        BusinessRuleValidationException: If rating author doesn't match recipe author.
        
    Example:
        >>> recipe.add_rating(Rating(score=4.5, author_id="user123"))
    """
    
# Check type hints are complete
def calculate_average_rating(ratings: list[Rating]) -> float | None:
    """Calculate average rating from list of ratings."""
```

**2.2 API Documentation**
```bash
# Update technical specifications if needed
# Add new commands/queries to docs/architecture/technical-specifications.md

# Update workflow documentation if new patterns introduced
```

#### Phase 3: Domain Rule Validation (10 minutes)

**3.1 Business Rule Compliance**
```python
# Verify all business rules are enforced:
# ✓ Recipe author matches meal author
# ✓ Rating scores are in valid range (1.0-5.0)
# ✓ Rating author is authenticated user
# ✓ Cache invalidation on state changes
# ✓ Aggregate boundaries respected

# Check rule tests exist:
grep -r "BusinessRuleValidationException" tests/contexts/recipes_catalog/
```

**3.2 Domain Model Integrity**
```bash
# Verify domain model consistency
poetry run python -c "
from contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe

# Test domain model can be instantiated
meal = Meal.create_meal('Test', 'author', 'meal_id', 'menu_id')
print('Domain model integrity: OK')
"
```

#### Phase 4: Integration Validation (5 minutes)

**4.1 Database Integration**
```bash
# Run integration tests  
poetry run python -m pytest tests/contexts/recipes_catalog/integration/ -v

# Test database migrations
poetry run python alembic upgrade head
poetry run python alembic downgrade -1
poetry run python alembic upgrade head
```

**4.2 API Integration**  
```bash
# Run end-to-end tests
poetry run python -m pytest tests/contexts/recipes_catalog/e2e/ -v

# Test Lambda handlers if applicable
```

#### Phase 5: Review Artifacts (5 minutes)

**5.1 Create Pull Request Description**
```markdown
## Feature: Recipe Rating System

### Summary
Adds ability for users to rate recipes within meals with scores (1-5) and optional comments.

### Changes Made
- ✅ Added Rating value object with validation
- ✅ Extended Recipe entity with rating capabilities  
- ✅ Added RateRecipe command and handler
- ✅ Implemented cached average_rating property
- ✅ Added comprehensive test coverage (>95%)
- ✅ Optimized database queries to avoid N+1
- ✅ Updated technical specifications

### Domain Rules Enforced
- Rating scores must be 1.0-5.0
- Rating author must match recipe author (meal author)
- Cache invalidation on rating changes
- Aggregate boundary preservation (mutations through Meal)

### Performance Impact
- Minimal memory usage (~100 bytes per rating)
- Cached average calculation (100x faster repeated access)
- Optimized database queries with JOINs
- No N+1 query issues

### Testing
- Unit tests: 98% coverage
- Integration tests: All scenarios covered
- Performance tests: All benchmarks passing
- Domain rule tests: All business rules validated

### Breaking Changes
None - purely additive functionality

### Migration Required
- Database: Add recipe_ratings table
- No application code migration needed

### Validation Completed
- [x] All tests passing
- [x] Type checking clean
- [x] Linting clean  
- [x] Security scan clean
- [x] Performance benchmarks passing
- [x] Documentation updated
```

**5.2 Self-Review Checklist**
```markdown
## Pre-Review Self-Checklist

### Code Quality
- [x] All tests passing (unit, integration, e2e)
- [x] Type checking clean (mypy)
- [x] Linting clean (ruff, black)
- [x] Security scan clean (bandit)
- [x] Test coverage >95% for new code
- [x] Performance tests passing

### Domain Design  
- [x] Business rules properly enforced
- [x] Aggregate boundaries respected
- [x] Domain events emitted if needed
- [x] Cache invalidation implemented
- [x] Error handling comprehensive
- [x] Value objects immutable

### Documentation
- [x] Docstrings for all public methods
- [x] Type hints complete
- [x] Technical specifications updated
- [x] API examples provided
- [x] Migration notes documented

### Performance
- [x] No performance regressions
- [x] Cached properties for expensive operations  
- [x] Database queries optimized
- [x] Memory usage reasonable
- [x] Benchmark tests created

### Integration
- [x] Database migrations tested
- [x] API endpoints working
- [x] Lambda handlers updated
- [x] Error scenarios tested
- [x] Authentication/authorization correct

### Backwards Compatibility
- [x] No breaking API changes
- [x] Database schema migrations safe
- [x] Existing functionality unaffected
- [x] Version compatibility maintained
```

### Common Code Review Issues to Avoid

**Domain Model Issues**:
```python
# ❌ Bad: Direct entity manipulation
recipe._ratings.append(rating)  # Bypasses business rules

# ✅ Good: Through aggregate methods  
meal.add_recipe_rating(recipe_id, rating)  # Enforces business rules
```

**Performance Issues**:
```python
# ❌ Bad: N+1 queries
for recipe in meal.recipes:
    ratings = rating_repository.get_by_recipe_id(recipe.id)  # N+1 problem

# ✅ Good: Batch loading
recipe_ratings = rating_repository.get_by_meal_id(meal.id)  # Single query
```

**Testing Issues**:
```python
# ❌ Bad: Testing implementation details
assert recipe._ratings[0].score == 4.5  # Testing private details

# ✅ Good: Testing behavior
assert recipe.average_rating == 4.5  # Testing public interface
```

**Error Handling Issues**:
```python
# ❌ Bad: Generic exceptions
raise Exception("Invalid rating")  # Not helpful

# ✅ Good: Domain-specific exceptions
raise BusinessRuleValidationException("Rating score must be between 1.0 and 5.0")
```

This completes the comprehensive AI Agent Workflow Guide with practical, actionable workflows for all common development scenarios in the domain-driven architecture.

---

## 📚 Related Documents

### Essential Foundations
- **[Quick Start Guide](./quick-start-guide.md)** - Get oriented with the codebase in 15 minutes
- **[Pattern Library](./pattern-library.md)** - Implementation patterns for the workflows described here
- **[Technical Specifications](./technical-specifications.md)** - API contracts and data models referenced in workflows

### Implementation Support
- **[Decision Trees](./decision-trees.md)** - Architectural decision frameworks used in workflows
- **[Domain Rules Reference](./domain-rules-reference.md)** - Business rules that constrain implementation choices
- **[Troubleshooting Guide](./troubleshooting-guide.md)** - Debug issues encountered during workflow execution

### Navigation
- **[Documentation Index](./README.md)** - Complete guide to all available documentation 