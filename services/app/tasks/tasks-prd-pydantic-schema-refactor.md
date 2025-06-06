# Tasks for Pydantic Schema Refactoring

## Relevant Files

### Base Schema
- `src/src/contexts/seedwork/shared/adapters/api_schemas/base.py` - Base schema classes and shared configuration

### Test Infrastructure
- `tests/seedwork/shared/adapters/api_schemas/test_base.py` - Base schema test cases
- `tests/seedwork/shared/adapters/api_schemas/conftest.py` - Schema-specific test fixtures
- `tests/seedwork/shared/adapters/api_schemas/utils.py` - Schema testing utilities

### Prerequisites and Review Requirements

Before starting any migration task, ensure you have reviewed:

1. **Base Implementation**
   - Review `base.py` to understand the base schema classes and their configuration
   - Understand the generic type parameters and their constraints
   - Familiarize yourself with the required conversion methods

2. **Domain Models and ORM Models**
   - Review the corresponding domain models (Entity, ValueObject, Command)
   - Review the SQLAlchemy ORM models that the schemas will interact with
   - Understand the relationships and constraints between models

3. **Existing Implementations**
   - Study completed migrations in contexts of tasks that were already completed
   - Analyze test patterns and coverage in existing test files

4. **Testing Patterns**
   - Review test infrastructure and utilities
   - Understand the testing guidelines and patterns
   - Study example test cases for similar schemas

### Testing Guidelines
- Test names should be descriptive and follow the pattern: `test_[method]_[scenario]_[expected_behavior]`
  - Example: `test_to_domain_with_none_values_convert_value_to_zero_and_unit_to_defaults` instead of `test_to_domain_with_none_values`
  - Example: `test_create_with_mixed_none_and_valid_values` instead of `test_create_with_mixed_values`
- Use `@pytest.mark.parametrize` for simple test cases to improve readability and maintainability
- Include comprehensive edge cases:
  - Boundary values
  - Null/None values
  - Empty collections
  - Invalid data types
  - Special characters
  - Maximum/minimum values
- Add detailed docstrings for complex test cases explaining:
  - Test purpose
  - Input data characteristics
  - Expected behavior
  - Any special considerations

### Shared Kernel Context
- `src/contexts/shared_kernel/adapters/api_schemas/value_objects/amount.py`
- `src/contexts/shared_kernel/adapters/api_schemas/value_objects/address.py`
- `src/contexts/shared_kernel/adapters/api_schemas/value_objects/tag/tag_filter.py`
- `src/contexts/shared_kernel/adapters/api_schemas/value_objects/contact_info.py`
- `src/contexts/shared_kernel/adapters/api_schemas/value_objects/profile.py`

### IAM Context
- `src/contexts/iam/core/adapters/api_schemas/value_objects/role.py`
- `src/contexts/iam/core/adapters/api_schemas/entities/user.py`
- `src/contexts/iam/core/adapters/api_schemas/commands/create_user.py`
- `src/contexts/iam/core/adapters/api_schemas/commands/remove_role_from_user.py`
- `src/contexts/iam/core/adapters/api_schemas/commands/assign_role_to_user.py`

### Recipes Catalog Context
- `src/contexts/recipes_catalog/core/adapters/api_schemas/value_objects/rating.py`
- `src/contexts/recipes_catalog/core/adapters/api_schemas/value_objects/ingredient.py`
- `src/contexts/recipes_catalog/core/adapters/api_schemas/entities/menu/menu.py`
- `src/contexts/recipes_catalog/core/adapters/api_schemas/entities/menu/filter.py`
- `src/contexts/recipes_catalog/core/adapters/api_schemas/entities/meal/meal.py`
- `src/contexts/recipes_catalog/core/adapters/api_schemas/entities/meal/filter.py`
- `src/contexts/recipes_catalog/core/adapters/api_schemas/entities/recipe/recipe.py`
- `src/contexts/recipes_catalog/core/adapters/api_schemas/entities/recipe/filter.py`
- `src/contexts/recipes_catalog/core/adapters/api_schemas/entities/client/client.py`
- `src/contexts/recipes_catalog/core/adapters/api_schemas/entities/client/filter.py`
- `src/contexts/recipes_catalog/core/adapters/api_schemas/commands/menu/*.py`
- `src/contexts/recipes_catalog/core/adapters/api_schemas/commands/meal/*.py`
- `src/contexts/recipes_catalog/core/adapters/api_schemas/commands/recipe/*.py`
- `src/contexts/recipes_catalog/core/adapters/api_schemas/commands/client/*.py`
- `src/contexts/recipes_catalog/core/adapters/api_schemas/commands/tag/*.py`

