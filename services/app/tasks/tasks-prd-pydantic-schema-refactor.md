# Tasks for Pydantic Schema Refactoring

## Relevant Files

### Base Schema
- `src/contexts/seedwork/shared/adapters/api_schemas/base.py` - Base schema classes and shared configuration

### Test Infrastructure
- `tests/seedwork/shared/adapters/api_schemas/test_base.py` - Base schema test cases
- `tests/seedwork/shared/adapters/api_schemas/conftest.py` - Schema-specific test fixtures
- `tests/seedwork/shared/adapters/api_schemas/utils.py` - Schema testing utilities

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
- `contexts/shared_kernel/adapters/api_schemas/value_objects/amount.py`
- `contexts/shared_kernel/adapters/api_schemas/value_objects/address.py`
- `contexts/shared_kernel/adapters/api_schemas/value_objects/tag/tag_filter.py`
- `contexts/shared_kernel/adapters/api_schemas/value_objects/contact_info.py`
- `contexts/shared_kernel/adapters/api_schemas/value_objects/profile.py`

### IAM Context
- `contexts/iam/core/adapters/api_schemas/value_objects/role.py`
- `contexts/iam/core/adapters/api_schemas/entities/user.py`
- `contexts/iam/core/adapters/api_schemas/commands/create_user.py`
- `contexts/iam/core/adapters/api_schemas/commands/remove_role_from_user.py`
- `contexts/iam/core/adapters/api_schemas/commands/assign_role_to_user.py`

### Recipes Catalog Context
- `contexts/recipes_catalog/core/adapters/api_schemas/value_objects/rating.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/value_objects/ingredient.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/menu/menu.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/menu/filter.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/meal/meal.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/meal/filter.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/recipe/recipe.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/recipe/filter.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/client/client.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/client/filter.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/commands/menu/*.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/commands/meal/*.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/commands/recipe/*.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/commands/client/*.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/commands/tag/*.py`

### Products Catalog Context
- `contexts/products_catalog/core/adapters/api_schemas/value_objects/score.py`
- `contexts/products_catalog/core/adapters/api_schemas/value_objects/if_food_votes.py`
- `contexts/products_catalog/core/adapters/api_schemas/entities/product.py`
- `contexts/products_catalog/core/adapters/api_schemas/entities/product_filter.py`
- `contexts/products_catalog/core/adapters/api_schemas/entities/classifications/base_class.py`
- `contexts/products_catalog/core/adapters/api_schemas/entities/classifications/filter.py`
- `contexts/products_catalog/core/adapters/api_schemas/commands/products/*.py`
- `contexts/products_catalog/core/adapters/api_schemas/commands/classification/*.py`

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

- [ ] 3.0 IAM Context Migration
  - [x] 3.1 Migrate role value object (no user value object exists)
  - [x] 3.2 Migrate user entity schema
  - [ ] 3.3 Migrate command schemas (create_user, role management)
  - [ ] 3.4 Write tests for all IAM schemas
    - [ ] Implement descriptive test names following the pattern
    - [ ] Add parametrized tests for simple cases
    - [ ] Include edge cases and boundary testing
    - [ ] Add docstrings for complex test scenarios

- [ ] 4.0 Recipes Catalog Context Migration
  - [ ] 4.1 Migrate value objects (rating, ingredient)
  - [ ] 4.2 Migrate entity schemas (menu, meal, recipe, client)
  - [ ] 4.3 Migrate filter schemas
  - [ ] 4.4 Migrate command schemas
  - [ ] 4.5 Write tests for all recipes catalog schemas
    - [ ] Implement descriptive test names following the pattern
    - [ ] Add parametrized tests for simple cases
    - [ ] Include edge cases and boundary testing
    - [ ] Add docstrings for complex test scenarios

- [ ] 5.0 Products Catalog Context Migration
  - [ ] 5.1 Migrate value objects (score, if_food_votes)
  - [ ] 5.2 Migrate entity schemas (product, classification)
  - [ ] 5.3 Migrate filter schemas
  - [ ] 5.4 Migrate command schemas
  - [ ] 5.5 Write tests for all products catalog schemas
    - [ ] Implement descriptive test names following the pattern
    - [ ] Add parametrized tests for simple cases
    - [ ] Include edge cases and boundary testing
    - [ ] Add docstrings for complex test scenarios

- [ ] 6.0 Bulk Validation Implementation
  - [ ] 6.1 Implement TypeAdapter patterns for all collection fields
  - [ ] 6.2 Add performance testing
  - [ ] 6.3 Update documentation

- [ ] 7.0 Cleanup and Finalization
  - [ ] 7.1 Remove deprecated schemas
  - [ ] 7.2 Update documentation
  - [ ] 7.3 Final testing and validation
  - [ ] 7.4 Verify all schemas follow the new pattern 