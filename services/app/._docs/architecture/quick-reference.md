[← Index](./README.md) | [Quick Start](./quick-start-guide.md) | [Workflows](./ai-agent-workflows.md) | [Patterns](./pattern-library.md) | [Troubleshooting](./troubleshooting-guide.md)

---

# 🚀 Quick Reference Card - Menu Planning Backend

*2-page essential reference for developers and AI agents*

## ⚡ Essential Commands

### Development Workflow
```bash
# Setup & Dependencies
poetry install                              # Install dependencies
poetry run python manage.py check-db        # Verify database connection

# Testing (ALWAYS use poetry run python -m)
poetry run python -m pytest                           # Run all tests
poetry run python -m pytest tests/unit -v             # Unit tests only
poetry run python -m pytest --cov=src --cov-report=term-missing  # With coverage
poetry run python -m pytest -k "cache" -v             # Specific tests

# Code Quality
poetry run python -m mypy src/                        # Type checking
poetry run python -m ruff check .                     # Linting
poetry run python -m black . --check                  # Format checking
poetry run python -m bandit -r src/                   # Security scan

# Database
poetry run python alembic upgrade head                # Run migrations
poetry run python alembic history                     # View migration history
poetry run python cleanup_test_schema.py              # Reset test DB

# Development
poetry run python manage.py shell                     # Interactive shell
./scripts/validate-docs.sh                           # Validate documentation
```

### 🚨 Critical: Always Use `poetry run python -m`
- ✅ **Correct**: `poetry run python -m pytest`
- ❌ **Wrong**: `pytest` or `poetry run python pytest`

## 📁 Key File Locations

### Core Domain Objects
```
src/contexts/recipes_catalog/core/domain/meal/
├── root_aggregate/meal.py           # Primary aggregate
├── entities/recipe.py               # Recipe entity
└── value_objects/nutri_facts.py     # Nutrition values

src/contexts/seedwork/shared/domain/
├── entity.py                       # Base entity with caching
├── aggregate_root.py               # Base aggregate
└── value_object.py                 # Base value object
```

### Application Services
```
src/contexts/recipes_catalog/core/services/
├── command_handlers.py             # Command processing
├── query_handlers.py               # Query processing
└── meal_service.py                 # Application service

src/contexts/recipes_catalog/core/domain/meal/commands/
├── create_meal.py                  # Command definitions
├── update_meal.py
└── add_recipe_to_meal.py
```

### Data Access
```
src/contexts/recipes_catalog/core/adapters/repositories/
├── meal_repository.py              # Repository implementation
└── unit_of_work.py                 # Transaction management

tests/contexts/recipes_catalog/
├── unit/                           # Pure domain tests
├── integration/                    # Repository tests
└── e2e/                           # Full workflow tests
```

### Documentation
```
docs/architecture/
├── README.md                       # Documentation index
├── quick-start-guide.md            # 15-minute onboarding
├── technical-specifications.md     # API contracts
├── pattern-library.md              # Implementation patterns
├── ai-agent-workflows.md          # Development workflows
└── troubleshooting-guide.md       # Debug guide
```

## 🔧 Common Patterns

### Create New Entity Property
```python
# 1. Add to entity with validation
@property
def difficulty_level(self) -> DifficultyLevel:
    return self._difficulty_level

def set_difficulty_level(self, level: DifficultyLevel) -> None:
    if level not in DifficultyLevel:
        raise ValueError(f"Invalid difficulty: {level}")
    object.__setattr__(self, '_difficulty_level', level)
    self._increment_version()

# 2. Add to tests
def test_set_difficulty_level_valid():
    # Test valid input
    
def test_set_difficulty_level_invalid():
    # Test validation
```

### Add Cached Property  
```python
from contexts.seedwork.shared.domain.entity import cached_property

@cached_property  
def total_calories(self) -> int:
    """Calculate total calories from all recipes."""
    return sum(recipe.calories for recipe in self.recipes)

# Test caching behavior
def test_total_calories_cached():
    # First access populates cache
    # Subsequent access uses cache
    # Modification invalidates cache
```

### Create New Command
```python
# 1. Define command
@dataclass(frozen=True)
class RateRecipe:
    meal_id: str
    recipe_id: str  
    rating: float
    user_id: str

# 2. Add handler
def handle_rate_recipe(command: RateRecipe, uow: UnitOfWork) -> None:
    with uow:
        meal = uow.meals.get(command.meal_id)
        meal.rate_recipe(command.recipe_id, command.rating, command.user_id)
        uow.commit()

# 3. Add tests
def test_rate_recipe_success():
    # Test successful rating
    
def test_rate_recipe_invalid_rating():
    # Test validation
```