### Products Catalog Context
- `src/contexts/products_catalog/core/adapters/api_schemas/value_objects/score.py`
- `src/contexts/products_catalog/core/adapters/api_schemas/value_objects/if_food_votes.py`
- `src/contexts/products_catalog/core/adapters/api_schemas/entities/product.py`
- `src/contexts/products_catalog/core/adapters/api_schemas/entities/product_filter.py`
- `src/contexts/products_catalog/core/adapters/api_schemas/entities/classifications/base_class.py`
- `src/contexts/products_catalog/core/adapters/api_schemas/entities/classifications/filter.py`
- `src/contexts/products_catalog/core/adapters/api_schemas/commands/products/*.py`
- `src/contexts/products_catalog/core/adapters/api_schemas/commands/classification/*.py`

### CI Configuration
- `.github/workflows/schema-tests.yml` - CI pipeline for schema testing

### Notes

- All schema files should be placed under their respective context directories
- Test files should be placed alongside their corresponding schema files
- Use `pytest` for running tests
- Follow the example implementation pattern from the PRD
- Each schema should implement the required conversion methods (from_domain, to_domain, from_orm_model, to_orm_kwargs)
- All schemas must inherit from BaseApiModel with the specified configuration

## Tasks

- [ ] 1.0 Foundation Setup
  - [x] 1.1 Create base schema classes and configuration
  - [x] 1.2 Set up testing infrastructure
  - [ ] 1.3 Document schema patterns and guidelines (TODO: later)
  - [ ] 1.4 Create GitHub Actions workflow for schema testing (TODO: later)
  - [x] 1.5 SeedWork Context Migration
    - [x] 1.5.1 Migrate value objects
      - [x] Review domain models in `src/contexts/seedwork/shared/domain/value_objects/`
      - [x] Study base schema implementation patterns
      - [x] Migrate role schema
        - [x] Update to use BaseValueObject
        - [x] Implement proper type hints
        - [x] Add validation rules
      - [x] Migrate user schema
        - [x] Update to use BaseValueObject
        - [x] Implement proper type hints
        - [x] Add validation rules
        - [x] Ensure proper role relationship handling
    - [x] 1.5.2 Write tests for SeedWork schemas
      - [x] Create test suite for ApiSeedRole
      - [x] Create test suite for ApiSeedUser
      - [x] Test domain model conversion
      - [x] Test ORM model conversion
      - [x] Test serialization/deserialization
      - [x] Test validation rules
      - [x] Test immutability

- [x] 2.0 Shared Kernel Context Migration
  - [x] 2.1 Migrate value objects. (address, amount, contact_info, measure_unit, nutri_facts, nutri_value, profile, tag and tag_filter)
    - [x] address
    - [x] amount
    - [x] contact_info
    - [x] measure_unit (enum, no schema needed)
    - [x] nutri_facts
    - [x] nutri_value
    - [x] profile
    - [x] tag
    - [x] tag_filter
  - [x] 2.2 Write tests for all shared kernel schemas
    - [x] Implement descriptive test names following the pattern
    - [x] Add parametrized tests for simple cases
    - [x] Include edge cases and boundary testing
    - [x] Add docstrings for complex test scenarios

