# SaGenericRepository Test Suite

This directory contains comprehensive integration tests for the `SaGenericRepository` implementation, following "Architecture Patterns with Python" principles.

## Test Organization

The test suite is organized into logical groups for better maintainability and clarity:

```
repositories/
├── core/                           # Basic CRUD operations and core functionality
│   ├── test_seedwork_repository.py                # Core repository operations
│   └── test_seedwork_repository_behavior.py       # Behavior documentation
├── query_operations/               # Query building, filtering, and complex queries
│   ├── test_query_builder.py                      # Query building and SQL generation
│   ├── test_filter_operators.py                   # Filter operator implementations
│   └── test_filter_mappers.py                     # Filter-to-column mapping logic
├── advanced_features/              # Joins, edge cases, and specialized functionality
│   ├── test_seedwork_repository_joins.py          # Complex join scenarios
│   ├── test_seedwork_repository_edge_cases.py     # Edge cases and error conditions
│   └── test_repository_logger.py                  # Logging and monitoring
├── testing_infrastructure/         # Test models, factories, and shared utilities
│   ├── test_models.py                             # SQLAlchemy test models
│   ├── test_entities.py                           # Domain entity test classes
│   ├── test_mappers.py                            # Data mapper implementations
│   └── test_data_factories.py                     # Test data creation utilities
├── performance/                    # Benchmarking and performance validation
│   └── (future performance tests)
├── conftest.py                     # Shared fixtures and test configuration
├── __init__.py                     # Convenient imports and test utilities
└── README.md                       # This documentation
```

## Key Features

### Real Database Testing
- Uses actual PostgreSQL test database (not mocks)
- Tests behavior, not implementation
- Validates real database constraints and relationships
- Catches actual SQL errors and performance issues

### Test Infrastructure
- **Models**: Complete SQLAlchemy models with relationships, constraints, and indices
- **Entities**: Domain entities matching the production architecture
- **Mappers**: Data mappers for entity ↔ model conversion
- **Factories**: Comprehensive test data generation utilities
- **Fixtures**: Shared test fixtures with proper cleanup

### Comprehensive Coverage
- **CRUD Operations**: Add, get, update, delete with real database
- **Filtering**: All filter operators with actual SQL generation
- **Joins**: Complex multi-table joins and relationship handling
- **Edge Cases**: Null handling, constraint violations, circular references
- **Performance**: Benchmarking with real data and queries

## Usage

### Basic Import Pattern
```python
from tests.contexts.seedwork.adapters.repositories import (
    TestMealEntity, TestRecipeEntity, create_test_meal, TEST_MEAL_FILTER_MAPPERS
)
```

### Repository Fixtures
All repository fixtures are available in test functions:
```python
async def test_meal_operations(meal_repository, test_session):
    meal = create_test_meal(name="Test Meal")
    await meal_repository.add(meal)
    await test_session.commit()
    
    retrieved = await meal_repository.get(meal.id)
    assert retrieved.name == "Test Meal"
```

### Test Data Creation
```python
# Simple entity creation
meal = create_test_meal(name="Italian Pasta", total_time=45)

# Complex entity with relationships
meal, recipes = create_test_meal_with_recipes(recipe_count=3)

# Large datasets for performance testing
meals = create_large_dataset(entity_count=1000)
```

## Test Principles

### Architecture Patterns Compliance
- **Test Behavior**: Focus on what the repository does, not how
- **Real Database**: Use actual database connections, not mocks
- **Known States**: Use fixtures to create known database states
- **Real Errors**: Catch and validate actual database errors

### Integration Testing Best Practices
- **Independent Tests**: Each test can run in isolation
- **Proper Cleanup**: Automatic schema and data cleanup
- **Performance Awareness**: Timeout protection and benchmarking
- **Real Constraints**: Test actual foreign key and check constraints

## Running Tests

### All Repository Tests
```bash
pytest tests/contexts/seedwork/shared/adapters/repositories/
```

### Specific Test Groups
```bash
# Core functionality
pytest tests/contexts/seedwork/shared/adapters/repositories/core/

# Query operations
pytest tests/contexts/seedwork/shared/adapters/repositories/query_operations/

# Advanced features
pytest tests/contexts/seedwork/shared/adapters/repositories/advanced_features/
```

### With Coverage
```bash
pytest tests/contexts/seedwork/shared/adapters/repositories/ --cov=src.contexts.seedwork.adapters.repositories
```

## Test Database

### Schema Management
- Tests use isolated `test_seedwork` schema
- Automatic schema creation and cleanup
- Independent of main database schemas

### Transaction Management
- Each test runs in its own transaction
- Automatic rollback on test completion
- Real foreign key constraint validation

### Performance
- Connection pooling for efficiency
- Timeout protection (30-60 seconds per test)
- Benchmark assertions for performance regression detection

## Contributing

### Adding New Tests
1. Place tests in appropriate subdirectory based on functionality
2. Use real database fixtures from `conftest.py`
3. Import test utilities from `testing_infrastructure/`
4. Follow the established naming and documentation patterns

### Test Structure
```python
async def test_descriptive_name(repository_fixture, test_session):
    """Test description explaining the behavior being tested"""
    # Given: Setup test data
    entity = create_test_entity(...)
    
    # When: Perform the operation
    result = await repository_fixture.operation(...)
    
    # Then: Assert expected behavior
    assert result.property == expected_value
```

### Performance Tests
- Use `@timeout_test(seconds)` decorator for time-sensitive tests
- Use `benchmark_timer` fixture for performance assertions
- Create realistic test datasets for meaningful benchmarks

## Architecture

This test suite validates the repository layer of the hexagonal architecture:

```
Domain Layer (Entities) ← → Repository Interface ← → Database Adapter (SQLAlchemy)
       ↑                           ↑                         ↑
   Test Entities              Test Repository           Test Database
```

The tests ensure that:
- Domain entities are properly persisted and retrieved
- Repository interface contracts are maintained
- Database adapter handles all SQL operations correctly
- Real database constraints and relationships work as expected 