### Repository Method
```python
# In repository interface
def get_meals_by_author(self, author_id: str) -> List[Meal]:
    """Get all meals by specific author."""
    pass

# In implementation  
def get_meals_by_author(self, author_id: str) -> List[Meal]:
    query = self.session.query(MealTable).filter(
        MealTable.author_id == author_id
    )
    return [self._to_domain(row) for row in query.all()]
```

## 🚨 Emergency Procedures

### Tests Failing
```bash
# 1. Check Python path
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

# 2. Reset test database
poetry run python cleanup_test_schema.py

# 3. Run specific failing test
poetry run python -m pytest path/to/test.py::test_name -v -s

# 4. Check for import issues
poetry run python manage.py shell
```

### Import/Module Errors
```bash
# 1. Verify you're in correct directory
pwd  # Should show: .../menu-planning/backend/services/app

# 2. Check virtual environment
poetry env info

# 3. Reinstall dependencies
poetry install

# 4. Use manage.py shell (sets Python path)
poetry run python manage.py shell
```

### Performance Issues
```bash
# 1. Check if using correct commands
# ✅ poetry run python -m pytest
# ❌ pytest

# 2. Profile slow tests
poetry run python -m pytest --benchmark-only

# 3. Check caching behavior
poetry run python -m pytest tests/ -k "cache" -v
```

### Database Issues
```bash
# 1. Test connection
poetry run python manage.py check-db

# 2. Check migration status
poetry run python alembic current

# 3. Reset if needed
poetry run python cleanup_test_schema.py
poetry run python alembic upgrade head
```

## 🎯 Quick Navigation Commands

### Find Code Patterns
```bash
# Find entity implementations
find src -name "*.py" | grep entity

# Find all command definitions  
find src -name "*command*.py" -type f

# Find test examples
find tests -name "*test_meal*" -type f

# Search for patterns in code
grep -r "cached_property" src/contexts/seedwork/
grep -r "@dataclass" src/contexts/*/core/domain/commands/
```

### Explore Domain Model
```python
# In shell: poetry run python manage.py shell
from contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal

# Create test instance
meal = Meal.create_meal("Test", "author", "meal_id", "menu_id")

# Explore properties
print([prop for prop in dir(meal) if not prop.startswith('_')])
print(f"Has caching: {hasattr(meal, '_cached_attrs')}")
```

### Documentation Search
```bash
# Find specific topics
grep -r "caching" docs/architecture/
grep -r "aggregate" docs/architecture/  
grep -n "Command" docs/architecture/technical-specifications.md

# View file structure
tree docs/architecture/ -I "__pycache__|*.pyc"
```

## 📊 Performance Benchmarks

### Acceptable Performance
- **Unit tests**: <30 seconds total
- **Entity creation**: <1ms per entity
- **Cached property access**: <0.1ms after first access
- **Repository queries**: <100ms for simple queries
- **Command processing**: <10ms per command

### Warning Signs
- Tests taking >60 seconds
- Memory usage growing during test runs  
- Cache hit rate <80% for cached properties
- Database queries >500ms

## 🔍 Common Debugging Commands

```bash
# Check what's cached
print(entity._cached_attrs if hasattr(entity, '_cached_attrs') else 'No cache')

# Verify domain events
print(f"Events: {aggregate.domain_events}")

# Check aggregate state
print(f"Version: {entity.version}, Created: {entity.created_at}")

# Test business rules
try:
    entity.some_operation()
except BusinessRuleValidationException as e:
    print(f"Rule violation: {e}")
```

## 📚 Most Useful Documentation

**Daily Reference**: 
- [Quick Start Guide](./quick-start-guide.md) - Commands & navigation
- [Pattern Library](./pattern-library.md) - Implementation examples

**Weekly Reference**:
- [AI Agent Workflows](./ai-agent-workflows.md) - Development processes  
- [Technical Specifications](./technical-specifications.md) - API contracts

**Troubleshooting**:
- [Troubleshooting Guide](./troubleshooting-guide.md) - Issue resolution

---

*💡 **Tip**: Bookmark this page for instant access to essential information. Most development tasks can be completed using just these patterns and commands.* 