- [x] 3.0 IAM Context Migration
  - [x] 3.1 Migrate role value object (no user value object exists)
  - [x] 3.2 Migrate user entity schema
  - [x] 3.3 Migrate command schemas (create_user, role management)
    - [x] Review domain models in `src/contexts/iam/core/domain/`
    - [x] Review ORM models in `src/contexts/iam/infrastructure/persistence/models/`
    - [x] Study existing role and user schema implementations
    - [x] Migrate ApiCreateUser schema
    - [x] Migrate ApiAssignRoleToUser schema
    - [x] Migrate ApiRemoveRoleFromUser schema
  - [x] 3.4 Write tests for all IAM schemas
    - [x] Implement descriptive test names following the pattern
    - [x] Add parametrized tests for simple cases
    - [x] Include edge cases and boundary testing
    - [x] Add docstrings for complex test scenarios
    - [x] Test schema validation
    - [x] Test domain model conversion
    - [x] Test immutability

- [ ] 4.0 Recipes Catalog Context Migration
  - [x] 4.1 Migrate value objects in `src/contexts/recipes_catalog/core/adapters/api_schemas/value_objects/` (rating, ingredient, menu_meal, user)
    - [x] Review domain models in `src/contexts/recipes_catalog/core/domain/value_objects/`
    - [x] Review ORM models in `src/contexts/recipes_catalog/adapters/ORM/sa_models/`
    - [x] Study value object implementations for patterns on the contexts that are already migrated on previous tasks
  - [x] 4.2 Migrate entity schemas `src/contexts/recipes_catalog/core/adapters/api_schemas/entities/` (menu, meal, recipe, client)
    - [x] Review domain models in `src/contexts/recipes_catalog/core/domain/entities/`
    - [x] Review ORM models in `src/contexts/recipes_catalog/adapters/ORM/sa_models/`
    - [x] Study schema implementations for patterns on the contexts that are already migrated on previous tasks
  - [x] 4.3 Migrate filter schemas `src/contexts/recipes_catalog/core/adapters/api_schemas/entities/filter.py`
    - [x] Review ORM models in `src/contexts/recipes_catalog/adapters/ORM/sa_models/` and query patterns in repositories `src/contexts/recipes_catalog/core/adapters/repositories/`
  - [x] 4.4 Migrate command schemas in `src/contexts/recipes_catalog/core/adapters/api_schemas/commands/`
    - [x] Review command implementations on the contexts that are already migrated on previous tasks
    - [x] Study command patterns in domain models
  - [ ] 4.5 Write tests for all recipes catalog schemas
    - [ ] Implement descriptive test names following the pattern
    - [ ] Add parametrized tests for simple cases
    - [ ] Include edge cases and boundary testing
    - [ ] Add docstrings for complex test scenarios

- [ ] 5.0 Products Catalog Context Migration
  - [ ] 5.1 Migrate value objects (score, if_food_votes)
    - [ ] Review domain models in `src/contexts/products_catalog/core/domain/value_objects/`
    - [ ] Study shared kernel value object implementations for patterns
  - [ ] 5.2 Migrate entity schemas (product, classification)
    - [ ] Review domain models in `src/contexts/products_catalog/core/domain/entities/`
    - [ ] Review ORM models in `src/contexts/products_catalog/infrastructure/persistence/models/`
    - [ ] Study recipes catalog entity schema implementations for patterns
  - [ ] 5.3 Migrate filter schemas
    - [ ] Review existing filter implementations in shared kernel and recipes catalog
    - [ ] Study query patterns in domain models
  - [ ] 5.4 Migrate command schemas
    - [ ] Review command implementations in IAM and recipes catalog contexts
    - [ ] Study command patterns in domain models
  - [ ] 5.5 Write tests for all products catalog schemas
    - [ ] Implement descriptive test names following the pattern
    - [ ] Add parametrized tests for simple cases
    - [ ] Include edge cases and boundary testing
    - [ ] Add docstrings for complex test scenarios

- [ ] 6.0 Bulk Validation Implementation
  - [ ] 6.1 Implement TypeAdapter patterns for all collection fields
    - [ ] Review existing collection field implementations
    - [ ] Study performance implications
  - [ ] 6.2 Add performance testing
  - [ ] 6.3 Update documentation

- [ ] 7.0 Cleanup and Finalization
  - [ ] 7.1 Remove deprecated schemas
  - [ ] 7.2 Update documentation
  - [ ] 7.3 Final testing and validation
  - [ ] 7.4 Verify all schemas follow the new pattern 